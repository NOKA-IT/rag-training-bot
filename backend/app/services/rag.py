"""RAG pipeline: build access-aware filters, retrieve context, generate answer."""
from typing import List, Optional, Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from ..config import settings
from ..models import User, Role
from . import vector_store

SYSTEM_PROMPT = (
    "You are a helpful internal training assistant for company employees. "
    "Answer the question using ONLY the provided context from company documents. "
    "If the context does not contain the answer, say you don't have enough "
    "information in the available documents. Be concise, accurate and cite the "
    "document names you used."
)


def _build_where(user: User,
                 department_id: Optional[int]) -> Optional[Dict[str, Any]]:
    """Construct a ChromaDB access-control filter based on the user's role."""
    # Admin sees everything; optionally narrow by requested department.
    if user.role == Role.ADMIN:
        if department_id is not None:
            return {"$or": [
                {"visibility": "general"},
                {"department_id": department_id},
            ]}
        return None

    # Non-admin: general company docs OR their own department's docs.
    allowed = [{"visibility": "general"}]
    if user.department_id is not None:
        allowed.append({"department_id": user.department_id})
    if len(allowed) == 1:
        return allowed[0]
    return {"$or": allowed}


def _llm():
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_CHAT_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.2,
    )


def answer_question(user: User,
                    question: str,
                    department_id: Optional[int] = None,
                    category_ids: Optional[List[int]] = None) -> Dict[str, Any]:
    where = _build_where(user, department_id)
    # retrieve extra results so we can post-filter by category if needed
    hits = vector_store.query(question, where=where, k=settings.RETRIEVAL_K * 2)

    # Optional category post-filtering (category ids stored as csv string)
    if category_ids:
        wanted = set(str(c) for c in category_ids)
        filtered = []
        for h in hits:
            cats = str(h["metadata"].get("category_ids", "")).split(",")
            if wanted & set(c for c in cats if c):
                filtered.append(h)
        hits = filtered

    hits = hits[: settings.RETRIEVAL_K]

    if not hits:
        return {
            "answer": "I couldn't find any relevant information in the documents "
                      "available to you.",
            "sources": [],
        }

    context_parts = []
    sources = []
    seen_docs = set()
    for h in hits:
        meta = h["metadata"]
        fname = meta.get("filename", "document")
        context_parts.append(f"[Source: {fname}]\n{h['document']}")
        doc_id = meta.get("document_id")
        if doc_id not in seen_docs:
            seen_docs.add(doc_id)
            sources.append({
                "document_id": doc_id,
                "filename": fname,
                "snippet": h["document"][:200],
            })

    context = "\n\n---\n\n".join(context_parts)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Context:\n{context}\n\nQuestion: {question}"),
    ]
    llm = _llm()
    response = llm.invoke(messages)
    answer = response.content if hasattr(response, "content") else str(response)

    return {"answer": answer, "sources": sources}
