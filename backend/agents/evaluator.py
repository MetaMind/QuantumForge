import re
from typing import Any, Dict

from backend.agents.base import BaseAgent
from backend.core.logger import get_logger
from backend.core.models import ExecutionResult

logger = get_logger(__name__)


class EvaluatorAgent(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("evaluator", llm)
        self.weights = {
            "execution_success": 0.4,
            "correctness": 0.3,
            "code_quality": 0.2,
            "efficiency": 0.1
        }
    
    def get_system_prompt(self) -> str:
        return """You are a code evaluation expert. Score the provided code based on multiple criteria.

Provide scores in this exact format:
SUCCESS: <true|false>
CORRECTNESS: <0.0-1.0>
QUALITY: <0.0-1.0>
EFFICIENCY: <0.0-1.0>
FEEDBACK: <brief explanation>

Scoring guide:
- SUCCESS: Did it execute without errors?
- CORRECTNESS: Does it solve the stated problem?
- QUALITY: Code clarity, error handling, type hints
- EFFICIENCY: Algorithmic complexity and performance"""
    
    def format_prompt(self, task_input: Dict[str, Any]) -> str:
        step = task_input.get("step", "")
        code = task_input.get("code", "")
        result = task_input.get("result", {})
        
        prompt = f"Task: {step}\n\n"
        prompt += f"Code:\n```python\n{code}\n```\n\n"
        
        if isinstance(result, ExecutionResult):
            prompt += f"Execution stdout: {result.stdout}\n"
            prompt += f"Execution stderr: {result.stderr}\n"
            prompt += f"Exit code: {result.exit_code}\n"
            prompt += f"Execution time: {result.execution_time:.2f}s\n"
        else:
            prompt += f"Result: {result}\n"
        
        return prompt
    
    def parse_scores(self, content: str) -> Dict[str, float]:
        """Parse evaluation scores from LLM output"""
        scores = {
            "success": 0.0,
            "correctness": 0.0,
            "quality": 0.0,
            "efficiency": 0.0,
            "feedback": ""
        }
        
        patterns = {
            "success": r"SUCCESS:\s*(true|false|True|False)",
            "correctness": r"CORRECTNESS:\s*([0-9.]+)",
            "quality": r"QUALITY:\s*([0-9.]+)",
            "efficiency": r"EFFICIENCY:\s*([0-9.]+)",
            "feedback": r"FEEDBACK:\s*(.+?)(?=\n|$)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if key == "success":
                    scores[key] = 1.0 if value.lower() == "true" else 0.0
                elif key == "feedback":
                    scores[key] = value
                else:
                    scores[key] = float(value)
        
        return scores
    
    def calculate_final_score(
        self,
        execution_result: ExecutionResult,
        llm_scores: Dict[str, float]
    ) -> float:
        """Calculate weighted final score"""
        if not execution_result.success:
            return max(0.0, llm_scores.get("correctness", 0) * 0.3)
        
        score = (
            self.weights["execution_success"] * (1.0 if execution_result.success else 0.0) +
            self.weights["correctness"] * llm_scores.get("correctness", 0.5) +
            self.weights["code_quality"] * llm_scores.get("quality", 0.5) +
            self.weights["efficiency"] * llm_scores.get("efficiency", 0.5)
        )
        
        # Penalize long execution times
        if execution_result.execution_time > 10:
            score *= 0.9
        
        return min(1.0, max(0.0, score))
    
    def run(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        output = super().run(task_input)
        scores = self.parse_scores(output.content)
        
        result = task_input.get("result")
        if isinstance(result, ExecutionResult):
            final_score = self.calculate_final_score(result, scores)
        else:
            final_score = sum([
                scores.get("correctness", 0) * 0.4,
                scores.get("quality", 0) * 0.3,
                scores.get("efficiency", 0) * 0.3
            ])
        
        return {
            "scores": scores,
            "final_score": final_score,
            "raw_output": output.content
        }
