import json
import logging
import sys
import os
from datetime import datetime
from typing import Any, Dict

from backend.core.config import settings

# Create logs directory
os.makedirs('logs', exist_ok=True)

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        
        # File handler
        file_handler = logging.FileHandler('logs/quantumforge.jsonl')
        
        if settings.log_format == "json":
            formatter = JSONFormatter()
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)
        else:
            simple_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(simple_formatter)
            file_handler.setFormatter(simple_formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger

def log_structured(logger: logging.Logger, level: str, message: str, **kwargs) -> None:
    extra = {"extra_data": kwargs}
    getattr(logger, level.lower())(message, extra=extra)
