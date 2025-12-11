import re
from pathlib import Path
from rank_bm25 import BM25Okapi
import numpy as np


class LocalDocsRetriever:
    """BM25-based local retriever for Rossum API documentation."""

    def __init__(self, docs_path: Path = None, num_results: int = 4):
        if docs_path is None:
            docs_path = Path(__file__).parent / "api_docs" / "rossum_api_docs.md"

        self.num_results = num_results
        self.chunks = self._load_and_chunk(docs_path)
        tokenized = [c.lower().split() for c in self.chunks]
        self.bm25 = BM25Okapi(tokenized)

    def _load_and_chunk(self, docs_path: Path) -> list[str]:
        content = docs_path.read_text()
        chunks = re.split(r"\n(?=#{1,4} )", content)
        return [c.strip() for c in chunks if len(c.strip()) > 100]

    def invoke(self, query: str) -> str:
        query_tokens = query.lower().split()
        scores = self.bm25.get_scores(query_tokens)
        top_indices = np.argsort(scores)[-self.num_results :][::-1]

        results = []
        for i in top_indices:
            if scores[i] > 0:
                results.append(self.chunks[i])

        return "\n\n---\n\n".join(results) if results else "No relevant documentation found."

    async def ainvoke(self, query: str) -> str:
        return self.invoke(query)
