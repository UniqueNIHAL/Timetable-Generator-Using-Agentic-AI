"""Base agent class for timetable planning."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum


class AgentStatus(Enum):
    """Agent execution status."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentResult:
    """Result from agent execution."""
    
    def __init__(
        self,
        success: bool,
        data: Any = None,
        message: str = "",
        errors: List[str] = None
    ):
        self.success = success
        self.data = data
        self.message = message
        self.errors = errors or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "message": self.message,
            "errors": self.errors
        }


class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.status = AgentStatus.IDLE
        self.results: List[AgentResult] = []
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute the agent's main task.
        
        Args:
            input_data: Input data for the agent
            
        Returns:
            AgentResult with execution results
        """
        pass
    
    async def run(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Run the agent with status tracking.
        
        Args:
            input_data: Input data for the agent
            
        Returns:
            AgentResult with execution results
        """
        try:
            self.status = AgentStatus.RUNNING
            result = await self.execute(input_data)
            self.results.append(result)
            self.status = AgentStatus.COMPLETED if result.success else AgentStatus.FAILED
            return result
        except Exception as e:
            error_result = AgentResult(
                success=False,
                message=f"Agent {self.name} failed",
                errors=[str(e)]
            )
            self.results.append(error_result)
            self.status = AgentStatus.FAILED
            return error_result
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "results_count": len(self.results)
        }
