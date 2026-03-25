from abc import ABC, abstractmethod
from typing import Any, Dict, List

from backend.core.logger import get_logger
from backend.core.models import AgentOutput
from backend.services.llm import LLMClient

logger = get_logger(__name__)


class BaseAgent(ABC):
    def __init__(self, agent_type: str, llm: LLMClient = None):
        self.agent_type = agent_type
        self.llm = llm or LLMClient()
        self.history: List[AgentOutput] = []
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        pass
    
    def run(self, task_input: Dict[str, Any]) -> AgentOutput:
        user_prompt = self.format_prompt(task_input)
        
        response = self.llm.generate(
            system_prompt=self.get_system_prompt(),
            user_prompt=user_prompt
        )
        
        output = AgentOutput(
            agent_type=self.agent_type,
            content=response["content"],
            metadata={
                "usage": response.get("usage", {}),
                "fallback": response.get("fallback", False)
            }
        )
        
        self.history.append(output)
        return output
    
    def format_prompt(self, task_input: Dict[str, Any]) -> str:
        return str(task_input)
    
    def get_history(self) -> List[AgentOutput]:
        return self.history.copy()
