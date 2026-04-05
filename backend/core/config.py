import os
import json
from typing import List, Optional, Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )
    
    app_name: str = "QuantumForge AI"
    debug: bool = False
    
    # Store as string initially, parse in validator
    _llm_providers_str: Optional[str] = None
    
    @property
    def llm_providers(self) -> List[str]:
        """Parse LLM_PROVIDERS from env string"""
        raw = os.getenv("LLM_PROVIDERS", "")
        if not raw or raw.strip() == "":
            return ["openai", "groq", "fallback"]
        
        # Try JSON first
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except json.JSONDecodeError:
            pass
        
        # Fall back to comma-separated
        return [item.strip() for item in raw.split(",") if item.strip()]
    
    llm_routing_strategy: str = "priority"
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4"
    openai_timeout: int = 60
    openai_max_tokens: int = 2000
    openai_temperature: float = 0.7
    openai_priority: int = 1
    
    # Groq Configuration
    groq_api_key: Optional[str] = None
    groq_model: str = "moonshotai/kimi-k2-instruct-0905"
    groq_timeout: int = 30
    groq_max_tokens: int = 2000
    groq_temperature: float = 0.7
    groq_priority: int = 2
    
    # Anthropic Configuration
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-opus-20240229"
    anthropic_timeout: int = 60
    anthropic_max_tokens: int = 2000
    anthropic_temperature: float = 0.7
    anthropic_priority: int = 3
    
    # Local Model Configuration
    local_model_path: Optional[str] = None
    local_model_type: str = "llama_cpp"
    local_context_length: int = 4096
    local_priority: int = 99
    
    # Fallback Configuration
    enable_fallback_mock: bool = True
    
    # Global LLM Defaults
    default_temperature: float = 0.7
    default_max_tokens: int = 2000
    default_timeout: int = 60
    max_retries_per_provider: int = 2
    
    # Memory Configuration
    vector_store_path: str = "./data/vector_store"
    embedding_dim: int = 384
    max_memory_items: int = 1000
    
    # Sandbox Configuration
    sandbox_timeout: int = 30
    sandbox_max_memory_mb: int = 512
    
    # Distributed Configuration
    ray_address: Optional[str] = None
    max_parallel_workers: int = 4
    
    # Evolution Configuration
    evolution_population_size: int = 5
    evolution_mutation_rate: float = 0.3
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # CORS
    cors_origins: List[str] = Field(default=["*"])


def get_settings() -> Settings:
    # Note: not cached — env var changes take effect on next call.
    # Restart the server to pick up changes in production.
    return Settings()


settings = get_settings()
