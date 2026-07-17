import os
import pickle
from typing import Any, Dict, List, Tuple
import numpy as np

try:
    import faiss
except ImportError:
    faiss = None


class FAISSStore:
    def __init__(self) -> None:
        self.index_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "uploads", "faiss_index.bin"
        )
        self.metadata_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "uploads", "faiss_metadata.pkl"
        )
        
        self.dimension = 384  # Dimension of all-MiniLM-L6-v2 embeddings
        self.index = None
        self.metadata: List[Dict[str, Any]] = []
        
        self.load_index()

    def load_index(self) -> None:
        # Load FAISS index from disk
        if faiss is not None and os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
                if os.path.exists(self.metadata_path):
                    with open(self.metadata_path, "rb") as f:
                        self.metadata = pickle.load(f)
                return
            except Exception as e:
                print(f"Error loading FAISS index: {e}. Re-creating index...")

        # Initialize new index
        if faiss is not None:
            # IndexFlatIP calculates inner product. If vectors are normalized, Inner Product is Cosine Similarity.
            self.index = faiss.IndexFlatIP(self.dimension)
        else:
            self.index = None  # Fallback mode
            self.fallback_vectors: List[np.ndarray] = []

        self.metadata = []

    def save_index(self) -> None:
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        if faiss is not None and self.index is not None:
            try:
                faiss.write_index(self.index, self.index_path)
                with open(self.metadata_path, "wb") as f:
                    pickle.dump(self.metadata, f)
            except Exception as e:
                print(f"Error saving FAISS index to disk: {e}")

    def add(self, vector: List[float], metadata: Dict[str, Any]) -> None:
        # Ensure dimensions match
        if len(vector) != self.dimension:
            # Pad or truncate
            vector = vector[:self.dimension] + [0.0] * max(0, self.dimension - len(vector))

        # Normalize vector for cosine similarity
        arr = np.array([vector], dtype=np.float32)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        arr = arr / norms

        if faiss is not None and self.index is not None:
            self.index.add(arr)
            self.metadata.append(metadata)
            self.save_index()
        else:
            # Fallback memory storage
            if not hasattr(self, 'fallback_vectors'):
                self.fallback_vectors = []
            self.fallback_vectors.append(arr[0])
            self.metadata.append(metadata)

    def search(self, vector: List[float], top_k: int = 5) -> List[Tuple[float, Dict[str, Any]]]:
        if not self.metadata:
            return []

        # Pad/truncate query vector
        if len(vector) != self.dimension:
            vector = vector[:self.dimension] + [0.0] * max(0, self.dimension - len(vector))

        # Normalize search vector
        q = np.array([vector], dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm > 0:
            q = q / q_norm

        if faiss is not None and self.index is not None:
            try:
                # Search FAISS index
                scores, indices = self.index.search(q, min(top_k, len(self.metadata)))
                results = []
                for score, idx in zip(scores[0], indices[0]):
                    if idx != -1 and idx < len(self.metadata):
                        results.append((float(score), self.metadata[idx]))
                return results
            except Exception as e:
                print(f"FAISS search failed: {e}. Falling back to numpy search.")

        # Fallback numpy cosine similarity search
        if not hasattr(self, 'fallback_vectors') or not self.fallback_vectors:
            # Extract from metadata if index failed but we have data
            return []

        q_vec = q[0]
        similarities = []
        for idx, stored_vec in enumerate(self.fallback_vectors):
            sim = float(np.dot(stored_vec, q_vec))
            similarities.append((sim, self.metadata[idx]))
            
        similarities.sort(key=lambda x: x[0], reverse=True)
        return similarities[:top_k]
