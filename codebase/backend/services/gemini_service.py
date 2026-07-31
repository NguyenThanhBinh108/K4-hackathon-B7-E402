import os
import json
import hashlib
import time
import random
import re
import threading
from typing import Optional

# ── AI Call Logger ────────────────────────────────────────────────────
LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "eval", "ai_call_log.jsonl")


def log_ai_call(route: str, model: str, prompt: str, has_citation: bool, success: bool = True,
                 case_id: str = None, provider: str = None, attempt: int = 1,
                 error_type: str = None, latency_ms: int = None, cache_hit: bool = False):
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "route": route,
            "model": model,
            "provider": provider,
            "input_hash": hashlib.md5(prompt.encode()).hexdigest()[:8],
            "prompt_length": len(prompt),
            "has_citation": has_citation,
            "success": success,
            "golden_case": case_id,
            "attempt": attempt,
            "error_type": error_type,
            "latency_ms": latency_ms,
            "cache_hit": cache_hit,
        }
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ── Provider Selection ────────────────────────────────────────────────
# Ưu tiên: Gemini → Groq (fallback thật lúc runtime khi Gemini bị rate-limit/lỗi)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ── Tunables (rate-limit resilience) ───────────────────────────────────
RETRY_MAX_ATTEMPTS = int(os.getenv("LLM_RETRY_MAX_ATTEMPTS", "3"))
RETRY_BASE_DELAY = float(os.getenv("LLM_RETRY_BASE_DELAY", "1.0"))
CACHE_TTL_SECONDS = int(os.getenv("LLM_CACHE_TTL_SECONDS", "600"))
CACHE_MAX_ENTRIES = int(os.getenv("LLM_CACHE_MAX_ENTRIES", "200"))
MAX_CONCURRENT = int(os.getenv("LLM_MAX_CONCURRENT", "2"))

_llm_semaphore = threading.Semaphore(MAX_CONCURRENT)

_gemini_client = None
_groq_client = None
_init_lock = threading.Lock()

# ── Simple TTL cache (prompt hash → result) ────────────────────────────
_cache: dict = {}
_cache_order: list = []
_cache_lock = threading.Lock()


class AllProvidersExhaustedError(Exception):
    """Raised when both Gemini and Groq fail (retry exhausted) for a request."""
    pass


def _cache_get(key: str):
    with _cache_lock:
        entry = _cache.get(key)
        if entry is None:
            return None
        result, ts = entry
        if time.time() - ts > CACHE_TTL_SECONDS:
            _cache.pop(key, None)
            if key in _cache_order:
                _cache_order.remove(key)
            return None
        return result


def _cache_set(key: str, result):
    with _cache_lock:
        if key not in _cache and len(_cache_order) >= CACHE_MAX_ENTRIES:
            oldest = _cache_order.pop(0)
            _cache.pop(oldest, None)
        _cache[key] = (result, time.time())
        if key not in _cache_order:
            _cache_order.append(key)


def _cache_key(system: str, prompt: str) -> str:
    return hashlib.md5((system + "||" + prompt).encode()).hexdigest()


def _init_clients():
    global _gemini_client, _groq_client
    with _init_lock:
        if GEMINI_API_KEY and not GEMINI_API_KEY.startswith("your_") and _gemini_client is None:
            try:
                from google import genai
                _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
                print(f"[LLM] Gemini client ready ({GEMINI_MODEL})")
            except Exception as e:
                print(f"[LLM] Gemini init failed: {e}")

        if GROQ_API_KEY and not GROQ_API_KEY.startswith("your_") and _groq_client is None:
            try:
                from groq import Groq
                _groq_client = Groq(api_key=GROQ_API_KEY)
                print(f"[LLM] Groq client ready ({GROQ_MODEL})")
            except Exception as e:
                print(f"[LLM] Groq init failed: {e}")

        if _gemini_client is None and _groq_client is None:
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
6. Với câu hỏi kỹ thuật sâu, LUÔN kèm "🤖 Xem [TXX] để verify chi tiết kỹ thuật."
7. Mọi trả lời kết thúc bằng: '🤖 Tóm tắt tự động — xem nguyên văn để xác nhận.'"""

SYNTHESIZE_SYSTEM = """Bạn là Knowledge Assistant của khoá VinAI Thực Chiến.
Nhiệm vụ: Tổng hợp đoạn chat Discord và rút ra insights.
Output PHẢI là JSON hợp lệ."""


# ── Retryable error detection ───────────────────────────────────────────
_RETRYABLE_MARKERS = (
    "429", "resource_exhausted", "rate limit", "rate_limit",
    "503", "unavailable", "timeout", "deadline exceeded",
)


def _classify_error(exc: Exception) -> str:
    msg = str(exc).lower()
    status_code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if status_code in (429,) or "429" in msg or "resource_exhausted" in msg or "rate limit" in msg or "rate_limit" in msg:
        return "rate_limit"
    if status_code in (503,) or "503" in msg or "unavailable" in msg:
        return "unavailable"
    if "timeout" in msg or "deadline exceeded" in msg:
        return "timeout"
    return "other"


def _is_retryable(error_type: str) -> bool:
    return error_type in ("rate_limit", "unavailable", "timeout")


# ── Single-provider raw call ────────────────────────────────────────────
def _call_gemini(system: str, prompt: str) -> str:
    from google.genai import types
    response = _gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.3,
            max_output_tokens=1500,
        )
    )
    return response.text.strip()


def _call_groq(system: str, prompt: str) -> str:
    response = _groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=1500,
    )
    return response.choices[0].message.content.strip()


def _call_with_retry(provider_name: str, call_fn, system: str, prompt: str):
    """Retry a single provider call with exponential backoff + jitter.
    Returns (text, attempt_count, error_type_or_None). Raises the last
    exception if all attempts (or a non-retryable error) fail.
    """
    last_exc = None
    last_error_type = None
    for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
        try:
            text = call_fn(system, prompt)
            return text, attempt, None
        except Exception as e:
            last_exc = e
            last_error_type = _classify_error(e)
            if not _is_retryable(last_error_type) or attempt == RETRY_MAX_ATTEMPTS:
                raise
            delay = RETRY_BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
            print(f"[LLM] {provider_name} attempt {attempt} failed ({last_error_type}), retry in {delay:.1f}s")
            time.sleep(delay)
    raise last_exc


# ── Core Generate Function ────────────────────────────────────────────
def _generate(system: str, prompt: str) -> tuple:
    """Call LLM with retry + runtime fallback (Gemini → Groq).
    Returns (text, provider, model, attempt, error_type, latency_ms).
    Raises AllProvidersExhaustedError if every configured provider fails.
    """
    _init_clients()

    if _gemini_client is None and _groq_client is None:
        raise ValueError("Chưa có API key hợp lệ. Set GEMINI_API_KEY hoặc GROQ_API_KEY trong .env")

    start = time.time()
    with _llm_semaphore:
        if _gemini_client is not None:
            try:
                text, attempt, _ = _call_with_retry("gemini", _call_gemini, system, prompt)
                latency_ms = int((time.time() - start) * 1000)
                return text, "gemini", GEMINI_MODEL, attempt, None, latency_ms
            except Exception as e:
                gemini_error_type = _classify_error(e)
                print(f"[LLM] Gemini exhausted ({gemini_error_type}): {e}")
                if _groq_client is None:
                    latency_ms = int((time.time() - start) * 1000)
                    raise AllProvidersExhaustedError(
                        f"Gemini thất bại ({gemini_error_type}) và không có provider dự phòng: {e}"
                    ) from e
                # fall through to Groq

        try:
            text, attempt, _ = _call_with_retry("groq", _call_groq, system, prompt)
            latency_ms = int((time.time() - start) * 1000)
            return text, "groq", GROQ_MODEL, attempt, None, latency_ms
        except Exception as e:
            groq_error_type = _classify_error(e)
            latency_ms = int((time.time() - start) * 1000)
            raise AllProvidersExhaustedError(
                f"Mọi provider đều thất bại. Groq lỗi cuối ({groq_error_type}): {e}"
            ) from e


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
    key = _cache_key(SUMMARIZE_SYSTEM, prompt)
    cached = _cache_get(key)
    if cached is not None:
        raw, provider, model = cached
        result = _parse_json(raw)
        log_ai_call("SUMMARY", model, prompt, has_citation=True, success=True,
                    provider=provider, attempt=0, cache_hit=True, latency_ms=0)
        return result

    provider, model, attempt, latency_ms = None, GEMINI_MODEL or "unknown", None, None
    try:
        raw, provider, model, attempt, error_type, latency_ms = _generate(SUMMARIZE_SYSTEM, prompt)
        result = _parse_json(raw)
        _cache_set(key, (raw, provider, model))
        log_ai_call("SUMMARY", model, prompt, has_citation=True, success=True,
                    provider=provider, attempt=attempt, latency_ms=latency_ms)
        return result
    except AllProvidersExhaustedError:
        log_ai_call("SUMMARY", model, prompt, has_citation=False, success=False,
                    provider=provider, attempt=attempt or 0, error_type="rate_limit")
        raise
    except Exception as e:
        log_ai_call("SUMMARY", model, prompt, has_citation=False, success=False,
                    provider=provider, attempt=attempt or 0, latency_ms=latency_ms, error_type="parse_error")
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
    key = _cache_key(CHAT_SYSTEM, prompt)
    cached = _cache_get(key)
    if cached is not None:
        raw, provider, model = cached
        result = _parse_json(raw)
        has_cite = bool(result.get("citations"))
        log_ai_call("RAG_QUERY", model, prompt, has_citation=has_cite, success=True,
                    provider=provider, attempt=0, cache_hit=True, latency_ms=0)
        return result

    provider, model, attempt, latency_ms = None, GEMINI_MODEL or "unknown", None, None
    try:
        raw, provider, model, attempt, error_type, latency_ms = _generate(CHAT_SYSTEM, prompt)
        result = _parse_json(raw)
        _cache_set(key, (raw, provider, model))
        has_cite = bool(result.get("citations"))
        log_ai_call("RAG_QUERY", model, prompt, has_citation=has_cite, success=True,
                    provider=provider, attempt=attempt, latency_ms=latency_ms)
        return result
    except AllProvidersExhaustedError as e:
        log_ai_call("RAG_QUERY", model, prompt, has_citation=False, success=False,
                    provider=provider, attempt=attempt or 0, error_type="rate_limit")
        return {
            "response": "Hệ thống AI đang quá tải (rate limit), vui lòng thử lại sau ít phút.",
            "citations": [],
            "found_in_kb": False,
            "is_out_of_scope": False,
            "suggested_docs": []
        }
    except Exception as e:
        log_ai_call("RAG_QUERY", model, prompt, has_citation=False, success=False,
                    provider=provider, attempt=attempt or 0, latency_ms=latency_ms, error_type="parse_error")
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
    provider, model, attempt, latency_ms = None, GEMINI_MODEL or "unknown", None, None
    try:
        raw, provider, model, attempt, error_type, latency_ms = _generate(SYNTHESIZE_SYSTEM, prompt)
        result = _parse_json(raw)
        log_ai_call("SYNTHESIZE", model, prompt, has_citation=False, success=True,
                    provider=provider, attempt=attempt, latency_ms=latency_ms)
        return result
    except AllProvidersExhaustedError as e:
        log_ai_call("SYNTHESIZE", model, prompt, has_citation=False, success=False,
                    provider=provider, attempt=attempt or 0, error_type="rate_limit")
        return {"error": f"Hệ thống AI đang quá tải (rate limit): {str(e)[:150]}"}
    except Exception as e:
        log_ai_call("SYNTHESIZE", model, prompt, has_citation=False, success=False,
                    provider=provider, attempt=attempt or 0, latency_ms=latency_ms, error_type="parse_error")
        return {"error": f"Lỗi: {str(e)[:150]}"}
