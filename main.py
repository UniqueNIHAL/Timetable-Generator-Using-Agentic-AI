"""Main FastAPI application for timetable planner."""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd

from config import settings
from models import (
    Faculty, Subject, Classroom, Section, Constraint,
    TimetableRequest, Timetable, ScheduleEntry
)
from agents import TimetableAgent, ConstraintAgent
from services.gemini_service import gemini_service
from services.firebase_auth import initialize_firebase, auth_required, get_current_user

# Initialize Firebase Admin SDK
try:
    initialize_firebase()
except Exception as e:
    print(f"Warning: Firebase initialization failed: {e}")
    print("Authentication will not work properly")

# Initialize FastAPI app
app = FastAPI(
    title="Agentic Timetable Planner",
    description="AI-powered university timetable planner using Google Gemini",
    version="0.1.0"
)

# Simple rate limiter (in-memory, per-session)
# In production, use Redis or similar
rate_limit_store = {}

def check_rate_limit(identifier: str, max_requests: int = 20, window_seconds: int = 60) -> bool:
    """
    Check if request is within rate limit.
    
    Args:
        identifier: Unique identifier (e.g., IP, session)
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
        
    Returns:
        True if within limit, False if exceeded
    """
    now = datetime.now()
    
    if identifier not in rate_limit_store:
        rate_limit_store[identifier] = []
    
    # Remove old requests outside the window
    rate_limit_store[identifier] = [
        req_time for req_time in rate_limit_store[identifier]
        if now - req_time < timedelta(seconds=window_seconds)
    ]
    
    # Check if limit exceeded
    if len(rate_limit_store[identifier]) >= max_requests:
        return False
    
    # Add current request
    rate_limit_store[identifier].append(now)
    return True

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory storage (replace with database in production)
data_store = {
    "faculty": [],
    "subjects": [],
    "classrooms": [],
    "sections": [],
    "constraints": [],
    "timetables": []
}

# Initialize agents
timetable_agent = TimetableAgent()
constraint_agent = ConstraintAgent()


# Pydantic models for API
class ChatMessage(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = None
    last_timetable: Optional[Dict[str, Any]] = None  # Store last generated timetable for refinement


class ChatResponse(BaseModel):
    response: str
    intent: Optional[Dict[str, Any]] = None


class GenerateTimetableRequest(BaseModel):
    academic_year: str
    semester: int
    section_ids: Optional[List[str]] = None  # If None, use all sections


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main UI."""
    try:
        with open("static/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Agentic Timetable Planner</h1><p>UI coming soon. Check /docs for API.</p>"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


async def generate_timetable_from_chat(user_request: str, previous_timetable: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Helper function to generate timetable from natural language."""
    
    # Check if this is a modification request
    is_modification = previous_timetable is not None and any(word in user_request.lower() for word in ['change', 'modify', 'update', 'adjust', 'let', 'make', 'set', 'from'])
    
    # First, extract key parameters using Gemini
    extraction_prompt = f"""
    Extract ONLY these parameters from this timetable request: "{user_request}"
    
    {f"Previous timetable context: {json.dumps(previous_timetable, indent=2)}" if previous_timetable else ""}
    
    If the user is asking to MODIFY an existing timetable (keywords: change, let, adjust, from), 
    use the previous timetable values as defaults and only update what they're asking to change.
    
    Respond ONLY in this exact JSON format:
    {{
      "university": "university name or 'Unknown'",
      "semester": "semester number",
      "subjects": ["Subject1", "Subject2", "Subject3"],
      "classes_per_subject_per_week": 3,
      "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "start_time": "07:50",
      "end_time": "11:40",
      "class_duration_minutes": 50
    }}
    """
    
    try:
        extraction_response = await gemini_service.generate_text(extraction_prompt, temperature=0.1, max_tokens=500)
        
        # Parse extraction
        if "```json" in extraction_response:
            json_str = extraction_response.split("```json")[1].split("```")[0].strip()
        elif "```" in extraction_response:
            json_str = extraction_response.split("```")[1].split("```")[0].strip()
        else:
            json_str = extraction_response.strip()
        
        params = json.loads(json_str)
        
        # Now generate schedule with explicit constraints
        subjects = params.get("subjects", [])
        classes_per_subject = params.get("classes_per_subject_per_week", 3)
        days = params.get("days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        start_time_raw = params.get("start_time", "07:50")
        class_duration_raw = params.get("class_duration_minutes", 50)
        
        # Validate and fix start_time format
        if start_time_raw == "Unknown" or not start_time_raw or ":" not in str(start_time_raw):
            start_time = "07:50"
        else:
            start_time = start_time_raw
        
        # Validate and convert class_duration to int
        try:
            class_duration = int(class_duration_raw)
        except (ValueError, TypeError):
            class_duration = 50  # Default to 50 minutes
        
        # Validate and convert classes_per_subject to int
        try:
            classes_per_subject = int(classes_per_subject)
        except (ValueError, TypeError):
            classes_per_subject = 3
        
        # Create schedule programmatically to ensure correct count
        schedule = []
        time_slots_per_day = 4  # Maximum slots per day
        
        # Calculate time slots
        from datetime import datetime, timedelta
        try:
            current_time = datetime.strptime(start_time, "%H:%M")
        except ValueError:
            # Fallback if time parsing fails
            current_time = datetime.strptime("07:50", "%H:%M")
        
        time_slots = []
        for _ in range(time_slots_per_day):
            end_time = current_time + timedelta(minutes=class_duration)
            time_slots.append({
                "start": current_time.strftime("%H:%M"),
                "end": end_time.strftime("%H:%M")
            })
            current_time = end_time
        
        # NEW DISTRIBUTION STRATEGY: Spread across all days
        # Instead of round-robin by class, distribute by day first
        total_classes = len(subjects) * classes_per_subject
        classes_per_day = (total_classes + len(days) - 1) // len(days)  # Ceiling division
        
        classes_scheduled = {subject: 0 for subject in subjects}
        current_slot = 0
        
        for day_index, day in enumerate(days):
            classes_for_today = 0
            subject_index = day_index % len(subjects)  # Start with different subject each day
            
            # Schedule classes for this day (max classes_per_day or until all scheduled)
            while classes_for_today < classes_per_day and sum(classes_scheduled.values()) < total_classes:
                # Find next subject that needs more classes
                attempts = 0
                while classes_scheduled[subjects[subject_index]] >= classes_per_subject and attempts < len(subjects):
                    subject_index = (subject_index + 1) % len(subjects)
                    attempts += 1
                
                # Check if we found a subject that needs scheduling
                if classes_scheduled[subjects[subject_index]] < classes_per_subject:
                    slot = time_slots[classes_for_today % len(time_slots)]
                    schedule.append({
                        "day": day,
                        "start_time": slot["start"],
                        "end_time": slot["end"],
                        "subject": subjects[subject_index],
                        "class_type": "Lecture"
                    })
                    classes_scheduled[subjects[subject_index]] += 1
                    classes_for_today += 1
                    subject_index = (subject_index + 1) % len(subjects)
                else:
                    break  # All subjects fully scheduled
        
        return {
            "university": params.get("university", "Unknown"),
            "semester": params.get("semester", "3"),
            "schedule": schedule
        }
        
    except Exception as e:
        print(f"Error in chat timetable generation: {e}")
        # Fallback to original method
        return await generate_timetable_from_chat_fallback(user_request)


async def generate_timetable_from_chat_fallback(user_request: str) -> Dict[str, Any]:
    """Fallback method using original AI generation."""
    # Use Gemini to parse the request and create a basic schedule
    prompt = f"""
    Based on this timetable request: "{user_request}"
    
    Generate a weekly timetable in JSON format. 
    
    IMPORTANT RULES:
    1. Extract the EXACT number of classes per subject per week from the request
    2. If the user says "3 classes per week per subject", schedule EXACTLY 3 classes for each subject, NOT MORE
    3. Distribute classes evenly across different days (avoid scheduling the same subject on consecutive days if possible)
    4. Respect the time range and duration specified
    5. Avoid time conflicts - no overlapping classes
    
    Extract from request:
    - Subjects mentioned
    - Number of classes per subject per week (EXACT number)
    - Days (default Monday-Friday)
    - Time range
    - Duration per class
    
    Create a schedule array with format:
    {{
      "university": "extracted or 'Unknown'",
      "semester": "extracted or '3'",
      "schedule": [
        {{
          "day": "Monday",
          "start_time": "08:00",
          "end_time": "08:50",
          "subject": "Subject Name",
          "class_type": "Lecture"
        }}
      ]
    }}
    
    CRITICAL: Count the classes per subject carefully. If user wants 3 classes/week, schedule ONLY 3 occurrences of that subject, not 5.
    Example: For 3 subjects with 3 classes each = 9 total classes, distributed across Monday-Friday.
    """
    
    response = await gemini_service.generate_text(prompt, temperature=0.5, max_tokens=4096)
    
    try:
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        else:
            json_str = response.strip()
        
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Error parsing schedule: {e}")
        return {"error": "Could not parse timetable", "raw_response": response}


@app.post("/api/chat")
@auth_required
async def chat(request: Request, message: ChatMessage) -> ChatResponse:
    """
    Chat interface for natural language interaction.
    Requires authentication.
    """
    try:
        # Get authenticated user
        user = request.state.user
        
        # Apply rate limiting (20 requests per minute per user)
        session_id = f"chat_{user['uid']}"
        
        if not check_rate_limit(session_id, max_requests=20, window_seconds=60):
            return ChatResponse(
                response="⏱️ You're sending messages too quickly. Please wait a moment before trying again.\n\n"
                        "This helps ensure the service remains available for everyone.",
                intent={"intent": "rate_limited"}
            )
        
        # Apply context guardrails
        validation = await gemini_service.validate_chat_context(message.message)
        
        if not validation.get("is_valid", True):
            return ChatResponse(
                response=f"⚠️ {validation.get('reason', 'Please ask questions related to timetable scheduling.')}\n\n"
                        f"I'm here to help with:\n"
                        f"• Creating and managing timetables\n"
                        f"• Scheduling classes and faculty\n"
                        f"• Managing rooms and sections\n"
                        f"• Answering scheduling-related questions",
                intent={"intent": "out_of_context", "validation": validation}
            )
        
        # Check if it's a greeting
        message_lower = message.message.lower().strip()
        greeting_patterns = ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
        
        if any(greeting in message_lower for greeting in greeting_patterns) and len(message.message.split()) <= 3:
            return ChatResponse(
                response="👋 Hello! I'm your **AI Timetable Planning Assistant**.\n\n"
                        "I can help you:\n"
                        "• 📅 **Generate timetables** from natural language (e.g., 'Create a timetable with 3 classes per week')\n"
                        "• 📤 **Upload data** - Upload CSV/JSON files with faculty, subjects, classrooms, and sections\n"
                        "• ⚙️ **Manage constraints** - Ensure no conflicts with faculty, classrooms, or capacity\n"
                        "• 📊 **View schedules** - See day-wise timetables with validation\n"
                        "• 📥 **Export results** - Download as CSV or JSON\n\n"
                        "**Try asking:**\n"
                        "• 'Generate a timetable for semester 3 with 5 subjects'\n"
                        "• 'Create a schedule with classes spread across 5 days'\n"
                        "• 'What data do I need to upload?'\n\n"
                        "How can I assist you today?",
                intent={"intent": "greeting"}
            )
        
        # Parse user intent
        parsed = await gemini_service.parse_natural_language_request(
            message.message,
            context={"data_store": {k: len(v) for k, v in data_store.items()}}
        )
        
        # Handle different intents
        intent = parsed.get("intent", "")
        response_msg = parsed.get("response_message", "")
        
        if intent == "query_status":
            response_msg += f"\n\nCurrent data: {len(data_store['faculty'])} faculty, "
            response_msg += f"{len(data_store['subjects'])} subjects, "
            response_msg += f"{len(data_store['classrooms'])} classrooms, "
            response_msg += f"{len(data_store['sections'])} sections"
        
        # Check if user wants to generate a timetable
        if intent == "generate_timetable" or "generate" in message.message.lower() or "timetable" in message.message.lower():
            # Generate timetable from natural language (pass previous timetable for refinement)
            try:
                timetable_data = await generate_timetable_from_chat(
                    message.message,
                    previous_timetable=message.last_timetable
                )
                
                if timetable_data and "error" not in timetable_data:
                    response_msg = "✅ I've generated a timetable based on your requirements!\n\n"
                    response_msg += f"**{timetable_data.get('university', 'University')} - Semester {timetable_data.get('semester', '3')}**\n\n"
                    
                    # Format the schedule
                    schedule = timetable_data.get('schedule', [])
                    if schedule:
                        response_msg += "**Schedule:**\n"
                        current_day = None
                        for entry in schedule:
                            if entry['day'] != current_day:
                                current_day = entry['day']
                                response_msg += f"\n**{current_day}:**\n"
                            response_msg += f"• {entry['start_time']}-{entry['end_time']}: {entry['subject']}\n"
                    
                    # Store in intent for frontend to display
                    parsed["timetable_data"] = timetable_data
                else:
                    response_msg = "I had trouble generating the timetable. Please try again or provide more details like:\n"
                    response_msg += "• Number of days (e.g., '5 days')\n"
                    response_msg += "• Subjects to include\n"
                    response_msg += "• Classes per week per subject\n"
            except Exception as gen_error:
                print(f"Timetable generation error: {gen_error}")
                response_msg = "I encountered an error while generating the timetable. Please try rephrasing your request."
        
        # Ensure we always have a response
        if not response_msg or response_msg.strip() == "":
            response_msg = parsed.get("response_message", "I'm here to help with timetable scheduling. What would you like to do?")
        
        return ChatResponse(
            response=response_msg,
            intent=parsed
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload/faculty")
@auth_required
async def upload_faculty(request: Request, file: UploadFile = File(...)):
    """
    Upload faculty data from CSV/JSON file.
    Expected columns: id, name, email, department, subjects_can_teach (comma-separated)
    Requires authentication.
    """
    try:
        user = request.state.user
        content = await file.read()
        
        if file.filename.endswith('.csv'):
            import io
            df = pd.read_csv(io.BytesIO(content))
            faculty_list = []
            
            for _, row in df.iterrows():
                faculty = Faculty(
                    id=str(row['id']),
                    name=row['name'],
                    email=row.get('email', ''),
                    department=row['department'],
                    subjects_can_teach=row['subjects_can_teach'].split(',') if pd.notna(row.get('subjects_can_teach')) else [],
                    max_hours_per_week=int(row.get('max_hours_per_week', 20))
                )
                faculty_list.append(faculty)
        
        elif file.filename.endswith('.json'):
            data = json.loads(content)
            faculty_list = [Faculty(**item) for item in data]
        else:
            raise HTTPException(status_code=400, detail="File must be CSV or JSON")
        
        # Store in data store
        data_store["faculty"] = faculty_list
        
        return {
            "success": True,
            "message": f"Uploaded {len(faculty_list)} faculty members",
            "count": len(faculty_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload/subjects")
@auth_required
async def upload_subjects(request: Request, file: UploadFile = File(...)):
    """
    Upload subjects data from CSV/JSON file.
    Expected columns: id, name, code, department, credits, hours_per_week
    Requires authentication.
    """
    try:
        user = request.state.user
        content = await file.read()
        
        if file.filename.endswith('.csv'):
            import io
            df = pd.read_csv(io.BytesIO(content))
            subjects_list = []
            
            for _, row in df.iterrows():
                subject = Subject(
                    id=str(row['id']),
                    name=row['name'],
                    code=row['code'],
                    department=row['department'],
                    credits=int(row['credits']),
                    hours_per_week=int(row['hours_per_week']),
                    lecture_type=row.get('lecture_type', 'theory'),
                    requires_lab=bool(row.get('requires_lab', False)),
                    is_elective=bool(row.get('is_elective', False))
                )
                subjects_list.append(subject)
        
        elif file.filename.endswith('.json'):
            data = json.loads(content)
            subjects_list = [Subject(**item) for item in data]
        else:
            raise HTTPException(status_code=400, detail="File must be CSV or JSON")
        
        data_store["subjects"] = subjects_list
        
        return {
            "success": True,
            "message": f"Uploaded {len(subjects_list)} subjects",
            "count": len(subjects_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload/classrooms")
@auth_required
async def upload_classrooms(request: Request, file: UploadFile = File(...)):
    """
    Upload classrooms data from CSV/JSON file.
    Expected columns: id, name, building, capacity, room_type
    Requires authentication.
    """
    try:
        user = request.state.user
        content = await file.read()
        
        if file.filename.endswith('.csv'):
            import io
            df = pd.read_csv(io.BytesIO(content))
            classrooms_list = []
            
            for _, row in df.iterrows():
                classroom = Classroom(
                    id=str(row['id']),
                    name=row['name'],
                    building=row['building'],
                    capacity=int(row['capacity']),
                    room_type=row.get('room_type', 'lecture_hall'),
                    facilities=row.get('facilities', '').split(',') if pd.notna(row.get('facilities')) else []
                )
                classrooms_list.append(classroom)
        
        elif file.filename.endswith('.json'):
            data = json.loads(content)
            classrooms_list = [Classroom(**item) for item in data]
        else:
            raise HTTPException(status_code=400, detail="File must be CSV or JSON")
        
        data_store["classrooms"] = classrooms_list
        
        return {
            "success": True,
            "message": f"Uploaded {len(classrooms_list)} classrooms",
            "count": len(classrooms_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload/sections")
@auth_required
async def upload_sections(request: Request, file: UploadFile = File(...)):
    """
    Upload sections data from CSV/JSON file.
    Expected columns: id, name, program, year, semester, num_students, subjects (comma-separated)
    Requires authentication.
    """
    try:
        user = request.state.user
        content = await file.read()
        
        if file.filename.endswith('.csv'):
            import io
            df = pd.read_csv(io.BytesIO(content))
            sections_list = []
            
            for _, row in df.iterrows():
                section = Section(
                    id=str(row['id']),
                    name=row['name'],
                    program=row['program'],
                    year=int(row['year']),
                    semester=int(row['semester']),
                    num_students=int(row['num_students']),
                    subjects=row['subjects'].split(',') if pd.notna(row.get('subjects')) else []
                )
                sections_list.append(section)
        
        elif file.filename.endswith('.json'):
            data = json.loads(content)
            sections_list = [Section(**item) for item in data]
        else:
            raise HTTPException(status_code=400, detail="File must be CSV or JSON")
        
        data_store["sections"] = sections_list
        
        return {
            "success": True,
            "message": f"Uploaded {len(sections_list)} sections",
            "count": len(sections_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-timetable")
@auth_required
async def generate_timetable(request: Request, request_data: GenerateTimetableRequest):
    """
    Generate timetable using AI agents.
    Requires authentication.
    """
    # User is automatically set by @auth_required decorator in request.state.user
    
    try:
        
        # Validate we have all required data
        if not all([
            data_store["faculty"],
            data_store["subjects"],
            data_store["classrooms"],
            data_store["sections"]
        ]):
            raise HTTPException(
                status_code=400,
                detail="Please upload all required data: faculty, subjects, classrooms, and sections"
            )
        
        # Filter sections if specific ones requested
        sections = data_store["sections"]
        if request_data.section_ids:
            sections = [s for s in sections if s.id in request_data.section_ids]
        
        # Step 1: Generate initial timetable using TimetableAgent
        timetable_result = await timetable_agent.run({
            "sections": sections,
            "subjects": data_store["subjects"],
            "faculty": data_store["faculty"],
            "classrooms": data_store["classrooms"],
            "constraints": data_store["constraints"]
        })
        
        if not timetable_result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate timetable: {timetable_result.message}"
            )
        
        schedule_entries = timetable_result.data.get("schedule_entries", [])
        
        # Step 2: Validate constraints using ConstraintAgent
        constraint_result = await constraint_agent.run({
            "schedule_entries": schedule_entries,
            "constraints": data_store["constraints"]
        })
        
        # Create timetable object
        timetable_id = f"tt_{request_data.academic_year}_{request_data.semester}_{len(data_store['timetables'])}"
        timetable = {
            "id": timetable_id,
            "name": f"Timetable {request_data.academic_year} Semester {request_data.semester}",
            "academic_year": request_data.academic_year,
            "semester": request_data.semester,
            "schedule": schedule_entries,
            "constraints_satisfied": constraint_result.success,
            "validation_results": constraint_result.data
        }
        
        data_store["timetables"].append(timetable)
        
        return {
            "success": True,
            "timetable_id": timetable_id,
            "message": f"Generated timetable with {len(schedule_entries)} entries",
            "schedule": schedule_entries,
            "validation": constraint_result.data,
            "constraints_satisfied": constraint_result.success
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/timetable/{timetable_id}")
async def get_timetable(timetable_id: str):
    """Get a specific timetable by ID."""
    for tt in data_store["timetables"]:
        if tt["id"] == timetable_id:
            return tt
    raise HTTPException(status_code=404, detail="Timetable not found")


@app.get("/api/timetables")
async def list_timetables():
    """List all generated timetables."""
    return {
        "timetables": [
            {
                "id": tt["id"],
                "name": tt["name"],
                "academic_year": tt["academic_year"],
                "semester": tt["semester"],
                "entries_count": len(tt["schedule"]),
                "constraints_satisfied": tt.get("constraints_satisfied", False)
            }
            for tt in data_store["timetables"]
        ]
    }


@app.get("/api/data/summary")
async def get_data_summary():
    """Get summary of uploaded data."""
    return {
        "faculty_count": len(data_store["faculty"]),
        "subjects_count": len(data_store["subjects"]),
        "classrooms_count": len(data_store["classrooms"]),
        "sections_count": len(data_store["sections"]),
        "constraints_count": len(data_store["constraints"]),
        "timetables_count": len(data_store["timetables"])
    }


if __name__ == "__main__":
    import uvicorn
    import os
    
    # Use PORT environment variable from Cloud Run, fallback to settings
    port = int(os.environ.get("PORT", settings.api_port))
    uvicorn.run(app, host=settings.api_host, port=port)
