import os
import json
import hashlib
import time
import google.generativeai as genai
from typing import Optional

# ── AI Call Logger (evidence cho eval/) ───────────────────────────────────
LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "eval", "ai_call_log.jsonl")

def log_ai_call(route: str, model: str, prompt: str, has_citation: bool, success: bool = True, case_id: str = None):
    """Log mỗi lời gọi AI thật để có trace evidence trong repo."""
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "route": route,
            "model": model,
            "input_hash": hashlib.md5(prompt.encode()).hexdigest()[:8],
            "prompt_length": len(prompt),
            "has_citation": has_citation,
            "success": success,
            "golden_case": case_id
        }
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # logging không được làm crash main flow

# ── Configure Gemini ───────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-1.5-flash"

SUMMARIZE_SYSTEM = """Bạn là Knowledge Assistant của khoá VinAI Thực Chiến.
Nhiệm vụ: Phân tích và tóm tắt tài liệu học tập AI/ML theo cấu trúc NGHIÊM NGẶT.

LUẬT BẮT BUỘC:
1. Chỉ dùng thông tin CÓ trong tài liệu được cung cấp. KHÔNG bịa.
2. Luôn trích dẫn nguồn (trang, slide, hoặc đoạn cụ thể).
3. Nếu không chắc → viết "Không rõ từ tài liệu này" thay vì đoán.
4. Phân loại module: Day 1 (Foundation: LLM, Transformer...) hoặc Day 2 (Bài toán AI, Evaluation...).
5. Phân loại cấp độ: Foundation | Intermediate | Advanced.
6. Output PHẢI là JSON hợp lệ theo đúng schema yêu cầu."""

CHAT_SYSTEM = """Bạn là Knowledge Assistant của khoá VinAI Thực Chiến.
Phạm vi: Chỉ trả lời về kiến thức AI/ML từ tài liệu khoá học.

LUẬT BẮT BUỘC:
1. Câu hỏi về deadline, điểm số, lịch học, học phí, thông tin cá nhân → TỪ CHỐI lịch sự.
2. Nếu có trong Knowledge Base → trả lời kèm citation [Txx-NNN].
3. Nếu KHÔNG có trong KB → nói thẳng "Không tìm thấy trong tài liệu hiện có".
4. KHÔNG đoán mò kiến thức kỹ thuật — sai thì học viên học sai.
5. Luôn kèm gợi ý "Xem thêm: [tên tài liệu]" nếu có tài liệu liên quan.
6. Với câu hỏi kỹ thuật sâu (softmax, attention, gradient...) LUÔN kèm: '🤖 Xem [TXX] để verify chi tiết kỹ thuật.'
7. Response tối đa 900 ký tự. Nếu cần dài hơn, dùng bullet points ngắn gọn.
8. Tone: Thân thiện, chính xác, ngắn gọn. Mỗi trả lời kết thúc bằng: '🤖 Tóm tắt tự động — xem nguyên văn để xác nhận.'"""

SYNTHESIZE_SYSTEM = """Bạn là Knowledge Assistant của khoá VinAI Thực Chiến.
Nhiệm vụ: Tổng hợp đoạn chat Discord và rút ra insights.

LUẬT:
1. Chỉ phân tích những gì CÓ trong đoạn chat. Không thêm thông tin ngoài.
2. Xác định chủ đề kiến thức, câu hỏi phổ biến, điểm học viên đang stuck.
3. Output PHẢI là JSON hợp lệ."""


def summarize_document(text: str, filename: str, page_count: int) -> dict:
    """
    Call Gemini to summarize a document.
    Returns structured JSON.
    """
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=SUMMARIZE_SYSTEM,
    )

    prompt = f"""Tài liệu cần phân tích:
Tên file: {filename}
Số trang: {page_count}

NỘI DUNG TÀI LIỆU:
{text}

Hãy phân tích và trả về JSON với ĐÚNG schema sau (không thêm text ngoài JSON):
{{
  "title": "Tiêu đề đầy đủ của tài liệu",
  "subject": "Chủ đề chính trong 1 câu",
  "module": "Day 1 | Day 2 | Không xác định",
  "level": "Foundation | Intermediate | Advanced",
  "key_concepts": ["khái niệm 1", "khái niệm 2", "khái niệm 3", "khái niệm 4"],
  "key_takeaways": [
    "Takeaway quan trọng nhất (1-2 câu)",
    "Takeaway thứ 2",
    "Takeaway thứ 3"
  ],
  "prerequisites": ["Cần biết điều gì trước khi học tài liệu này"],
  "citations": ["Trang X hoặc đoạn cụ thể", "..."],
  "reliability_score": 90,
  "note": "Ghi chú nếu có phần không rõ từ tài liệu (hoặc null)"
}}"""

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        
        # Strip markdown code blocks if present
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1])
        
        result = json.loads(raw)
        log_ai_call("SUMMARY", MODEL_NAME, prompt, has_citation=True, success=True)
        return result
    
    except json.JSONDecodeError:
        # Try to extract JSON from response
        import re
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            result = json.loads(match.group())
            log_ai_call("SUMMARY", MODEL_NAME, prompt, has_citation=True, success=True)
            return result
        log_ai_call("SUMMARY", MODEL_NAME, prompt, has_citation=False, success=False)
        raise ValueError("Gemini trả về JSON không hợp lệ")


def chat_with_kb(message: str, kb_context: str, conversation_history: str = "") -> dict:
    """
    Chat endpoint: answer user question using KB context.
    Returns: {response, citations, found_in_kb, is_logistics}
    """
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=CHAT_SYSTEM,
    )

    history_section = ""
    if conversation_history:
        history_section = f"\n\nLịch sử hội thoại gần đây (ngữ cảnh):\n{conversation_history}\n"

    prompt = f"""Knowledge Base hiện có:
{kb_context}
{history_section}
Câu hỏi của học viên: {message}

Trả lời theo JSON:
{{
  "response": "Câu trả lời đầy đủ (hỗ trợ markdown với **bold** và bullet points)",
  "citations": ["[Txx-NNN]", "..."],
  "found_in_kb": true/false,
  "is_out_of_scope": true/false,
  "suggested_docs": ["tên tài liệu liên quan nếu có"]
}}"""

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1])
        
        result = json.loads(raw)
        has_cite = bool(result.get("citations"))
        log_ai_call("RAG_QUERY", MODEL_NAME, prompt, has_citation=has_cite, success=True)
        return result
    
    except Exception:
        log_ai_call("RAG_QUERY", MODEL_NAME, prompt, has_citation=False, success=False)
        return {
            "response": response.text if 'response' in locals() else "Có lỗi xảy ra, vui lòng thử lại.",
            "citations": [],
            "found_in_kb": False,
            "is_out_of_scope": False,
            "suggested_docs": []
        }


def synthesize_chat(chat_text: str) -> dict:
    """
    Synthesize Discord chat export into structured insights.
    """
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=SYNTHESIZE_SYSTEM,
    )

    prompt = f"""Đoạn chat Discord cần tổng hợp:
{chat_text}

Tổng hợp và trả về JSON:
{{
  "main_topics": [
    {{"topic": "Tên chủ đề", "count": 5, "description": "Mô tả ngắn"}}
  ],
  "popular_questions": [
    {{"question": "Câu hỏi phổ biến nhất", "asked_by": 3, "brief_answer": "Trả lời ngắn"}}
  ],
  "stuck_points": ["Điểm học viên đang bị stuck"],
  "suggested_resources": ["Tên tài liệu gợi ý"],
  "summary": "Tổng hợp 2-3 câu về toàn bộ đoạn chat"
}}"""

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1])
        
        result = json.loads(raw)
        log_ai_call("SYNTHESIZE", MODEL_NAME, prompt, has_citation=False, success=True)
        return result
    
    except Exception:
        log_ai_call("SYNTHESIZE", MODEL_NAME, prompt, has_citation=False, success=False)
        return {"error": "Không thể tổng hợp chat. Vui lòng thử lại."}
