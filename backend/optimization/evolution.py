import random
import re
from typing import Dict, List, Optional

from backend.core.config import settings
from backend.core.logger import get_logger
from backend.core.models import PromptGenome

logger = get_logger(__name__)


class PromptEvolution:
    def __init__(self):
        self.population_size = settings.evolution_population_size
        self.mutation_rate = settings.evolution_mutation_rate
        self.population: List[PromptGenome] = []
        self._initialize_population()
    
    def _initialize_population(self):
        """Initialize with diverse prompt strategies"""
        base_prompts = [
            PromptGenome(
                system_prompt="You are an expert Python programmer. Write clean, efficient code.",
                task_prompt_template="Task: {task}\nRequirements: {requirements}",
                score=0.5
            ),
            PromptGenome(
                system_prompt="You are a Python expert focused on correctness and edge cases.",
                task_prompt_template="Implement: {task}\nHandle errors for: {requirements}",
                score=0.5
            ),
            PromptGenome(
                system_prompt="You are a software engineer writing production Python code.",
                task_prompt_template="# Task\n{task}\n\n# Requirements\n{requirements}\n\n# Solution",
                score=0.5
            )
        ]
        self.population = base_prompts[:self.population_size]
    
    def get_best_genome(self) -> PromptGenome:
        """Select genome using tournament selection"""
        if not self.population:
            self._initialize_population()
        
        # Sort by score
        sorted_pop = sorted(self.population, key=lambda x: x.score, reverse=True)
        return sorted_pop[0]
    
    def evolve(self, task_performance: Dict[str, float]):
        """Evolve population based on performance"""
        # Update scores
        for genome in self.population:
            if genome.genome_id in task_performance:
                # Exponential moving average
                genome.score = 0.7 * genome.score + 0.3 * task_performance[genome.genome_id]
                genome.usage_count += 1
        
        # Sort by fitness
        self.population.sort(key=lambda x: x.score, reverse=True)
        
        # Elitism: keep top ~33% (minimum 2)
        elite_count = max(2, len(self.population) // 3)
        new_population = self.population[:elite_count]
        
        # Generate offspring
        while len(new_population) < self.population_size:
            parent = random.choice(self.population[:len(self.population)//2])
            offspring = self._mutate(parent)
            new_population.append(offspring)
        
        self.population = new_population
        logger.info(f"Evolved population, best score: {self.population[0].score:.2f}")
    
    def _mutate(self, parent: PromptGenome) -> PromptGenome:
        """Create mutated copy of parent"""
        system_prompt = parent.system_prompt
        task_template = parent.task_prompt_template
        
        if random.random() < self.mutation_rate:
            # Mutate system prompt
            mutations = [
                lambda s: s.replace("efficient", "optimized"),
                lambda s: s + " Include comprehensive error handling.",
                lambda s: s.replace("Python", "Python 3.11+"),
                lambda s: "Focus on readability. " + s,
                lambda s: s + " Use type hints and docstrings."
            ]
            system_prompt = random.choice(mutations)(system_prompt)
        
        if random.random() < self.mutation_rate:
            # Mutate task template
            templates = [
                "Task: {task}\nContext: {context}\nRequirements: {requirements}",
                "Implement solution for: {task}\nConsider: {context}\nMust: {requirements}",
                "# {task}\nContext: {context}\n## Requirements\n{requirements}\n## Code"
            ]
            task_template = random.choice(templates)
        
        return PromptGenome(
            system_prompt=system_prompt,
            task_prompt_template=task_template,
            score=parent.score * 0.9  # Slightly lower initial score
        )
    
    def format_task(
        self,
        genome: PromptGenome,
        task: str,
        context: str = "",
        requirements: str = ""
    ) -> str:
        """Format task using genome template"""
        return genome.task_prompt_template.format(
            task=task,
            context=context,
            requirements=requirements
        )
