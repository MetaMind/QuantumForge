import hashlib
import os
import pickle
from typing import Dict, List, Optional, Tuple

import numpy as np

from backend.core.config import settings
from backend.core.exceptions import MemoryException
from backend.core.logger import get_logger

logger = get_logger(__name__)


class SimpleEmbedding:
    """Simple bag-of-words embedding for testing without external models"""
    
    def __init__(self, dim: int = 384):
        self.dim = dim
        self.vocab: Dict[str, int] = {}
        self.next_idx = 0
    
    def _tokenize(self, text: str) -> List[str]:
        return text.lower().split()
    
    def _get_or_create_idx(self, token: str) -> int:
        if token not in self.vocab:
            self.vocab[token] = self.next_idx
            self.next_idx += 1
        return self.vocab[token]
    
    def embed(self, text: str) -> np.ndarray:
        tokens = self._tokenize(text)
        vector = np.zeros(self.dim)

        # Multi-hash strategy: each token contributes to multiple dimensions
        # using different hash seeds, reducing collision probability
        seeds = [0, 1, 2]
        for token in tokens:
            for seed in seeds:
                h = hashlib.md5(f"{seed}:{token}".encode()).digest()
                idx = int.from_bytes(h[:4], "little") % self.dim
                vector[idx] += 1.0 / len(seeds)

        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.astype(np.float32)


class VectorStore:
    def __init__(self, store_path: Optional[str] = None):
        self.store_path = store_path or settings.vector_store_path
        self.embedding_dim = settings.embedding_dim
        self.embedder = SimpleEmbedding(self.embedding_dim)
        
        self.vectors: np.ndarray = np.zeros((0, self.embedding_dim), dtype=np.float32)
        self.metadata: List[Dict] = []
        self.index_map: Dict[str, int] = {}
        
        os.makedirs(self.store_path, exist_ok=True)
        self._load()
    
    def add(self, text: str, metadata: Dict, entry_id: str) -> None:
        vector = self.embedder.embed(text)
        
        if entry_id in self.index_map:
            idx = self.index_map[entry_id]
            self.vectors[idx] = vector
            self.metadata[idx] = metadata
        else:
            idx = len(self.metadata)
            self.vectors = np.vstack([self.vectors, vector.reshape(1, -1)])
            self.metadata.append(metadata)
            self.index_map[entry_id] = idx
        
        self._save()
        logger.info(f"Added vector for entry {entry_id}")
    
    def search(self, query: str, k: int = 5) -> List[Tuple[Dict, float]]:
        if len(self.metadata) == 0:
            return []
        
        query_vector = self.embedder.embed(query).reshape(1, -1)
        
        # Cosine similarity
        similarities = np.dot(self.vectors, query_vector.T).flatten()
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        
        results = []
        for idx in top_k_indices:
            if similarities[idx] > 0:
                results.append((self.metadata[idx], float(similarities[idx])))
        
        return results
    
    def get(self, entry_id: str) -> Optional[Dict]:
        if entry_id not in self.index_map:
            return None
        idx = self.index_map[entry_id]
        return self.metadata[idx]
    
    def delete(self, entry_id: str) -> bool:
        if entry_id not in self.index_map:
            return False

        # Compact: rebuild store excluding the deleted entry
        new_vectors = []
        new_metadata = []
        new_index_map = {}

        for old_id, idx in self.index_map.items():
            if old_id == entry_id:
                continue
            meta = self.metadata[idx]
            if meta.get("_deleted"):
                continue
            new_idx = len(new_metadata)
            new_vectors.append(self.vectors[idx])
            new_metadata.append(meta)
            new_index_map[old_id] = new_idx

        self.vectors = np.array(new_vectors, dtype=np.float32).reshape(
            len(new_vectors), self.embedding_dim
        ) if new_vectors else np.zeros((0, self.embedding_dim), dtype=np.float32)
        self.metadata = new_metadata
        self.index_map = new_index_map

        self._save()
        return True
    
    def _save(self) -> None:
        try:
            data = {
                "vectors": self.vectors,
                "metadata": self.metadata,
                "index_map": self.index_map,
                "vocab": self.embedder.vocab,
                "next_idx": self.embedder.next_idx
            }
            store_file = os.path.join(self.store_path, "store.pkl")
            tmp_file = store_file + ".tmp"
            with open(tmp_file, "wb") as f:
                pickle.dump(data, f)
            os.replace(tmp_file, store_file)
        except Exception as e:
            raise MemoryException(f"Failed to save vector store: {e}")
    
    def _load(self) -> None:
        path = os.path.join(self.store_path, "store.pkl")
        if not os.path.exists(path):
            return
        
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            
            self.vectors = data["vectors"]
            self.metadata = data["metadata"]
            self.index_map = data["index_map"]
            self.embedder.vocab = data["vocab"]
            self.embedder.next_idx = data["next_idx"]
            
            logger.info(f"Loaded {len(self.metadata)} vectors from store")
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
    
    def clear(self) -> None:
        self.vectors = np.zeros((0, self.embedding_dim), dtype=np.float32)
        self.metadata = []
        self.index_map = {}
        self._save()
