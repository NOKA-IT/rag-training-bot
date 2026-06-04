"""ChromaDB embedded vector store integration."""
import os
from typing import List, Optional, Dict, Any

import chromadb

from ..config import settings
from . import embeddings

_client = None
_collection = None
COLLECTION_NAME = "documents"


def _get_collection():
    global _client, _collection
    if _collection is None:
        os.makedirs(settings.CHROMA_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def add_document_chunks(document_id: int,
                        chunks: List[str],
                        metadata: Dict[str, Any]) -> int:
    """Embed and store chunks for a document. Returns chunk count."""
    if not chunks:
        return 0
    collection = _get_collection()
    vectors = embeddings.embed_documents(chunks)

    ids = [f"doc{document_id}_chunk{i}" for i in range(len(chunks))]
    metadatas = []
    for i in range(len(chunks)):
        m = dict(metadata)
        m["document_id"] = document_id
        m["chunk_index"] = i
        metadatas.append(m)

    collection.add(ids=ids, embeddings=vectors, documents=chunks, metadatas=metadatas)
    return len(chunks)


def delete_document(document_id: int):
    """Remove all chunks belonging to a document."""
    collection = _get_collection()
    try:
        collection.delete(where={"document_id": document_id})
    except Exception:
        pass


def query(question: str,
          where: Optional[Dict[str, Any]] = None,
          k: int = None) -> List[Dict[str, Any]]:
    """Semantic search. Returns list of {document, metadata, distance}."""
    k = k or settings.RETRIEVAL_K
    collection = _get_collection()
    if collection.count() == 0:
        return []

    qvec = embeddings.embed_query(question)
    res = collection.query(
        query_embeddings=[qvec],
        n_results=k,
        where=where or None,
    )
    results = []
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]
    for doc, meta, dist in zip(docs, metas, dists):
        results.append({"document": doc, "metadata": meta, "distance": dist})
    return results
