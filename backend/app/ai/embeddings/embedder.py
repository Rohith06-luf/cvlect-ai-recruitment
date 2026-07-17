import math
from typing import List
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


class EmbeddingEngine:
    _model = None

    @classmethod
    def get_model(cls):
        if SentenceTransformer is None:
            return None
        if cls._model is None:
            cls._model = SentenceTransformer("all-MiniLM-L6-v2")
        return cls._model

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * 384
        
        model = self.get_model()
        if model is None:
            # Fallback bag-of-words logic if sentence-transformers is missing
            tokens = text.lower().split()
            return [float(len(tokens))] * 384

        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        
        model = self.get_model()
        if model is None:
            return [self.embed_text(t) for t in texts]

        embeddings = model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b:
            return 0.0
        
        a = np.array(vec_a)
        b = np.array(vec_b)
        
        # Match dimensions if they differ
        max_len = max(len(a), len(b))
        if len(a) < max_len:
            a = np.pad(a, (0, max_len - len(a)), 'constant')
        if len(b) < max_len:
            b = np.pad(b, (0, max_len - len(b)), 'constant')
            
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        return float(np.dot(a, b) / (norm_a * norm_b))
