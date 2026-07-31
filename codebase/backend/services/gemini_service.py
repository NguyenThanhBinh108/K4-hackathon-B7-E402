import os
import json
import hashlib
import time
import re
from typing import Optional

# ── AI Call Logger ────────────────────────────────────────────────────
LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "eval", "ai_call_log.jsonl")

def log_ai_call(route: str, model: str, prompt: str, has_citation: bool, success: bool = True, case_id: str = None):
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
        pass


# ── Provider Selection ────────────────────────────────────────────────
# Ưu tiên: Gemini → Groq → lỗi
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")

_client   = None
_provider = None
MODEL_NAME = None

def _init_client():
    global _client, _provider, MODEL_NAME
    if _client is not None:
        return

    if GEMINI_API_KEY and not GEMINI_API_KEY.startswith("your_"):
        try:
            from google import genai
            _client = genai.Client(api_key=GEMINI_API_KEY)
            _provider = "gemini"
            MODEL_NAME = "gemini-2.0-flash"
            print(f"[LLM] Provider: Gemini ({MODEL_NAME})")
            return
        except Exception as e:
            print(f"[LLM] Gemini init failed: {e} — trying Groq...")

    if GROQ_API_KEY and not GROQ_API_KEY.startswith("your_"):
        try:
            from groq import Groq
            _client = Groq(api_key=GROQ_API_KEY)
            _provider = "groq"
            MODEL_NAME = "llama-3.3-70b-versatile"
            print(f"[LLM] Provider: Groq ({MODEL_NAME})")
            return
        except Exception as e:
            print(f"[LLM] Groq init failed: {e}")

    print("[LLM] WARNING: No valid API key found! Set GEMINI_API_KEY or GROQ_API_KEY in .env")


# ── System Prompts ────────────────────────────────────────────────────
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
1. Câu hỏi về deadline, điểm số, lịch học → TỪ CHỐI lịch sự.
2. Nếu có trong Knowledge Base → trả lời kèm citation [Txx-NNN].
3. Nếu KHÔNG có trong KB → nói "Không tìm thấy trong tài liệu hiện có".
4. KHÔNG đoán mò kiến thức kỹ thuật.
5. Response tối đa 900 ký tự, dùng bullet points.
6. Mọi trả lời kết thúc bằng: '🤖 Tóm tắt tự động — xem nguyên văn để xác nhận.'"""

SYNTHESIZE_SYSTEM = """Bạn là Knowledge Assistant của khoá VinAI Thực Chiến.
Nhiệm vụ: Tổng hợp đoạn chat Discord và rút ra insights.
Output PHẢI là JSON hợp lệ."""


# ── Core Generate Function ────────────────────────────────────────────
def _generate(system: str, prompt: str) -> str:
    """Call LLM (Gemini hoặc Groq) và trả về text."""
    _init_client()

    if _client is None:
        raise ValueError("Chưa có API key hợp lệ. Set GEMINI_API_KEY hoặc GROQ_API_KEY trong .env")

    if _provider == "gemini":
        from google.genai import types
        response = _client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.3,
                max_output_tokens=1500,
            )
        )
        return response.text.strip()

    elif _provider == "groq":
        response = _client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1500,
        )
        return response.choices[0].message.content.strip()

    raise ValueError(f"Unknown provider: {_provider}")


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(text)


# ── Public Functions ──────────────────────────────────────────────────
def summarize_document(text: str, filename: str, page_count: int) -> dict:
    prompt = f"""Tài liệu cần phân tích:
Tên file: {filename}
Số trang: {page_count}

NỘI DUNG:
{text}

Trả về JSON với schema:
{{
  "title": "Tiêu đề đầy đủ",
  "subject": "Chủ đề chính trong 1 câu",
  "module": "Day 1 | Day 2 | Không xác định",
  "level": "Foundation | Intermediate | Advanced",
  "key_concepts": ["k1", "k2", "k3", "k4"],
  "key_takeaways": ["Takeaway 1", "Takeaway 2", "Takeaway 3"],
  "prerequisites": ["Điều cần biết trước"],
  "citations": ["Trang X", "..."],
  "reliability_score": 90,
  "note": null
}}"""
    try:
        raw = _generate(SUMMARIZE_SYSTEM, prompt)
        result = _parse_json(raw)
        log_ai_call("SUMMARY", MODEL_NAME or "unknown", prompt, has_citation=True, success=True)
        return result
    except Exception as e:
        log_ai_call("SUMMARY", MODEL_NAME or "unknown", prompt, has_citation=False, success=False)
        raise ValueError(f"LLM lỗi: {str(e)}")


def chat_with_kb(message: str, kb_context: str, conversation_history: str = "") -> dict:
    history_section = f"\n\nLịch sử:\n{conversation_history}\n" if conversation_history else ""
    prompt = f"""Knowledge Base:
{kb_context}
{history_section}
Câu hỏi: {message}

Trả lời JSON:
{{
  "response": "...",
  "citations": ["[Txx-NNN]"],
  "found_in_kb": true,
  "is_out_of_scope": false,
  "suggested_docs": []
}}"""
    try:
        raw = _generate(CHAT_SYSTEM, prompt)
        result = _parse_json(raw)
        has_cite = bool(result.get("citations"))
        log_ai_call("RAG_QUERY", MODEL_NAME or "unknown", prompt, has_citation=has_cite, success=True)
        return result
    except Exception as e:
        log_ai_call("RAG_QUERY", MODEL_NAME or "unknown", prompt, has_citation=False, success=False)
        return {
            "response": f"Lỗi xử lý: {str(e)[:200]}. Vui lòng thử lại.",
            "citations": [],
            "found_in_kb": False,
            "is_out_of_scope": False,
            "suggested_docs": []
        }


def synthesize_chat(chat_text: str) -> dict:
    prompt = f"""Chat Discord:
{chat_text}

Trả về JSON:
{{
  "main_topics": [{{"topic": "...", "count": 5, "description": "..."}}],
  "popular_questions": [{{"question": "...", "asked_by": 3, "brief_answer": "..."}}],
  "stuck_points": ["..."],
  "suggested_resources": ["..."],
  "summary": "Tổng hợp 2-3 câu"
}}"""
    try:
        raw = _generate(SYNTHESIZE_SYSTEM, prompt)
        result = _parse_json(raw)
        log_ai_call("SYNTHESIZE", MODEL_NAME or "unknown", prompt, has_citation=False, success=True)
        return result
    except Exception as e:
        log_ai_call("SYNTHESIZE", MODEL_NAME or "unknown", prompt, has_citation=False, success=False)
        return {"error": f"Lỗi: {str(e)[:150]}"}
