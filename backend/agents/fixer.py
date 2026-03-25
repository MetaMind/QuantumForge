from typing import Any, Dict

from backend.agents.base import BaseAgent
from backend.core.logger import get_logger

logger = get_logger(__name__)


class FixerAgent(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("fixer", llm)
    
    def get_system_prompt(self) -> str:
        return """You are a debugging expert. Fix the provided Python code that failed to execute or produced incorrect results.

Rules:
1. Analyze the error carefully
2. Fix the root cause, not just symptoms
3. Preserve the original intent of the code
4. Output ONLY the fixed code, no explanations
5. Include comments explaining critical fixes if non-obvious
6. Ensure the fix handles similar edge cases

Output format: Just the corrected Python code."""
    
    def format_prompt(self, task_input: Dict[str, Any]) -> str:
        code = task_input.get("code", "")
        error = task_input.get("error", "")
        stderr = task_input.get("stderr", "")
        step = task_input.get("step", "")
        
        prompt = f"Task: {step}\n\n"
        prompt += f"Code with errors:\n```python\n{code}\n```\n"
        
        if error:
            prompt += f"\nError: {error}\n"
        if stderr:
            prompt += f"\nStderr: {stderr}\n"
        
        # Include context about what should work
        prompt += "\nProvide the corrected code that fixes all errors."
        
        return prompt
    
    def run(self, task_input: Dict[str, Any]) -> str:
        from backend.agents.executor import ExecutorAgent
        executor = ExecutorAgent(self.llm)
        
        output = super().run(task_input)
        return executor.extract_code(output.content)
