from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class ProviderType(str, Enum):
    OPENAI = "openai"
    GROQ = "groq"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    FALLBACK = "fallback"


@dataclass
class GenerationResult:
    content: str
    provider: ProviderType
    model: str
    usage: Dict[str, int]
    latency_ms: float
    fallback: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "provider": self.provider.value,
            "model": self.model,
            "usage": self.usage,
            "latency_ms": self.latency_ms,
            "fallback": self.fallback,
            "metadata": self.metadata
        }


class BaseLLMProvider(ABC):
    def __init__(self, provider_type: ProviderType, priority: int = 99):
        self.provider_type = provider_type
        self.priority = priority
        self.available = False
        self._check_availability()
    
    @abstractmethod
    def _check_availability(self) -> None:
        """Check if provider is properly configured and available"""
        pass
    
    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> GenerationResult:
        """Generate completion"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model name being used"""
        pass
    
    def is_available(self) -> bool:
        return self.available
    
    def health_check(self) -> Dict[str, Any]:
        """Return health status of provider"""
        return {
            "provider": self.provider_type.value,
            "available": self.available,
            "priority": self.priority,
            "model": self.get_model_name() if self.available else None
        }
