from typing import Dict, List, Optional

from backend.core.logger import get_logger
from backend.core.models import ExecutionResult

logger = get_logger(__name__)


class ScoringEngine:
    def __init__(self):
        self.weights = {
            "functional": 0.5,
            "performance": 0.2,
            "robustness": 0.2,
            "style": 0.1
        }
    
    def score_execution(
        self,
        result: ExecutionResult,
        expected_output: Optional[str] = None
    ) -> Dict[str, float]:
        """Score an execution result"""
        scores = {
            "functional": 0.0,
            "performance": 0.0,
            "robustness": 0.0,
            "style": 0.0,
            "total": 0.0
        }
        
        # Functional score
        if result.success:
            scores["functional"] = 1.0
            if expected_output and expected_output in result.stdout:
                scores["functional"] = 1.0
            elif expected_output:
                scores["functional"] = 0.5
        
        # Performance score (based on execution time)
        if result.execution_time < 1.0:
            scores["performance"] = 1.0
        elif result.execution_time < 5.0:
            scores["performance"] = 0.7
        elif result.execution_time < 10.0:
            scores["performance"] = 0.4
        else:
            scores["performance"] = 0.2
        
        # Robustness score (absence of stderr warnings)
        if not result.stderr:
            scores["robustness"] = 1.0
        elif "warning" in result.stderr.lower():
            scores["robustness"] = 0.6
        else:
            scores["robustness"] = 0.3
        
        # Style score (code analysis)
        scores["style"] = self._analyze_code_style(result.artifacts.get("code", ""))
        
        # Calculate total
        scores["total"] = sum(
            scores[k] * self.weights[k] for k in self.weights.keys()
        )
        
        return scores
    
    def _analyze_code_style(self, code: str) -> float:
        """Basic code style analysis"""
        if not code:
            return 0.5
        
        score = 0.5
        lines = code.split('\n')
        
        # Check for docstrings
        if '"""' in code or "'''" in code:
            score += 0.2
        
        # Check for type hints
        if '-> ' in code or ': ' in code:
            score += 0.15
        
        # Check for proper naming (snake_case)
        import re
        snake_case = len(re.findall(r'def [a-z_][a-z0-9_]*\(', code))
        camel_case = len(re.findall(r'def [A-Z][a-zA-Z]*\(', code))
        if snake_case > camel_case:
            score += 0.15
        
        return min(1.0, score)
    
    def select_best_candidate(
        self,
        candidates: List[Dict]
    ) -> Optional[Dict]:
        """Select best candidate from parallel executions"""
        if not candidates:
            return None
        
        # Sort by score descending
        sorted_candidates = sorted(
            candidates,
            key=lambda x: x.get("score", 0),
            reverse=True
        )
        
        return sorted_candidates[0]
