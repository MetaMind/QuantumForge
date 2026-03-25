import time
from typing import Any, Dict, Optional

import anthropic
from anthropic import Anthropic

from backend.core.config import settings
from backend.core.logger import get_logger
from backend.core.exceptions import LLMException
from backend.services.llm_providers.base import BaseLLMProvider, GenerationResult, ProviderType

logger = get_logger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider"""
    
    def __init__(self):
        self.client: Optional[Anthropic] = None
        self.model = settings.anthropic_model
        self.timeout = settings.anthropic_timeout
        self.max_tokens = settings.anthropic_max_tokens
        self.temperature = settings.anthropic_temperature
        super().__init__(ProviderType.ANTHROPIC, settings.anthropic_priority)
    
    def _check_availability(self) -> None:
        if settings.anthropic_api_key:
            try:
                self.client = Anthropic(
                    api_key=settings.anthropic_api_key,
                    timeout=self.timeout
                )
                self.available = True
                logger.info(f"Anthropic provider initialized with model {self.model}")
            except Exception as e:
                logger.warning(f"Anthropic provider unavailable: {e}")
                self.available = False
        else:
            logger.info("Anthropic API key not configured")
            self.available = False
    
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> GenerationResult:
        if not self.client:
            raise LLMException("Anthropic client not initialized")
        
        start_time = time.time()
        temp = temperature or self.temperature
        tokens = max_tokens or self.max_tokens
        
        try:
            # Anthropic uses different message format
            message = self.client.messages.create(
                model=self.model,
                max_tokens=tokens,
                temperature=temp,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": user_prompt
                }],
                **kwargs
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract text content
            content = ""
            for block in message.content:
                if hasattr(block, 'text'):
                    content += block.text
            
            return GenerationResult(
                content=content,
                provider=self.provider_type,
                model=self.model,
                usage={
                    "prompt_tokens": message.usage.input_tokens,
                    "completion_tokens": message.usage.output_tokens,
                    "total_tokens": message.usage.input_tokens + message.usage.output_tokens
                },
                latency_ms=latency_ms,
                metadata={"stop_reason": message.stop_reason}
            )
            
        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            raise LLMException(f"Anthropic generation failed: {e}")
    
    def get_model_name(self) -> str:
        return self.model
