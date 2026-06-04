"""Gemini embedding wrapper used by the vector store.

Notes on model names (important):
- The ``google-generativeai`` SDK's ``embed_content`` requires the model name to
  be fully qualified, i.e. it MUST start with ``models/`` (or ``tunedModels/``).
  Passing a bare name like ``gemini-embedding-001`` raises:
      ValueError: Invalid model name: 'gemini-embedding-001'.
      Model names should start with 'models/' or 'tunedModels/'.
  Therefore every model name is normalized to include the ``models/`` prefix
  before being handed to the SDK.
- The legacy embedding models ``text-embedding-004`` and ``embedding-001`` were
  retired from the Gemini API and now return a ``404 ... is not found`` error.
  The current generally-available text embedding model is
  ``gemini-embedding-001`` (used as ``models/gemini-embedding-001``).
- If the configured model is unavailable, this module automatically falls back
  to the first model reported by ``list_models()`` that supports
  ``embedContent``. The resolved model name is cached.
"""
from typing import List, Optional
import logging

import google.generativeai as genai

from ..config import settings

logger = logging.getLogger(__name__)

_configured = False
# The fully-qualified model name actually used for requests, resolved lazily.
_resolved_model: Optional[str] = None

# Preferred fallbacks (in order), fully qualified, if the configured model is
# unavailable for this API key.
_FALLBACK_MODELS = [
    "models/gemini-embedding-001",
    "models/text-embedding-005",
    "models/text-embedding-004",
    "models/embedding-001",
]


def _qualify(name: str) -> str:
    """Ensure the model name carries the required ``models/`` prefix.

    The SDK accepts ``models/...`` and ``tunedModels/...``. Anything else
    (including a bare model id) is prefixed with ``models/``.
    """
    if not name:
        return name
    name = name.strip()
    if name.startswith("models/") or name.startswith("tunedModels/"):
        return name
    return f"models/{name}"


def _ensure_configured():
    global _configured
    if not _configured:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Configure it in the environment."
            )
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _configured = True


def _list_embedding_models() -> List[str]:
    """Return fully-qualified names of models that support embedContent.

    ``genai.list_models()`` already returns names with the ``models/`` prefix,
    but we normalize defensively.
    """
    names = []
    try:
        for m in genai.list_models():
            methods = getattr(m, "supported_generation_methods", []) or []
            if "embedContent" in methods:
                names.append(_qualify(m.name))
    except Exception as e:  # noqa: BLE001
        logger.warning("Could not list Gemini models: %s", e)
    return names


def _resolve_model() -> str:
    """Resolve a usable, fully-qualified embedding model, caching the result.

    Tries the configured model first; if it isn't among the models that
    support embedContent, falls back to a known-good model, and finally to
    whatever the API reports as available.
    """
    global _resolved_model
    if _resolved_model:
        return _resolved_model

    _ensure_configured()
    configured = _qualify(settings.GEMINI_EMBEDDING_MODEL)
    available = _list_embedding_models()

    # If we couldn't list models (e.g. transient error), trust the config.
    if not available:
        _resolved_model = configured
        return _resolved_model

    if configured in available:
        _resolved_model = configured
    else:
        chosen = next((m for m in _FALLBACK_MODELS if m in available), None)
        chosen = chosen or available[0]
        logger.warning(
            "Configured embedding model '%s' is not available; "
            "falling back to '%s'. Available: %s",
            configured, chosen, available,
        )
        _resolved_model = chosen
    return _resolved_model


def _embed(content: str, task_type: str) -> List[float]:
    """Call embed_content with the resolved model and a 404 self-heal retry."""
    global _resolved_model
    model = _resolve_model()
    try:
        res = genai.embed_content(model=model, content=content, task_type=task_type)
    except Exception as e:  # noqa: BLE001
        # If the cached model 404s at request time, re-resolve once and retry.
        if "404" in str(e) or "not found" in str(e).lower():
            logger.warning("Embedding model '%s' failed (%s); re-resolving.", model, e)
            _resolved_model = None
            new_model = _resolve_model()
            if new_model != model:
                res = genai.embed_content(
                    model=new_model, content=content, task_type=task_type
                )
            else:
                raise
        else:
            raise
    return res["embedding"]


def embed_documents(texts: List[str]) -> List[List[float]]:
    """Embed a list of document chunks."""
    _ensure_configured()
    return [_embed(t, "retrieval_document") for t in texts]


def embed_query(text: str) -> List[float]:
    """Embed a single search query."""
    _ensure_configured()
    return _embed(text, "retrieval_query")
