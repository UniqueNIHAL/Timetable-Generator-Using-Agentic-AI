"""Data models for the timetable planner."""
from datetime import time
from typing import List, Optional
from pydantic import BaseModel, Field


class TimeSlot(BaseModel):
    """Represents a time slot in the schedule."""
    day: str  # Monday, Tuesday, etc.
    start_time: str  # "09:00"
    end_time: str  # "10:00"
    slot_id: str = Field(default="")
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.slot_id:
            self.slot_id = f"{self.day}_{self.start_time}_{self.end_time}"


class Faculty(BaseModel):
    """Faculty member information."""
    id: str
    name: str
    email: Optional[str] = None
    department: str
    subjects_can_teach: List[str]  # List of subject IDs
    max_hours_per_week: int = 20
    unavailable_slots: List[TimeSlot] = Field(default_factory=list)
    preferences: Optional[dict] = None


class Subject(BaseModel):
    """Subject/Course information."""
    id: str
    name: str
    code: str
    department: str
    credits: int
    hours_per_week: int
    lecture_type: str = "theory"  # theory, lab, tutorial
    requires_lab: bool = False
    lab_hours: int = 0
    track: Optional[str] = None  # For track-based curriculum
    is_elective: bool = False
    is_open_elective: bool = False
    prerequisites: List[str] = Field(default_factory=list)


class Classroom(BaseModel):
    """Classroom/venue information."""
    id: str
    name: str
    building: str
    capacity: int
    room_type: str = "lecture_hall"  # lecture_hall, lab, seminar_room
    facilities: List[str] = Field(default_factory=list)  # projector, computers, etc.
    unavailable_slots: List[TimeSlot] = Field(default_factory=list)


class Section(BaseModel):
    """Student section/batch information."""
    id: str
    name: str
    program: str  # B.Tech CSE, B.Tech ECE, etc.
    year: int
    semester: int
    num_students: int
    track: Optional[str] = None  # For track-based sections
    subjects: List[str]  # List of subject IDs for this section
    electives: List[str] = Field(default_factory=list)  # Elective subject IDs


class ScheduleEntry(BaseModel):
    """Single entry in the timetable."""
    slot: TimeSlot
    subject: Subject
    faculty: Faculty
    classroom: Classroom
    section: Section
    entry_type: str = "regular"  # regular, lab, tutorial


class Timetable(BaseModel):
    """Complete timetable."""
    id: str
    name: str
    academic_year: str
    semester: int
    schedule: List[ScheduleEntry]
    created_at: Optional[str] = None
    metadata: Optional[dict] = None
    constraints_satisfied: bool = False
    optimization_score: float = 0.0


class Constraint(BaseModel):
    """Constraint definition."""
    id: str
    name: str
    constraint_type: str  # hard, soft
    description: str
    priority: int = 1  # 1-10, 10 being highest
    parameters: Optional[dict] = None


class TimetableRequest(BaseModel):
    """Request to generate a timetable."""
    academic_year: str
    semester: int
    sections: List[Section]
    subjects: List[Subject]
    faculty: List[Faculty]
    classrooms: List[Classroom]
    constraints: List[Constraint] = Field(default_factory=list)
    preferences: Optional[dict] = None
