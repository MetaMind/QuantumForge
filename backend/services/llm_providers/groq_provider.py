import time
from typing import Any, Dict, Optional

import groq
from groq import Groq

from backend.core.config import settings
from backend.core.logger import get_logger
from backend.core.exceptions import LLMException
from backend.services.llm_providers.base import BaseLLMProvider, GenerationResult, ProviderType

logger = get_logger(__name__)


class GroqProvider(BaseLLMProvider):
    """Groq provider with ultra-fast inference"""
    
    def __init__(self):
        self.client: Optional[Groq] = None
        self.model = settings.groq_model
        self.timeout = settings.groq_timeout
        self.max_tokens = settings.groq_max_tokens
        self.temperature = settings.groq_temperature
        super().__init__(ProviderType.GROQ, settings.groq_priority)
    
    def _check_availability(self) -> None:
        if settings.groq_api_key:
            try:
                self.client = Groq(
                    api_key=settings.groq_api_key,
                    timeout=self.timeout
                )
                self.available = True
                logger.info(f"Groq provider initialized with model {self.model}")
            except Exception as e:
                logger.warning(f"Groq provider unavailable: {e}")
                self.available = False
        else:
            logger.info("Groq API key not configured")
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
            raise LLMException("Groq client not initialized")
        
        start_time = time.time()
        temp = temperature or self.temperature
        tokens = max_tokens or self.max_tokens
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temp,
                max_tokens=tokens,
                **kwargs
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            return GenerationResult(
                content=response.choices[0].message.content,
                provider=self.provider_type,
                model=self.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                latency_ms=latency_ms,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "speed": "ultra-fast"
                }
            )
            
        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            raise LLMException(f"Groq generation failed: {e}")
    
    def get_model_name(self) -> str:
        return self.model
