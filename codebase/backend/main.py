"""
VinAI Knowledge Assistant — FastAPI Backend
Router: logistics → injection → ambiguous → RAG_QUERY
Conversational memory: 4 turns per session
"""
import os
import json
import time
from collections import defaultdict
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

from services.pdf_service import extract_text, truncate_text, validate_file_size, UnsupportedDocError
from services.gemini_service import (
    summarize_document, chat_with_kb, synthesize_chat, log_ai_call,
    AllProvidersExhaustedError,
)
from services.knowledge_base import (
    get_all_documents, search_documents,
    format_kb_for_context, is_logistics_query, is_ambiguous_query,
    is_injection_attempt, format_out_of_scope_response, format_ambiguous_response
)

app = FastAPI(
    title="VinAI Knowledge Assistant API",
    description="AI-powered document intelligence for VinAI Discord learning community",
    version="2.0.0"
)

# ── CORS ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
LOG_PATH     = os.path.join(os.path.dirname(__file__), "..", "..", "..", "eval", "ai_call_log.jsonl")
FEEDBACK_LOG = os.path.join(os.path.dirname(__file__), "..", "..", "..", "validation", "feedback.jsonl")

# ── Conversational Memory (session → last 4 turns) ───────────────────
# Key: session_id (str), Value: list of {"role": "user"|"bot", "text": str}
_conversation_memory: dict[str, list] = defaultdict(list)
MAX_MEMORY_TURNS = 4  # số turn giữ lại mỗi phía

def _get_context(session_id: str) -> str:
    history = _conversation_memory.get(session_id, [])
    if not history:
        return ""
    lines = []
    for turn in history[-MAX_MEMORY_TURNS * 2:]:
        prefix = "User" if turn["role"] == "user" else "Assistant"
        lines.append(f"{prefix}: {turn['text'][:300]}")  # cap mỗi turn 300 chars
    return "\n".join(lines)

def _add_to_memory(session_id: str, role: str, text: str):
    _conversation_memory[session_id].append({"role": role, "text": text})
    # Keep only last MAX_MEMORY_TURNS * 2 entries
    if len(_conversation_memory[session_id]) > MAX_MEMORY_TURNS * 2 + 2:
        _conversation_memory[session_id] = _conversation_memory[session_id][-(MAX_MEMORY_TURNS * 2):]


# ── Request / Response Models ─────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

class SynthesizeRequest(BaseModel):
    chat_text: str

class FeedbackRequest(BaseModel):
    message_id: str
    rating: str          # "up" | "down"
    comment: Optional[str] = ""
    session_id: Optional[str] = "default"


# ═══════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════

@app.get("/api/health")
def health():
    api_key_set = bool(os.getenv("GEMINI_API_KEY"))
    return {
        "status": "ok",
        "gemini_configured": api_key_set,
        "kb_docs": len(get_all_documents()),
        "message": "VinAI Knowledge Assistant v2.0 is running!"
    }


@app.get("/api/knowledge-base")
def get_knowledge_base():
    docs = get_all_documents()
    return {"documents": docs, "total": len(docs)}


# ── Document Summarization ────────────────────────────────────────────
@app.post("/api/summarize")
async def summarize_pdf(file: UploadFile = File(...)):
    """Upload PDF/Word/PowerPoint/Text → AI structured summary with citations.
    Video/audio được nhận diện nhưng KHÔNG xử lý nội dung — đúng non-goal đã khai (spec.md §4).
    """
    file_bytes = await file.read()

    error = validate_file_size(file_bytes)
    if error:
        raise HTTPException(status_code=400, detail=error)

    try:
        text, page_count, doc_type = extract_text(file_bytes, file.filename)
    except UnsupportedDocError as e:
        if e.doc_type == "video":
            raise HTTPException(
                status_code=422,
                detail="Video/audio chưa hỗ trợ tự động tóm tắt — cần transcript dạng text. "
                       "Xem #tài-nguyên hoặc paste text thủ công."
            )
        raise HTTPException(
            status_code=400,
            detail="Định dạng file chưa hỗ trợ (chỉ PDF, Word, PowerPoint, Text)."
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="Không thể đọc nội dung file này (có thể là file scan ảnh). Hãy thử paste text thủ công."
        )

    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=503, detail="Gemini API key chưa được cấu hình.")

    truncated_text = truncate_text(text, max_chars=12000)

    try:
        summary = summarize_document(truncated_text, file.filename, page_count)
    except AllProvidersExhaustedError as e:
        raise HTTPException(status_code=503, headers={"Retry-After": "30"},
                             detail="Hệ thống AI đang quá tải, vui lòng thử lại sau ít phút.")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi AI: {str(e)}")

    return {
        "success": True,
        "filename": file.filename,
        "page_count": page_count,
        "summary": summary
    }


# ── Chat Q&A ──────────────────────────────────────────────────────────
@app.post("/api/chat")
def chat(req: ChatRequest):
    """
    4-layer routing:
      ③ Injection detection  → block
      ③ Logistics detection  → block (no Gemini call)
      ② Ambiguity detection  → ask back
      ① RAG search + Gemini generate
    """
    message = req.message.strip()
    session = req.session_id or "default"

    if not message:
        raise HTTPException(status_code=400, detail="Message không được để trống.")
    if len(message) > 2000:
        raise HTTPException(status_code=400, detail="Message quá dài (tối đa 2000 ký tự).")

    # ── Layer ③: Prompt injection ─────────────────────────────────────
    if is_injection_attempt(message):
        resp = format_out_of_scope_response(reason="injection")
        _add_to_memory(session, "user", message)
        _add_to_memory(session, "bot", resp["response"])
        return resp

    # ── Layer ③: Logistics (blocked before Gemini) ────────────────────
    if is_logistics_query(message):
        resp = format_out_of_scope_response(reason="logistics")
        _add_to_memory(session, "user", message)
        _add_to_memory(session, "bot", resp["response"])
        # Log block (no AI call = no token cost, evidence for eval)
        _write_route_log("OUT_OF_SCOPE_LOGISTICS", message, has_citation=False)
        return resp

    # ── Layer ②: Ambiguous ────────────────────────────────────────────
    if is_ambiguous_query(message):
        resp = format_ambiguous_response()
        _add_to_memory(session, "user", message)
        _add_to_memory(session, "bot", resp["response"])
        _write_route_log("AMBIGUOUS", message, has_citation=False)
        return resp

    # ── Layer ①+RAG: KB search → Gemini generate ─────────────────────
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=503, detail="Gemini API key chưa được cấu hình.")

    if os.getenv("KB_BACKEND", "json") == "vector":
        from services.vector_kb import vector_search, format_vector_context
        kb_context = format_vector_context(vector_search(message))
    else:
        relevant_docs = search_documents(message)
        kb_context = format_kb_for_context(relevant_docs)

    # Build context-aware message including conversation history
    conv_context = _get_context(session)

    try:
        result = chat_with_kb(message, kb_context, conversation_history=conv_context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Store in memory
    _add_to_memory(session, "user", message)
    _add_to_memory(session, "bot", result.get("response", ""))

    return result


# ── Synthesize ────────────────────────────────────────────────────────
@app.post("/api/synthesize")
def synthesize(req: SynthesizeRequest):
    """Synthesize Discord chat export into structured insights."""
    text = req.chat_text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Chat text không được để trống.")
    if len(text) < 50:
        raise HTTPException(status_code=400, detail="Chat text quá ngắn (cần ≥50 ký tự).")
    if len(text) > 20000:
        raise HTTPException(status_code=400, detail="Chat text quá dài (tối đa 20000 ký tự).")

    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=503, detail="Gemini API key chưa được cấu hình.")

    try:
        result = synthesize_chat(text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return result


# ── User Feedback ─────────────────────────────────────────────────────
@app.post("/api/feedback")
def log_feedback(req: FeedbackRequest):
    """
    Log user 👍👎 feedback — evidence for validation/ and eval/.
    G8: gạt bỏ dễ dàng + G9: thu thập feedback.
    """
    os.makedirs(os.path.dirname(FEEDBACK_LOG), exist_ok=True)
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "message_id": req.message_id,
        "rating": req.rating,
        "comment": req.comment or "",
        "session_id": req.session_id or "default"
    }
    try:
        with open(FEEDBACK_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # Không crash vì feedback log
    return {"status": "logged", "rating": req.rating}


# ── Helpers ───────────────────────────────────────────────────────────
def _write_route_log(route: str, message: str, has_citation: bool):
    """Write a route decision log (no AI call) for eval evidence."""
    try:
        import hashlib
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "route": route,
            "model": "NONE (blocked before LLM)",
            "input_hash": hashlib.md5(message.encode()).hexdigest()[:8],
            "prompt_length": len(message),
            "has_citation": has_citation,
            "success": True,
            "golden_case": None
        }
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ── Serve Frontend (must be LAST after all /api routes) ──────────────
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
