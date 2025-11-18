"""Timetable generation agent using Gemini AI."""
from typing import Dict, Any, List, Set, Tuple
from agents.base_agent import BaseAgent, AgentResult
from services.gemini_service import gemini_service
from models import Section, Subject, Faculty, Classroom


class TimetableAgent(BaseAgent):
    """Agent responsible for generating timetable using AI with constraint validation."""
    
    def __init__(self):
        super().__init__(
            name="TimetableAgent",
            description="Generates constraint-aware timetable"
        )
        self.gemini = gemini_service
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Generate timetable with constraint checking.
        
        Args:
            input_data: Contains sections, subjects, faculty, classrooms, constraints
            
        Returns:
            AgentResult with generated schedule
        """
        try:
            sections = input_data.get("sections", [])
            subjects = input_data.get("subjects", [])
            faculty = input_data.get("faculty", [])
            classrooms = input_data.get("classrooms", [])
            constraints = input_data.get("constraints", [])
            
            # Generate time slots
            time_slots = self._generate_time_slots()
            
            # Track resource usage to avoid conflicts
            faculty_schedule: Dict[str, Set[str]] = {}  # faculty_id -> set of slot_ids
            classroom_schedule: Dict[str, Set[str]] = {}  # classroom_id -> set of slot_ids
            section_schedule: Dict[str, Set[str]] = {}  # section_id -> set of slot_ids
            
            # Generate schedule for each section with constraint checking
            all_schedule_entries = []
            
            for section in sections:
                section_dict = section if isinstance(section, dict) else section.dict()
                section_id = section_dict.get("id")
                section_schedule[section_id] = set()
                
                # Get subjects for this section
                section_subject_ids = section_dict.get("subjects", [])
                section_subjects = [
                    s for s in subjects
                    if (s.get("id") if isinstance(s, dict) else s.id) in section_subject_ids
                ]
                
                # Schedule each subject for this section
                for subject in section_subjects:
                    subject_dict = subject if isinstance(subject, dict) else subject.dict()
                    hours_per_week = subject_dict.get("hours_per_week", 3)
                    
                    # Try to schedule the required hours
                    classes_scheduled = 0
                    for slot in time_slots:
                        if classes_scheduled >= hours_per_week:
                            break
                        
                        slot_id = slot["slot_id"]
                        
                        # Check if section is already busy
                        if slot_id in section_schedule[section_id]:
                            continue
                        
                        # Find suitable faculty
                        suitable_faculty = self._find_available_faculty(
                            subject_dict, faculty, faculty_schedule, slot_id
                        )
                        
                        if not suitable_faculty:
                            continue
                        
                        # Find suitable classroom
                        suitable_classroom = self._find_available_classroom(
                            section_dict, classrooms, classroom_schedule, slot_id
                        )
                        
                        if not suitable_classroom:
                            continue
                        
                        # Create schedule entry
                        entry = {
                            "day": slot["day"],
                            "start_time": slot["start_time"],
                            "end_time": slot["end_time"],
                            "subject": subject_dict,
                            "subject_id": subject_dict["id"],
                            "faculty": suitable_faculty,
                            "faculty_id": suitable_faculty["id"],
                            "classroom": suitable_classroom,
                            "classroom_id": suitable_classroom["id"],
                            "section": section_dict,
                            "section_id": section_id
                        }
                        
                        # Mark resources as used
                        if suitable_faculty["id"] not in faculty_schedule:
                            faculty_schedule[suitable_faculty["id"]] = set()
                        faculty_schedule[suitable_faculty["id"]].add(slot_id)
                        
                        if suitable_classroom["id"] not in classroom_schedule:
                            classroom_schedule[suitable_classroom["id"]] = set()
                        classroom_schedule[suitable_classroom["id"]].add(slot_id)
                        
                        section_schedule[section_id].add(slot_id)
                        
                        all_schedule_entries.append(entry)
                        classes_scheduled += 1
            
            return AgentResult(
                success=True,
                data={
                    "schedule_entries": all_schedule_entries,
                    "total_entries": len(all_schedule_entries),
                    "sections_scheduled": len(sections)
                },
                message=f"Generated {len(all_schedule_entries)} conflict-free schedule entries for {len(sections)} sections"
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                message=f"Failed to generate timetable: {str(e)}",
                errors=[str(e)]
            )
    
    def _find_available_faculty(
        self,
        subject: Dict[str, Any],
        faculty_list: List[Any],
        faculty_schedule: Dict[str, Set[str]],
        slot_id: str
    ) -> Dict[str, Any]:
        """Find faculty who can teach this subject and is available."""
        subject_id = subject.get("id")
        
        for faculty in faculty_list:
            faculty_dict = faculty if isinstance(faculty, dict) else faculty.dict()
            faculty_id = faculty_dict.get("id")
            
            # Check if faculty can teach this subject
            can_teach = faculty_dict.get("subjects_can_teach", [])
            if subject_id not in can_teach:
                continue
            
            # Check if faculty is available
            if faculty_id in faculty_schedule:
                if slot_id in faculty_schedule[faculty_id]:
                    continue
            
            return faculty_dict
        
        return None
    
    def _find_available_classroom(
        self,
        section: Dict[str, Any],
        classroom_list: List[Any],
        classroom_schedule: Dict[str, Set[str]],
        slot_id: str
    ) -> Dict[str, Any]:
        """Find classroom with sufficient capacity that is available."""
        section_size = section.get("num_students", 0)
        
        # Sort classrooms by capacity (prefer smaller rooms that fit)
        sorted_classrooms = sorted(
            classroom_list,
            key=lambda c: c.get("capacity") if isinstance(c, dict) else c.capacity
        )
        
        for classroom in sorted_classrooms:
            classroom_dict = classroom if isinstance(classroom, dict) else classroom.dict()
            classroom_id = classroom_dict.get("id")
            capacity = classroom_dict.get("capacity", 0)
            
            # Check capacity
            if capacity < section_size:
                continue
            
            # Check availability
            if classroom_id in classroom_schedule:
                if slot_id in classroom_schedule[classroom_id]:
                    continue
            
            return classroom_dict
        
        return None
    
    def _generate_time_slots(self) -> List[Dict[str, Any]]:
        """Generate available time slots."""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        time_slots = []
        
        # Generate slots from 9 AM to 5 PM with 1-hour duration
        hours = [
            ("09:00", "10:00"),
            ("10:00", "11:00"),
            ("11:00", "12:00"),
            # ("12:00", "13:00"),  # Lunch break
            ("13:00", "14:00"),
            ("14:00", "15:00"),
            ("15:00", "16:00"),
            ("16:00", "17:00"),
        ]
        
        for day in days:
            for start_time, end_time in hours:
                time_slots.append({
                    "day": day,
                    "start_time": start_time,
                    "end_time": end_time,
                    "slot_id": f"{day}_{start_time}_{end_time}"
                })
        
        return time_slots
