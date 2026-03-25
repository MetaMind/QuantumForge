import time
from typing import Any, Dict, Optional

from backend.core.config import settings
from backend.core.logger import get_logger
from backend.core.exceptions import LLMException
from backend.services.llm_providers.base import BaseLLMProvider, GenerationResult, ProviderType

logger = get_logger(__name__)


class LocalProvider(BaseLLMProvider):
    """Local model provider using llama-cpp-python or similar"""
    
    def __init__(self):
        self.model = None
        self.model_path = settings.local_model_path
        self.context_length = settings.local_context_length
        super().__init__(ProviderType.LOCAL, settings.local_priority)
    
    def _check_availability(self) -> None:
        if not self.model_path:
            logger.info("Local model path not configured")
            self.available = False
            return
        
        try:
            # Try to import llama_cpp
            from llama_cpp import Llama
            
            logger.info(f"Loading local model from {self.model_path}")
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=self.context_length,
                verbose=False
            )
            self.available = True
            logger.info("Local provider initialized")
        except ImportError:
            logger.warning("llama_cpp not installed, local provider unavailable")
            self.available = False
        except Exception as e:
            logger.warning(f"Local provider initialization failed: {e}")
            self.available = False
    
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> GenerationResult:
        if not self.model:
            raise LLMException("Local model not loaded")
        
        start_time = time.time()
        temp = temperature or 0.7
        tokens = max_tokens or 2000
        
        try:
            # Format prompt for instruction models
            full_prompt = f"{system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"
            
            output = self.model(
                prompt=full_prompt,
                max_tokens=tokens,
                temperature=temp,
                stop=["User:", "\n\n"],
                echo=False
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            return GenerationResult(
                content=output["choices"][0]["text"].strip(),
                provider=self.provider_type,
                model="local-llm",
                usage={
                    "prompt_tokens": output["usage"]["prompt_tokens"],
                    "completion_tokens": output["usage"]["completion_tokens"],
                    "total_tokens": output["usage"]["total_tokens"]
                },
                latency_ms=latency_ms,
                metadata={"local": True}
            )
            
        except Exception as e:
            logger.error(f"Local generation failed: {e}")
            raise LLMException(f"Local generation failed: {e}")
    
    def get_model_name(self) -> str:
        return "local-llm"
