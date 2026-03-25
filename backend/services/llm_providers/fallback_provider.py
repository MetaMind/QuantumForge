import time
from typing import Any, Dict, Optional

from backend.core.logger import get_logger
from backend.services.llm_providers.base import BaseLLMProvider, GenerationResult, ProviderType

logger = get_logger(__name__)


class FallbackProvider(BaseLLMProvider):
    """Mock provider for testing without API keys"""
    
    def __init__(self):
        super().__init__(ProviderType.FALLBACK, 999)
    
    def _check_availability(self) -> None:
        self.available = True
    
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> GenerationResult:
        start_time = time.time()
        
        content = self._generate_mock_response(user_prompt)
        latency_ms = (time.time() - start_time) * 1000
        
        return GenerationResult(
            content=content,
            provider=self.provider_type,
            model="fallback-mock",
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            latency_ms=latency_ms,
            fallback=True,
            metadata={"note": "Mock response for testing"}
        )
    
    def _generate_mock_response(self, prompt: str) -> str:
        """Generate contextually relevant mock responses"""
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ["hello", "world", "print"]):
            return 'print("Hello, World!")'
        elif any(word in prompt_lower for word in ["fibonacci", "fib", "sequence"]):
            return """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))"""
        elif any(word in prompt_lower for word in ["sort", "bubble", "quick", "merge"]):
            return """def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

print(quick_sort([64, 34, 25, 12, 22, 11, 90]))"""
        elif any(word in prompt_lower for word in ["plan", "decompose", "steps"]):
            return """{
  "steps": [
    {"id": "step_1", "description": "Analyze requirements", "verification": "Understand the problem"},
    {"id": "step_2", "description": "Design solution", "verification": "Architecture defined"},
    {"id": "step_3", "description": "Implement code", "verification": "Code compiles"}
  ],
  "estimated_complexity": "medium"
}"""
        else:
            return 'print("Task completed successfully")'
    
    def get_model_name(self) -> str:
        return "fallback-mock"
