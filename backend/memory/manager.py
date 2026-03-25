from typing import List, Optional

from backend.core.logger import get_logger
from backend.core.models import MemoryEntry
from backend.memory.vector_store import VectorStore

logger = get_logger(__name__)


class MemoryManager:
    def __init__(self):
        self.store = VectorStore()
    
    def store_solution(self, entry: MemoryEntry) -> None:
        """Store a successful solution"""
        text = f"{entry.task_description}\n{entry.code}\nResult: {entry.result.stdout}"
        
        metadata = {
            "entry_id": entry.entry_id,
            "task_description": entry.task_description,
            "code": entry.code,
            "score": entry.score,
            "success": entry.result.success,
            "tags": entry.tags,
            "timestamp": entry.timestamp.isoformat()
        }
        
        self.store.add(text, metadata, entry.entry_id)
        logger.info(f"Stored solution {entry.entry_id} with score {entry.score}")
    
    def retrieve_relevant(
        self,
        task_description: str,
        k: int = 3,
        min_score: float = 0.5
    ) -> List[MemoryEntry]:
        """Retrieve relevant past solutions"""
        results = self.store.search(task_description, k=k*2)  # Fetch more to filter
        
        entries = []
        for metadata, similarity in results:
            if similarity < min_score or metadata.get("_deleted"):
                continue
            
            # Reconstruct partial entry (without full ExecutionResult for speed)
            entry = MemoryEntry(
                entry_id=metadata["entry_id"],
                task_description=metadata["task_description"],
                code=metadata["code"],
                result=None,  # Lazy load if needed
                score=metadata["score"],
                tags=metadata["tags"]
            )
            entries.append(entry)
            
            if len(entries) >= k:
                break
        
        logger.info(f"Retrieved {len(entries)} relevant memories for task")
        return entries
    
    def get_successful_patterns(self, tag: str, limit: int = 5) -> List[str]:
        """Get code patterns from successful solutions with specific tags"""
        # Search by tag
        results = self.store.search(tag, k=limit*3)
        
        codes = []
        for metadata, _ in results:
            if tag in metadata.get("tags", []) and metadata.get("score", 0) > 0.7:
                codes.append(metadata["code"])
                if len(codes) >= limit:
                    break
        
        return codes
    
    def forget_failure(self, entry_id: str) -> bool:
        """Mark a failed solution to avoid repetition"""
        return self.store.delete(entry_id)
