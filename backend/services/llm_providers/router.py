import random
import time
from typing import Any, Dict, List, Optional

from backend.core.config import settings
from backend.core.logger import get_logger, log_structured
from backend.core.exceptions import LLMException
from backend.services.llm_providers.base import BaseLLMProvider, GenerationResult, ProviderType
from backend.services.llm_providers.openai_provider import OpenAIProvider
from backend.services.llm_providers.groq_provider import GroqProvider
from backend.services.llm_providers.anthropic_provider import AnthropicProvider
from backend.services.llm_providers.local_provider import LocalProvider
from backend.services.llm_providers.fallback_provider import FallbackProvider

logger = get_logger(__name__)


class LLMRouter:
    """Intelligent routing across multiple LLM providers"""
    
    def __init__(self):
        self.providers: Dict[ProviderType, BaseLLMProvider] = {}
        self.strategy = settings.llm_routing_strategy
        self.max_retries = settings.max_retries_per_provider
        self._last_provider_idx = 0
        self._provider_health: Dict[ProviderType, Dict] = {}
        
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all configured providers"""
        provider_map = {
            ProviderType.OPENAI: OpenAIProvider,
            ProviderType.GROQ: GroqProvider,
            ProviderType.ANTHROPIC: AnthropicProvider,
            ProviderType.LOCAL: LocalProvider,
            ProviderType.FALLBACK: FallbackProvider
        }
        
        for provider_name in settings.llm_providers:
            try:
                provider_type = ProviderType(provider_name)
                provider_class = provider_map.get(provider_type)
                
                if provider_class:
                    provider = provider_class()
                    self.providers[provider_type] = provider
                    self._provider_health[provider_type] = {
                        "success_count": 0,
                        "failure_count": 0,
                        "avg_latency": 0,
                        "last_used": None
                    }
                    
                    if provider.is_available():
                        log_structured(
                            logger, "info", f"Provider {provider_name} available",
                            priority=provider.priority
                        )
            except Exception as e:
                logger.error(f"Failed to initialize provider {provider_name}: {e}")
        
        if not self.providers:
            # Ensure fallback is always available
            fallback = FallbackProvider()
            self.providers[ProviderType.FALLBACK] = fallback
    
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        preferred_provider: Optional[ProviderType] = None,
        **kwargs
    ) -> GenerationResult:
        """Generate with automatic failover"""
        providers_to_try = self._select_providers(preferred_provider)
        
        last_error = None
        
        for provider in providers_to_try:
            for attempt in range(self.max_retries):
                try:
                    start_time = time.time()
                    
                    result = provider.generate(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs
                    )
                    
                    # Update health metrics
                    self._update_health(provider.provider_type, result, time.time() - start_time)
                    
                    log_structured(
                        logger, "info", "Generation successful",
                        provider=provider.provider_type.value,
                        model=result.model,
                        latency_ms=result.latency_ms,
                        attempt=attempt + 1
                    )
                    
                    return result
                    
                except Exception as e:
                    last_error = e
                    log_structured(
                        logger, "warning", "Provider attempt failed",
                        provider=provider.provider_type.value,
                        attempt=attempt + 1,
                        error=str(e)
                    )
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
        
        # All providers failed
        raise LLMException(f"All providers failed. Last error: {last_error}")
    
    def _select_providers(
        self,
        preferred: Optional[ProviderType] = None
    ) -> List[BaseLLMProvider]:
        """Select providers based on routing strategy"""
        available = [
            p for p in self.providers.values() 
            if p.is_available() and p.provider_type != ProviderType.FALLBACK
        ]
        
        # Sort by priority
        available.sort(key=lambda p: p.priority)
        
        if preferred and preferred in self.providers:
            if self.providers[preferred].is_available():
                # Put preferred first
                available.insert(0, self.providers[preferred])
        
        if not available:
            # Return fallback as last resort
            return [self.providers[ProviderType.FALLBACK]]
        
        if self.strategy == "priority":
            return available
        
        elif self.strategy == "round_robin":
            idx = self._last_provider_idx % len(available)
            self._last_provider_idx = (self._last_provider_idx + 1) % len(available)
            return [available[idx]] + available[:idx] + available[idx+1:]
        
        elif self.strategy == "load_balance":
            # Sort by lowest latency
            available.sort(
                key=lambda p: self._provider_health.get(
                    p.provider_type, {}
                ).get("avg_latency", float('inf'))
            )
            return available
        
        elif self.strategy == "random":
            random.shuffle(available)
            return available
        
        return available
    
    def _update_health(
        self,
        provider_type: ProviderType,
        result: GenerationResult,
        duration: float
    ):
        """Update provider health metrics"""
        health = self._provider_health.get(provider_type, {})
        
        health["success_count"] = health.get("success_count", 0) + 1
        health["last_used"] = time.time()
        
        # Update rolling average latency
        current_avg = health.get("avg_latency", 0)
        count = health["success_count"]
        health["avg_latency"] = (current_avg * (count - 1) + result.latency_ms) / count
        
        self._provider_health[provider_type] = health
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all providers"""
        return {
            provider_type.value: {
                **provider.health_check(),
                **self._provider_health.get(provider_type, {})
            }
            for provider_type, provider in self.providers.items()
        }
    
    def force_provider(self, provider_type: ProviderType) -> bool:
        """Temporarily force a specific provider"""
        if provider_type in self.providers and self.providers[provider_type].is_available():
            self.strategy = "priority"
            # Reorder providers to put selected first
            provider = self.providers[provider_type]
            self.providers = {provider_type: provider, **self.providers}
            return True
        return False
