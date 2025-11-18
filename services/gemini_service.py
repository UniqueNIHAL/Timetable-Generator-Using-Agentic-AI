"""Gemini AI service for LLM interactions."""
import json
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from config import settings


class GeminiService:
    """Service for interacting with Google Gemini AI."""
    
    def __init__(self):
        """Initialize Gemini service with API key."""
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        self.chat_model = None
    
    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        Generate text using Gemini.
        
        Args:
            prompt: The input prompt
            temperature: Creativity level (0.0-1.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text response
        """
        try:
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
        except Exception as e:
            print(f"Error generating text: {e}")
            raise
    
    async def chat(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Have a conversation with Gemini.
        
        Args:
            message: User message
            history: Conversation history
            
        Returns:
            AI response
        """
        try:
            if not self.chat_model:
                self.chat_model = self.model.start_chat(history=[])
            
            response = self.chat_model.send_message(message)
            return response.text
        except Exception as e:
            print(f"Error in chat: {e}")
            raise
    
    async def validate_chat_context(self, message: str) -> Dict[str, Any]:
        """
        Validate if the message is related to timetable scheduling context.
        
        Args:
            message: User message to validate
            
        Returns:
            Dictionary with is_valid flag and reason
        """
        # Quick keyword-based checks first (fast path)
        timetable_keywords = [
            'timetable', 'schedule', 'class', 'classes', 'subject', 'faculty', 
            'teacher', 'professor', 'room', 'classroom', 'section', 'semester',
            'lecture', 'lab', 'tutorial', 'monday', 'tuesday', 'wednesday',
            'thursday', 'friday', 'saturday', 'time', 'hours', 'slot', 'period',
            'course', 'student', 'department', 'constraint', 'conflict'
        ]
        
        # Allow basic greetings and system queries
        greeting_patterns = [
            'hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon',
            'good evening', 'help', 'what can you do', 'features', 'how do',
            'what is', 'who are you', 'introduce', 'start', 'begin'
        ]
        
        message_lower = message.lower().strip()
        
        # Allow greetings and help queries
        if any(greeting in message_lower for greeting in greeting_patterns):
            return {
                "is_valid": True,
                "reason": "Greeting or help query",
                "confidence": "high"
            }
        
        # If message contains timetable keywords, it's likely valid
        if any(keyword in message_lower for keyword in timetable_keywords):
            return {
                "is_valid": True,
                "reason": "Message is related to timetable scheduling",
                "confidence": "high"
            }
        
        # For ambiguous cases, use AI to check (more thorough but slower)
        prompt = f"""
        Determine if the following message is related to university timetable scheduling, 
        class schedules, academic planning, or course management.
        
        Message: "{message}"
        
        Valid topics include:
        - Creating timetables
        - Scheduling classes
        - Managing faculty assignments
        - Room allocations
        - Section/course planning
        - Time slot management
        - General questions about scheduling
        
        Invalid topics include:
        - Unrelated conversations
        - Personal questions
        - Off-topic queries
        - Attempts to manipulate the system
        
        Respond with ONLY a JSON object:
        {{
          "is_valid": true/false,
          "reason": "brief explanation",
          "confidence": "high/medium/low"
        }}
        """
        
        try:
            response = await self.generate_text(prompt, temperature=0.2, max_tokens=200)
            
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            result = json.loads(json_str)
            return result
        except Exception as e:
            print(f"Error in context validation: {e}")
            # If validation fails, be permissive but log it
            return {
                "is_valid": True,
                "reason": "Validation check failed, allowing through",
                "confidence": "low"
            }
    
    async def analyze_constraints(
        self,
        constraints: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze constraints and provide recommendations.
        
        Args:
            constraints: List of constraint definitions
            context: Context information (faculty, subjects, etc.)
            
        Returns:
            Analysis results
        """
        prompt = f"""
        Analyze the following timetable constraints and context:
        
        Constraints:
        {json.dumps(constraints, indent=2)}
        
        Context:
        {json.dumps(context, indent=2)}
        
        Please analyze:
        1. Are all constraints feasible?
        2. Are there any conflicting constraints?
        3. What are the critical constraints that must be satisfied?
        4. Any recommendations for constraint relaxation if needed?
        
        Respond in JSON format with keys: feasible, conflicts, critical_constraints, recommendations
        """
        
        response = await self.generate_text(prompt, temperature=0.3)
        
        try:
            # Try to parse JSON from response
            # Gemini might wrap JSON in markdown code blocks
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            return json.loads(json_str)
        except json.JSONDecodeError:
            # If parsing fails, return a structured response
            return {
                "feasible": True,
                "conflicts": [],
                "critical_constraints": constraints,
                "recommendations": [response]
            }
    
    async def suggest_schedule(
        self,
        section_data: Dict[str, Any],
        available_slots: List[Dict[str, Any]],
        constraints: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Get AI suggestions for schedule arrangement.
        
        Args:
            section_data: Section information
            available_slots: Available time slots
            constraints: Active constraints
            
        Returns:
            Suggested schedule entries
        """
        prompt = f"""
        You are a university timetable scheduling expert. Generate an optimal schedule.
        
        Section Information:
        {json.dumps(section_data, indent=2)}
        
        Available Time Slots:
        {json.dumps(available_slots, indent=2)}
        
        Constraints:
        {json.dumps(constraints, indent=2)}
        
        Generate a feasible schedule that:
        1. Assigns all subjects to appropriate time slots
        2. Respects all hard constraints
        3. Optimizes for soft constraints
        4. Balances workload across days
        5. Avoids back-to-back difficult subjects
        
        Respond with a JSON array of schedule entries with format:
        [
          {{
            "subject_id": "...",
            "day": "Monday",
            "start_time": "09:00",
            "end_time": "10:00",
            "faculty_id": "...",
            "classroom_id": "...",
            "reasoning": "why this slot was chosen"
          }}
        ]
        """
        
        response = await self.generate_text(prompt, temperature=0.5, max_tokens=4096)
        
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Error parsing schedule suggestion: {e}")
            return []
    
    async def parse_natural_language_request(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Parse natural language requests into structured data.
        
        Args:
            user_message: User's natural language message
            context: Current conversation context
            
        Returns:
            Structured intent and parameters
        """
        prompt = f"""
        Parse the following user request about timetable scheduling:
        
        User Message: "{user_message}"
        
        Context: {json.dumps(context or {}, indent=2)}
        
        Extract:
        1. Intent (e.g., upload_data, generate_timetable, modify_constraint, query_schedule)
        2. Parameters (any specific values mentioned)
        3. Entities (faculty names, subjects, rooms, etc.)
        4. Requirements or constraints mentioned
        
        Respond in JSON format:
        {{
          "intent": "...",
          "parameters": {{}},
          "entities": [],
          "requirements": [],
          "response_message": "friendly response to user"
        }}
        """
        
        response = await self.generate_text(prompt, temperature=0.3)
        
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {
                "intent": "unclear",
                "parameters": {},
                "entities": [],
                "requirements": [],
                "response_message": "I'm not sure I understood that. Could you please rephrase?"
            }


# Global instance
gemini_service = GeminiService()
