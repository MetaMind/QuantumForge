import time
from typing import Any, Dict, Optional

import openai
from openai import OpenAI

from backend.core.config import settings
from backend.core.logger import get_logger
from backend.core.exceptions import LLMException
from backend.services.llm_providers.base import BaseLLMProvider, GenerationResult, ProviderType

logger = get_logger(__name__)


class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        self.client: Optional[OpenAI] = None
        self.model = settings.openai_model
        self.timeout = settings.openai_timeout
        self.max_tokens = settings.openai_max_tokens
        self.temperature = settings.openai_temperature
        super().__init__(ProviderType.OPENAI, settings.openai_priority)
    
    def _check_availability(self) -> None:
        if settings.openai_api_key:
            try:
                self.client = OpenAI(
                    api_key=settings.openai_api_key,
                    base_url=settings.openai_base_url,
                    timeout=self.timeout
                )
                # Test connection
                self.client.models.list()
                self.available = True
                logger.info(f"OpenAI provider initialized with model {self.model}")
            except Exception as e:
                logger.warning(f"OpenAI provider unavailable: {e}")
                self.available = False
        else:
            logger.info("OpenAI API key not configured")
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
            raise LLMException("OpenAI client not initialized")
        
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
                metadata={"finish_reason": response.choices[0].finish_reason}
            )
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise LLMException(f"OpenAI generation failed: {e}")
    
    def get_model_name(self) -> str:
        return self.model
