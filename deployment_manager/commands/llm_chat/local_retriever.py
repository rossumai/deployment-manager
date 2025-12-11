import json
import logging
import re
from pathlib import Path

import numpy as np

logging.getLogger("faiss").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

import faiss
from sentence_transformers import SentenceTransformer


class LocalDocsRetriever:
    """Semantic search retriever using local embeddings for Rossum API documentation."""

    MODEL_NAME = "all-MiniLM-L6-v2"  # Fast, 80MB, good quality

    def __init__(self, docs_path: Path = None, num_results: int = 4):
        if docs_path is None:
            docs_path = Path(__file__).parent / "api_docs" / "rossum_api_docs.md"

        self.num_results = num_results
        self.cache_dir = docs_path.parent
        self.index_path = self.cache_dir / "faiss_index.bin"
        self.chunks_path = self.cache_dir / "chunks.json"

        self.model = SentenceTransformer(self.MODEL_NAME)

        if self._cache_exists():
            self._load_from_cache()
        else:
            self.chunks = self._load_and_chunk(docs_path)
            self.index = self._build_index()
            self._save_to_cache()

    def _cache_exists(self) -> bool:
        return self.index_path.exists() and self.chunks_path.exists()

    def _load_from_cache(self):
        self.index = faiss.read_index(str(self.index_path))
        self.chunks = json.loads(self.chunks_path.read_text())

    def _save_to_cache(self):
        faiss.write_index(self.index, str(self.index_path))
        self.chunks_path.write_text(json.dumps(self.chunks))

    def _load_and_chunk(self, docs_path: Path) -> list[str]:
        content = docs_path.read_text()
        chunks = re.split(r"\n(?=#{1,4} )", content)
        return [c.strip() for c in chunks if len(c.strip()) > 100]

    def _build_index(self) -> faiss.IndexFlatIP:
        embeddings = self.model.encode(self.chunks, normalize_embeddings=True, show_progress_bar=True)
        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings.astype(np.float32))
        return index

    def invoke(self, query: str) -> str:
        query_embedding = self.model.encode([query], normalize_embeddings=True)
        scores, indices = self.index.search(query_embedding.astype(np.float32), self.num_results)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and scores[0][i] > 0.2:  # Minimum similarity threshold
                results.append(self.chunks[idx])

        return "\n\n---\n\n".join(results) if results else "No relevant documentation found."

    async def ainvoke(self, query: str) -> str:
        return self.invoke(query)
