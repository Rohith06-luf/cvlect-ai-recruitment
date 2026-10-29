"""
CVlect AI — Embedding & Vector Search Service
Provides lazy-loaded dense representations using Sentence-Transformers,
cosine similarity computation, FAISS indexing, and vector serialization.
"""

import pickle
from typing import Optional, Union, Tuple, Any
import numpy as np

from app.config import settings
from app.utils import get_logger

logger = get_logger(__name__)

_model: Optional[Any] = None
_model_attempted: bool = False


def get_embedding_model():
    """Lazily load SentenceTransformer model on first invocation."""
    global _model, _model_attempted
    if not _model_attempted:
        _model_attempted = True
        try:
            from sentence_transformers import SentenceTransformer
            # Try loading cached model first without network overhead
            try:
                _model = SentenceTransformer(settings.sentence_transformer_model, local_files_only=True)
                logger.info(f"Loaded SentenceTransformer '{settings.sentence_transformer_model}' from local cache.")
            except Exception:
                import socket
                try:
                    socket.create_connection(("huggingface.co", 443), timeout=1.5)
                    _model = SentenceTransformer(settings.sentence_transformer_model)
                    logger.info(f"Initialized SentenceTransformer '{settings.sentence_transformer_model}'")
                except Exception as net_err:
                    logger.warning(
                        f"SentenceTransformer '{settings.sentence_transformer_model}' is not cached and network is unreachable ({net_err}). "
                        "Operating in fallback semantic mode."
                    )
                    _model = None
        except Exception as e:
            logger.warning(
                f"SentenceTransformer '{settings.sentence_transformer_model}' failed to load ({e}). "
                "Embeddings will return None."
            )
            _model = None
    return _model


def generate_embedding(text: str) -> Optional[np.ndarray]:
    """Generate normalized 1D embedding for a single text snippet."""
    if not text or not text.strip():
        return None

    model = get_embedding_model()
    if model is None:
        return None

    try:
        emb = model.encode(text.strip(), convert_to_numpy=True, normalize_embeddings=True)
        return emb.astype(np.float32)
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return None


def generate_embeddings(texts: list[str]) -> Optional[np.ndarray]:
    """Generate normalized 2D embeddings (N, D) for a batch of strings."""
    if not texts:
        return None

    model = get_embedding_model()
    if model is None:
        return None

    try:
        embs = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embs.astype(np.float32)
    except Exception as e:
        logger.error(f"Failed to generate batch embeddings: {e}")
        return None


def cosine_similarity(
    emb1: Optional[np.ndarray],
    emb2: Optional[np.ndarray],
) -> float:
    """Compute cosine similarity between two vectors. Returns a float between -1.0 and 1.0."""
    if emb1 is None or emb2 is None:
        return 0.0

    try:
        vec1 = np.asarray(emb1, dtype=np.float32).flatten()
        vec2 = np.asarray(emb2, dtype=np.float32).flatten()

        if vec1.shape != vec2.shape:
            return 0.0

        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = np.dot(vec1, vec2) / (norm1 * norm2)
        return float(np.clip(similarity, -1.0, 1.0))
    except Exception as e:
        logger.error(f"Error computing cosine similarity: {e}")
        return 0.0


def embedding_to_bytes(embedding: Optional[np.ndarray]) -> Optional[bytes]:
    """Serialize numpy embedding array into bytes for database storage."""
    if embedding is None:
        return None
    try:
        return pickle.dumps(np.asarray(embedding, dtype=np.float32))
    except Exception as e:
        logger.error(f"Failed to serialize embedding to bytes: {e}")
        return None


def bytes_to_embedding(data: Optional[bytes]) -> Optional[np.ndarray]:
    """Deserialize database binary blob back into a numpy embedding array."""
    if not data:
        return None
    try:
        arr = pickle.loads(data)
        if isinstance(arr, np.ndarray):
            return arr.astype(np.float32)
        return None
    except Exception as e:
        logger.error(f"Failed to deserialize bytes into embedding: {e}")
        return None


# =============================================================================
# FAISS & Fallback Vector Search
# =============================================================================

class FallbackVectorIndex:
    """NumPy-based index used when faiss is not installed."""
    def __init__(self, embeddings: np.ndarray):
        self.embeddings = embeddings.astype(np.float32)
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.normed = self.embeddings / norms

    def search(self, query: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        q = query.reshape(1, -1).astype(np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm > 0:
            q = q / q_norm

        sims = np.dot(self.normed, q.T).flatten()
        top_k = min(k, len(sims))
        sorted_indices = np.argsort(-sims)[:top_k]
        sorted_scores = sims[sorted_indices]

        return np.array([sorted_scores]), np.array([sorted_indices])


def build_index(embeddings: np.ndarray) -> Any:
    """
    Build a vector search index using FAISS IndexFlatIP (Inner Product/Cosine).
    Falls back to FallbackVectorIndex if FAISS is unavailable.
    """
    if embeddings is None or len(embeddings) == 0:
        return None

    matrix = np.asarray(embeddings, dtype=np.float32)
    try:
        import faiss
        dim = matrix.shape[1]
        # Normalize each row for cosine similarity with IndexFlatIP
        faiss.normalize_L2(matrix)
        index = faiss.IndexFlatIP(dim)
        index.add(matrix)
        return index
    except ImportError:
        logger.info("FAISS not installed; using FallbackVectorIndex.")
        return FallbackVectorIndex(matrix)
    except Exception as e:
        logger.warning(f"FAISS index creation failed ({e}); falling back to NumPy.")
        return FallbackVectorIndex(matrix)


def search_index(
    index: Any,
    query_embedding: np.ndarray,
    k: int = 5,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Query the index.
    Returns: (distances/similarities, indices)
    """
    if index is None or query_embedding is None:
        return np.array([[]]), np.array([[]])

    q = np.asarray(query_embedding, dtype=np.float32).reshape(1, -1)

    try:
        # Check if FAISS index
        if hasattr(index, "search"):
            import sys
            if "faiss" in sys.modules and not isinstance(index, FallbackVectorIndex):
                import faiss
                faiss.normalize_L2(q)
            return index.search(q, k)
        else:
            return np.array([[]]), np.array([[]])
    except Exception as e:
        logger.error(f"Error querying vector index: {e}")
        return np.array([[]]), np.array([[]])
