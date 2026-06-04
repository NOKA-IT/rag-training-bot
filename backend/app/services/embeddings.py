"""Gemini embedding wrapper used by the vector store."""
from typing import List

import google.generativeai as genai

from ..config import settings

_configured = False


def _ensure_configured():
    global _configured
    if not _configured:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Configure it in the environment."
            )
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _configured = True


def embed_documents(texts: List[str]) -> List[List[float]]:
    """Embed a list of document chunks."""
    _ensure_configured()
    vectors = []
    for t in texts:
        res = genai.embed_content(
            model=settings.GEMINI_EMBEDDING_MODEL,
            content=t,
            task_type="retrieval_document",
        )
        vectors.append(res["embedding"])
    return vectors


def embed_query(text: str) -> List[float]:
    """Embed a single search query."""
    _ensure_configured()
    res = genai.embed_content(
        model=settings.GEMINI_EMBEDDING_MODEL,
        content=text,
        task_type="retrieval_query",
    )
    return res["embedding"]
