"""Constraint validation agent."""
from typing import Dict, Any, List
from agents.base_agent import BaseAgent, AgentResult
from models import TimeSlot, Faculty, Subject, Classroom, Section, ScheduleEntry


class ConstraintAgent(BaseAgent):
    """Agent responsible for validating constraints."""
    
    def __init__(self):
        super().__init__(
            name="ConstraintAgent",
            description="Validates hard and soft constraints in the timetable"
        )
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Validate all constraints in the proposed schedule.
        
        Args:
            input_data: Contains schedule entries and constraint definitions
            
        Returns:
            AgentResult with validation results
        """
        schedule_entries = input_data.get("schedule_entries", [])
        constraints = input_data.get("constraints", [])
        
        violations = []
        warnings = []
        
        # Run all validation checks
        violations.extend(self._check_faculty_conflicts(schedule_entries))
        violations.extend(self._check_classroom_conflicts(schedule_entries))
        violations.extend(self._check_section_conflicts(schedule_entries))
        violations.extend(self._check_faculty_availability(schedule_entries))
        violations.extend(self._check_classroom_capacity(schedule_entries))
        warnings.extend(self._check_workload_balance(schedule_entries))
        warnings.extend(self._check_subject_distribution(schedule_entries))
        
        success = len(violations) == 0
        
        return AgentResult(
            success=success,
            data={
                "violations": violations,
                "warnings": warnings,
                "total_entries": len(schedule_entries),
                "valid_entries": len(schedule_entries) - len(violations)
            },
            message=f"Validated {len(schedule_entries)} schedule entries. "
                   f"Found {len(violations)} violations and {len(warnings)} warnings."
        )
    
    def _check_faculty_conflicts(self, entries: List[Dict[str, Any]]) -> List[str]:
        """Check for faculty double-booking."""
        violations = []
        faculty_schedule: Dict[str, List[Dict[str, Any]]] = {}
        
        for entry in entries:
            faculty_id = entry.get("faculty_id") or entry.get("faculty", {}).get("id")
            if not faculty_id:
                continue
            
            if faculty_id not in faculty_schedule:
                faculty_schedule[faculty_id] = []
            
            slot_key = f"{entry.get('day')}_{entry.get('start_time')}_{entry.get('end_time')}"
            
            for existing in faculty_schedule[faculty_id]:
                existing_key = f"{existing.get('day')}_{existing.get('start_time')}_{existing.get('end_time')}"
                if slot_key == existing_key:
                    violations.append(
                        f"Faculty conflict: {faculty_id} assigned to multiple classes at {slot_key}"
                    )
            
            faculty_schedule[faculty_id].append(entry)
        
        return violations
    
    def _check_classroom_conflicts(self, entries: List[Dict[str, Any]]) -> List[str]:
        """Check for classroom double-booking."""
        violations = []
        classroom_schedule: Dict[str, List[Dict[str, Any]]] = {}
        
        for entry in entries:
            classroom_id = entry.get("classroom_id") or entry.get("classroom", {}).get("id")
            if not classroom_id:
                continue
            
            if classroom_id not in classroom_schedule:
                classroom_schedule[classroom_id] = []
            
            slot_key = f"{entry.get('day')}_{entry.get('start_time')}_{entry.get('end_time')}"
            
            for existing in classroom_schedule[classroom_id]:
                existing_key = f"{existing.get('day')}_{existing.get('start_time')}_{existing.get('end_time')}"
                if slot_key == existing_key:
                    violations.append(
                        f"Classroom conflict: {classroom_id} double-booked at {slot_key}"
                    )
            
            classroom_schedule[classroom_id].append(entry)
        
        return violations
    
    def _check_section_conflicts(self, entries: List[Dict[str, Any]]) -> List[str]:
        """Check for section double-booking."""
        violations = []
        section_schedule: Dict[str, List[Dict[str, Any]]] = {}
        
        for entry in entries:
            section_id = entry.get("section_id") or entry.get("section", {}).get("id")
            if not section_id:
                continue
            
            if section_id not in section_schedule:
                section_schedule[section_id] = []
            
            slot_key = f"{entry.get('day')}_{entry.get('start_time')}_{entry.get('end_time')}"
            
            for existing in section_schedule[section_id]:
                existing_key = f"{existing.get('day')}_{existing.get('start_time')}_{existing.get('end_time')}"
                if slot_key == existing_key:
                    violations.append(
                        f"Section conflict: {section_id} has multiple classes at {slot_key}"
                    )
            
            section_schedule[section_id].append(entry)
        
        return violations
    
    def _check_faculty_availability(self, entries: List[Dict[str, Any]]) -> List[str]:
        """Check if faculty are assigned during unavailable slots."""
        violations = []
        # This would check against faculty unavailable_slots
        # Implementation depends on how unavailable slots are stored
        return violations
    
    def _check_classroom_capacity(self, entries: List[Dict[str, Any]]) -> List[str]:
        """Check if classroom capacity matches section size."""
        violations = []
        
        for entry in entries:
            classroom_capacity = entry.get("classroom", {}).get("capacity", 999)
            section_size = entry.get("section", {}).get("num_students", 0)
            
            if section_size > classroom_capacity:
                violations.append(
                    f"Capacity violation: Section with {section_size} students "
                    f"assigned to classroom with capacity {classroom_capacity}"
                )
        
        return violations
    
    def _check_workload_balance(self, entries: List[Dict[str, Any]]) -> List[str]:
        """Check for balanced workload distribution (soft constraint)."""
        warnings = []
        faculty_hours: Dict[str, int] = {}
        
        for entry in entries:
            faculty_id = entry.get("faculty_id") or entry.get("faculty", {}).get("id")
            if not faculty_id:
                continue
            
            # Assuming 1-hour slots
            faculty_hours[faculty_id] = faculty_hours.get(faculty_id, 0) + 1
        
        for faculty_id, hours in faculty_hours.items():
            if hours > 20:
                warnings.append(
                    f"Workload warning: Faculty {faculty_id} has {hours} hours (max recommended: 20)"
                )
        
        return warnings
    
    def _check_subject_distribution(self, entries: List[Dict[str, Any]]) -> List[str]:
        """Check for good distribution of subjects across days (soft constraint)."""
        warnings = []
        # Could check for clustering of difficult subjects, etc.
        return warnings
