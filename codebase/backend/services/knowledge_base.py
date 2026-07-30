import json
import os
from typing import Optional

KB_PATH = os.path.join(os.path.dirname(__file__), "..", "knowledge_base.json")

def load_knowledge_base() -> dict:
    with open(KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_all_documents() -> list:
    kb = load_knowledge_base()
    return kb.get("documents", [])

def search_documents(query: str) -> list[dict]:
    """Simple keyword search over the knowledge base."""
    query_lower = query.lower()
    docs = get_all_documents()
    results = []

    keywords = query_lower.split()
    for doc in docs:
        score = 0
        searchable = " ".join([
            doc.get("title", ""),
            doc.get("summary", ""),
            " ".join(doc.get("key_concepts", [])),
            " ".join(doc.get("key_takeaways", [])),
            doc.get("module", ""),
            doc.get("level", ""),
        ]).lower()

        for kw in keywords:
            if kw in searchable:
                score += 1

        if score > 0:
            results.append({"doc": doc, "score": score})

    results.sort(key=lambda x: x["score"], reverse=True)
    return [r["doc"] for r in results[:3]]

def format_kb_for_context(docs: list[dict]) -> str:
    """Format documents as context string for Gemini prompt."""
    if not docs:
        return "Không tìm thấy tài liệu liên quan trong Knowledge Base."
    
    lines = []
    for doc in docs:
        lines.append(f"--- TÀI LIỆU: {doc['title']} ---")
        lines.append(f"Module: {doc['module']} | Cấp độ: {doc['level']}")
        lines.append(f"Tóm tắt: {doc['summary']}")
        lines.append("Key Concepts: " + ", ".join(doc.get("key_concepts", [])))
        lines.append("Key Takeaways:")
        for t in doc.get("key_takeaways", []):
            lines.append(f"  • {t}")
        lines.append("Trích dẫn: " + ", ".join(doc.get("citations", [])))
        lines.append("")
    
    return "\n".join(lines)

def is_logistics_query(message: str) -> bool:
    """Detect if message is about logistics (deadline, score, etc.)."""
    logistics_keywords = [
        "deadline", "hạn nộp", "hạn chót", "nộp bài", "nộp lúc",
        "điểm số", "điểm thi", "kết quả", "chấm điểm",
        "lịch học", "lịch nghỉ", "ngày nghỉ", "nghỉ lễ",
        "học phí", "tiền", "hoàn tiền",
        "đăng ký", "enroll", "tên học viên", "danh sách",
        "contact", "liên hệ", "email mentor", "số điện thoại",
    ]
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in logistics_keywords)

def is_ambiguous_query(message: str) -> bool:
    """Detect if message is too vague."""
    too_short = len(message.strip().split()) <= 3
    vague_phrases = ["tài liệu về ai", "slide nào", "gì vậy", "cho biết", "nói về gì"]
    msg_lower = message.lower()
    return too_short or any(p in msg_lower for p in vague_phrases)
