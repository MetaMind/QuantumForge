import re
from typing import Any, Dict

from backend.agents.base import BaseAgent
from backend.core.logger import get_logger

logger = get_logger(__name__)


class ExecutorAgent(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("executor", llm)
    
    def get_system_prompt(self) -> str:
        return """You are an expert Python programmer. Your task is to write clean, efficient, and correct Python code.

Rules:
1. Write complete, runnable Python code
2. Include necessary imports
3. Handle edge cases and errors
4. Use type hints where appropriate
5. Output ONLY the code, no markdown, no explanations
6. If the task involves a function, include a test call at the end
7. Do not use input() - use predefined values or arguments

Example output format:
import math

def calculate_area(radius: float) -> float:
    return math.pi * radius ** 2

print(calculate_area(5.0))"""
    
    def format_prompt(self, task_input: Dict[str, Any]) -> str:
        step = task_input.get("step", "")
        previous_attempts = task_input.get("previous_attempts", [])
        context = task_input.get("context", "")
        
        prompt = f"Write Python code for: {step}\n"
        
        if context:
            prompt += f"Context: {context}\n"
        
        if previous_attempts:
            prompt += "\nPrevious attempts failed:\n"
            for i, attempt in enumerate(previous_attempts[-2:], 1):
                prompt += f"Attempt {i}:\n{attempt.get('code', '')}\n"
                prompt += f"Error: {attempt.get('error', 'Unknown')}\n"
        
        # Include successful patterns
        patterns = task_input.get("patterns", [])
        if patterns:
            prompt += "\nSimilar successful solutions:\n"
            for pattern in patterns[:2]:
                prompt += f"```python\n{pattern}\n```\n"
        
        return prompt
    
    def extract_code(self, content: str) -> str:
        """Extract code from markdown or raw text"""
        # Try to extract from markdown code blocks
        patterns = [
            r"```python\n(.*?)```",
            r"```\n(.*?)```",
            r"```(.*?)```"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                return matches[-1].strip()
        
        # If no code blocks, assume entire content is code
        # But filter out obvious non-code lines
        lines = content.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            if line.strip().startswith(('import ', 'from ', 'def ', 'class ', 'print(', '#', '"""', "'''")):
                in_code = True
            
            if in_code:
                code_lines.append(line)
        
        return '\n'.join(code_lines) if code_lines else content.strip()
    
    def run(self, task_input: Dict[str, Any]) -> str:
        output = super().run(task_input)
        code = self.extract_code(output.content)
        return code
