import json
from typing import Any, Dict, List

from backend.agents.base import BaseAgent
from backend.core.logger import get_logger

logger = get_logger(__name__)


class PlannerAgent(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("planner", llm)
    
    def get_system_prompt(self) -> str:
        return """You are a task decomposition expert. Your role is to break down complex programming tasks into clear, actionable steps.

Rules:
1. Analyze the task carefully
2. Break it down into 2-5 concrete steps
3. Each step should be specific and verifiable
4. Output must be valid JSON with format:
   {
     "steps": [
       {"id": "step_1", "description": "...", "verification": "..."},
       ...
     ],
     "estimated_complexity": "low|medium|high"
   }
5. Do not include explanations outside the JSON"""
    
    def format_prompt(self, task_input: Dict[str, Any]) -> str:
        task = task_input.get("task", "")
        context = task_input.get("context", "")
        
        prompt = f"Task: {task}\n"
        if context:
            prompt += f"Context: {context}\n"
        
        # Include relevant memories if available
        memories = task_input.get("memories", [])
        if memories:
            prompt += "\nRelevant past solutions:\n"
            for i, mem in enumerate(memories[:3], 1):
                prompt += f"{i}. {mem.task_description} (score: {mem.score})\n"
        
        return prompt
    
    def run(self, task_input: Dict[str, Any]) -> List[Dict[str, str]]:
        output = super().run(task_input)
        
        try:
            # Extract JSON from response
            content = output.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            plan = json.loads(content.strip())
            steps = plan.get("steps", [])
            
            logger.info(f"Generated plan with {len(steps)} steps")
            return steps
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse plan JSON: {e}")
            # Fallback to single step
            return [{
                "id": "step_1",
                "description": task_input.get("task", ""),
                "verification": "Code executes without errors"
            }]
