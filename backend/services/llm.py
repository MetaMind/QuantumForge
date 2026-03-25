from typing import Any, Dict

from backend.services.llm_providers import LLMRouter, ProviderType
from backend.core.config import settings
from backend.core.exceptions import LLMException
from backend.core.logger import get_logger, log_structured

logger = get_logger(__name__)


class LLMClient:
    """Unified LLM client with multi-provider support"""
    
    def __init__(self, preferred_provider: ProviderType = None):
        self.router = LLMRouter()
        self.preferred = preferred_provider
    
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = None,
        max_tokens: int = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion with automatic provider selection"""
        try:
            result = self.router.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature or settings.default_temperature,
                max_tokens=max_tokens or settings.default_max_tokens,
                preferred_provider=self.preferred,
                **kwargs
            )
            
            # Convert to legacy format for backward compatibility
            return {
                "content": result.content,
                "provider": result.provider.value,
                "model": result.model,
                "usage": result.usage,
                "latency_ms": result.latency_ms,
                "fallback": result.fallback,
                "metadata": result.metadata
            }
            
        except Exception as e:
            log_structured(logger, "error", "LLM generation failed", error=str(e))
            raise LLMException(f"LLM generation failed: {e}")
    
    def generate_with_provider(
        self,
        provider: ProviderType,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Force generation with specific provider"""
        result = self.router.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            preferred_provider=provider,
            **kwargs
        )
        
        return {
            "content": result.content,
            "provider": result.provider.value,
            "model": result.model,
            "usage": result.usage,
            "latency_ms": result.latency_ms,
            "fallback": result.fallback,
            "metadata": result.metadata
        }
    
    def get_health(self) -> Dict[str, Any]:
        """Get health status of all providers"""
        return self.router.get_health_status()
    
    def set_strategy(self, strategy: str):
        """Change routing strategy (priority, round_robin, load_balance, random)"""
        self.router.strategy = strategy


# Global instance for backward compatibility
llm_client = LLMClient()
