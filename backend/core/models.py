from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    EVALUATING = "evaluating"
    FIXING = "fixing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExecutionResult(BaseModel):
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    execution_time: float = 0.0
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "stdout": "Hello World",
                "stderr": "",
                "exit_code": 0,
                "execution_time": 1.5
            }
        }


class AgentOutput(BaseModel):
    agent_type: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    score: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_type": "executor",
                "content": "def hello(): return 'world'",
                "metadata": {"tokens_used": 150},
                "score": 0.85
            }
        }


class TaskStep(BaseModel):
    step_id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    attempts: List[Dict[str, Any]] = Field(default_factory=list)
    best_attempt: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class Task(BaseModel):
    task_id: str = Field(default_factory=lambda: f"task_{datetime.utcnow().timestamp()}")
    description: str
    status: TaskStatus = TaskStatus.PENDING
    steps: List[TaskStep] = Field(default_factory=list)
    final_output: Optional[str] = None
    metrics: Dict[str, float] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MemoryEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: f"mem_{datetime.utcnow().timestamp()}")
    task_description: str
    code: str
    result: ExecutionResult
    score: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)


class PromptGenome(BaseModel):
    genome_id: str = Field(default_factory=lambda: f"genome_{datetime.utcnow().timestamp()}")
    system_prompt: str
    task_prompt_template: str
    score: float = 0.0
    usage_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
