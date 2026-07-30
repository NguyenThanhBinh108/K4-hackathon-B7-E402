"""
VinAI Knowledge Assistant — Knowledge Base Service
Keyword search + Intent routing (logistics / ambiguous / injection / RAG)
"""
import json
import os
import re
from typing import List, Dict

# ── Load KB ───────────────────────────────────────────────────────────
KB_PATH = os.path.join(os.path.dirname(__file__), "..", "knowledge_base.json")

def _load_kb() -> List[Dict]:
    try:
        with open(KB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("documents", [])
    except Exception:
        return []

def get_all_documents() -> List[Dict]:
    return _load_kb()

# ── Intent Detection ──────────────────────────────────────────────────

# Layer ③: Logistics — NEVER answer, block before Gemini
LOGISTICS_KEYWORDS = [
    "deadline", "hạn nộp", "nộp bài", "lịch học", "thời khóa biểu",
    "học phí", "tiền", "điểm số", "điểm của tôi", "điểm của mình",
    "bao nhiêu điểm", "học bổng", "chứng chỉ", "certificate",
    "lịch thi", "giờ học", "buổi học mấy giờ", "bắt đầu lúc",
    "kết thúc lúc", "khi nào", "bao giờ nộp", "submit",
    "thông tin cá nhân", "số điện thoại", "email của",
    "account", "tài khoản của", "mật khẩu"
]

# Layer ②: Ambiguous — hỏi lại thay vì đoán
VAGUE_PHRASES = [
    "tài liệu", "slide", "thông tin", "nội dung",
    "kiến thức", "bài giảng", "học về", "về ai"
]

# Layer ③: Prompt injection patterns
INJECTION_PATTERNS = [
    r"ignore (all |previous |prior |above )?(instructions?|prompts?|rules?|guidelines?)",
    r"forget (everything|all|your|the) (instructions?|rules?|context)",
    r"you are now",
    r"pretend (you are|to be|that)",
    r"act as (if )?you('re| are) (a |an )?",
    r"roleplay as",
    r"jailbreak",
    r"DAN mode",
    r"developer mode",
    r"system prompt",
    r"reveal (your|the) (prompt|instructions?|system)",
]

def is_logistics_query(text: str) -> bool:
    """Layer ③: Block logistics queries before they reach Gemini."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in LOGISTICS_KEYWORDS)

def is_injection_attempt(text: str) -> bool:
    """Layer ③: Detect prompt injection attempts."""
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in INJECTION_PATTERNS)

def is_ambiguous_query(text: str) -> bool:
    """Layer ②: Detect queries that are too vague to answer meaningfully."""
    text = text.strip()
    words = text.split()

    # Short query (≤3 words)
    if len(words) <= 2:
        return True

    # Vague single-word topic with no specifics
    if len(words) == 3:
        text_lower = text.lower()
        if any(vague in text_lower for vague in VAGUE_PHRASES):
            return True

    return False

def has_logistics_component(text: str) -> bool:
    """Check if query contains ANY logistics component (for split handling)."""
    return is_logistics_query(text)

# ── Keyword Search ────────────────────────────────────────────────────

def search_documents(query: str, top_k: int = 3) -> List[Dict]:
    """
    Keyword-based search across KB documents.
    Returns top_k most relevant documents.
    Mock semantic search: scores by keyword overlap.
    """
    docs = _load_kb()
    query_words = set(re.sub(r'[^\w\s]', '', query.lower()).split())

    if not query_words:
        return docs[:top_k]

    scored = []
    for doc in docs:
        score = 0

        # Match against key_concepts (highest weight)
        concepts_text = " ".join(doc.get("key_concepts", [])).lower()
        for word in query_words:
            if word in concepts_text:
                score += 3

        # Match against title
        title_text = doc.get("title", "").lower()
        for word in query_words:
            if word in title_text:
                score += 2

        # Match against summary
        summary_text = doc.get("summary", "").lower()
        for word in query_words:
            if word in summary_text:
                score += 1

        # Match against key_takeaways
        takeaways_text = " ".join(doc.get("key_takeaways", [])).lower()
        for word in query_words:
            if word in takeaways_text:
                score += 1

        if score > 0:
            scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scored[:top_k]]


def format_kb_for_context(docs: List[Dict]) -> str:
    """Format retrieved documents into LLM-readable context."""
    if not docs:
        return "Không tìm thấy tài liệu liên quan trong Knowledge Base."

    parts = []
    for doc in docs:
        section = f"[{doc['id']}] {doc['title']} ({doc['module']})\n"
        section += f"Tóm tắt: {doc.get('summary', '')}\n"

        takeaways = doc.get("key_takeaways", [])
        if takeaways:
            section += "Key takeaways (đã có citation):\n"
            for t in takeaways:
                section += f"  - {t}\n"

        citations = doc.get("citations", [])
        if citations:
            section += f"Citations có sẵn: {', '.join(citations)}\n"

        parts.append(section)

    return "\n---\n".join(parts)


def format_out_of_scope_response(reason: str = "logistics") -> dict:
    """Standard out-of-scope response (G1 — làm rõ scope)."""
    if reason == "injection":
        return {
            "response": "Mình chỉ trả lời về tài liệu và kiến thức AI/ML trong khoá học.\n\n(Đây là giới hạn thiết kế — không phải lỗi hệ thống.)",
            "citations": [],
            "found_in_kb": False,
            "is_out_of_scope": True,
            "suggested_docs": []
        }
    return {
        "response": "⚠️ Câu hỏi này nằm ngoài phạm vi của mình.\n\nCâu hỏi về **deadline, điểm số, lịch học** hoặc thông tin cá nhân:\n• Hỏi trực tiếp **Lab Coach** hoặc **TA**\n• Xem kênh **#announcements** trên Discord\n\n_(Đây là giới hạn thiết kế — mình chỉ trả lời về kiến thức AI/ML từ tài liệu khoá học.)_\n\nNếu bạn có câu hỏi về **nội dung kỹ thuật AI/ML**, mình sẵn sàng giúp! 🎯",
        "citations": [],
        "found_in_kb": False,
        "is_out_of_scope": True,
        "suggested_docs": []
    }


def format_ambiguous_response() -> dict:
    """Standard ambiguous response (G10 — thu hẹp khi nghi ngờ)."""
    return {
        "response": "Câu hỏi của bạn còn hơi chung chung. Bạn muốn tìm về chủ đề cụ thể nào?\n\n• **LLM & Foundation** — Cách hoạt động của LLM, tokenization, embedding\n• **Transformer & Attention** — Kiến trúc Transformer, self-attention, positional encoding\n• **Prompt Engineering** — Cách viết prompt hiệu quả, few-shot, chain-of-thought\n• **RAG & Evaluation** — RAG vs Fine-tuning, golden set, hallucination\n• **Bài toán AI** — JTBD, xác định problem, đo impact, automation level\n\nHoặc bạn có thể **upload PDF** để mình tóm tắt trực tiếp 📄",
        "citations": [],
        "found_in_kb": False,
        "is_out_of_scope": False,
        "suggested_docs": []
    }
