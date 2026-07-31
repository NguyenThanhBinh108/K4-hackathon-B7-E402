"""
VinAI Knowledge Assistant — Vector Knowledge Base (opt-in)
Embedding chạy local (Chroma default ONNX MiniLM) — không gọi Gemini/Groq,
không tốn quota, không phụ thuộc rate-limit của LLM provider.
Bật bằng env KB_BACKEND=vector (mặc định vẫn dùng knowledge_base.py — JSON keyword search).
"""
import os
from typing import List, Dict

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_store")
COLLECTION_NAME = "vlearn_kb"

_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is not None:
        return _collection

    import chromadb
    from chromadb.utils import embedding_functions

    _client = chromadb.PersistentClient(path=CHROMA_PATH)
    ef = embedding_functions.DefaultEmbeddingFunction()
    _collection = _client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=ef)
    return _collection


def vector_search(query: str, top_k: int = 3) -> List[Dict]:
    """Tìm top_k chunk liên quan nhất bằng vector similarity (embedding local)."""
    collection = _get_collection()
    if collection.count() == 0:
        return []

    result = collection.query(query_texts=[query], n_results=min(top_k, collection.count()))
    items = []
    ids = result.get("ids", [[]])[0]
    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    for id_, doc, meta in zip(ids, docs, metas):
        items.append({
            "id": id_,
            "citation": meta.get("citation", ""),
            "source_label": meta.get("source_label", ""),
            "module": meta.get("module", ""),
            "source": meta.get("source", ""),
            "text": doc,
        })
    return items


def format_vector_context(results: List[Dict]) -> str:
    """Định dạng kết quả vector search thành context cho LLM prompt."""
    if not results:
        return "Không tìm thấy đoạn nội dung liên quan trong Knowledge Base (vector search)."

    parts = []
    for r in results:
        header = f"[{r['citation']}] {r['source_label']}" if r["citation"] else r["source_label"]
        parts.append(f"{header}\n{r['text']}")
    return "\n---\n".join(parts)
