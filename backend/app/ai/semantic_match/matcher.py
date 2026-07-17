from app.ai.embeddings.embedder import EmbeddingEngine


class SemanticMatcher:
    def __init__(self, embedder: EmbeddingEngine | None = None) -> None:
        self.embedder = embedder or EmbeddingEngine()

    def match(self, resume_text: str, job_description: str) -> float:
        resume_vec = self.embedder.embed_text(resume_text)
        job_vec = self.embedder.embed_text(job_description)
        return self.embedder.cosine_similarity(resume_vec, job_vec)
