"""
VinAI Knowledge Assistant — FastAPI Backend
"""
import os
from dotenv import load_dotenv

# Load .env file (GEMINI_API_KEY)
load_dotenv()
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


from services.pdf_service import extract_text_from_pdf, truncate_text, validate_pdf
from services.gemini_service import summarize_document, chat_with_kb, synthesize_chat
from services.knowledge_base import (
    get_all_documents, search_documents,
    format_kb_for_context, is_logistics_query, is_ambiguous_query
)

app = FastAPI(
    title="VinAI Knowledge Assistant API",
    description="AI-powered document intelligence for VinAI Discord learning community",
    version="1.0.0"
)

# ── CORS (allow frontend to call API) ──────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Frontend dir path (served at the END, after all API routes) ──
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")



# ── Request/Response Models ────────────────────────────────────
class ChatRequest(BaseModel):
    message: str

class SynthesizeRequest(BaseModel):
    chat_text: str


# ── Health Check ───────────────────────────────────────────────
@app.get("/api/health")
def health():
    api_key_set = bool(os.getenv("GEMINI_API_KEY"))
    return {
        "status": "ok",
        "gemini_configured": api_key_set,
        "message": "VinAI Knowledge Assistant is running!"
    }


# ── Knowledge Base ─────────────────────────────────────────────
@app.get("/api/knowledge-base")
def get_knowledge_base():
    """Return all documents in the knowledge base."""
    docs = get_all_documents()
    return {
        "documents": docs,
        "total": len(docs)
    }


# ── Document Summarization ─────────────────────────────────────
@app.post("/api/summarize")
async def summarize_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF and get an AI-powered structured summary.
    """
    # Read file
    file_bytes = await file.read()
    
    # Validate
    error = validate_pdf(file_bytes, file.filename)
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    # Extract text
    try:
        text, page_count = extract_text_from_pdf(file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    
    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="Không thể đọc nội dung file này. Có thể là file scan ảnh — hãy thử paste text thủ công."
        )
    
    # Truncate to avoid token limits
    truncated_text = truncate_text(text, max_chars=12000)
    
    # Check Gemini API key
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="Gemini API key chưa được cấu hình. Vui lòng set GEMINI_API_KEY."
        )
    
    # Call Gemini
    try:
        summary = summarize_document(truncated_text, file.filename, page_count)
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


# ── Chat Q&A ───────────────────────────────────────────────────
@app.post("/api/chat")
def chat(req: ChatRequest):
    """
    Answer user question using knowledge base context.
    Handles: logistics refusal, ambiguity, KB lookup, out-of-scope.
    """
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message không được để trống.")
    
    # Layer 3: Logistics out-of-scope check
    if is_logistics_query(message):
        return {
            "response": "⚠️ Câu hỏi này nằm ngoài phạm vi của mình.\n\nCâu hỏi về **deadline, điểm số, lịch học** hoặc thông tin cá nhân — vui lòng:\n• Hỏi trực tiếp **Lab Coach** hoặc **TA**\n• Xem kênh **#announcements** trên Discord\n\nNếu muốn tìm tài liệu học thuật AI/ML, mình sẵn sàng hỗ trợ! 🎯",
            "citations": [],
            "found_in_kb": False,
            "is_out_of_scope": True,
            "suggested_docs": []
        }
    
    # Layer 2: Ambiguity check
    if is_ambiguous_query(message):
        return {
            "response": "Câu hỏi của bạn còn hơi chung chung. Bạn muốn tìm về chủ đề cụ thể nào?\n\n• **LLM & Foundation** — Cách hoạt động của LLM, tokenization\n• **Transformer & Attention** — Kiến trúc Transformer, self-attention\n• **Prompt Engineering** — Cách viết prompt hiệu quả\n• **RAG & Evaluation** — RAG vs Fine-tuning, đánh giá hệ thống AI\n• **Bài toán AI** — JTBD, xác định problem, đo impact",
            "citations": [],
            "found_in_kb": False,
            "is_out_of_scope": False,
            "suggested_docs": []
        }
    
    # Layer 1: Search knowledge base
    relevant_docs = search_documents(message)
    kb_context = format_kb_for_context(relevant_docs)
    
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="Gemini API key chưa được cấu hình."
        )
    
    try:
        result = chat_with_kb(message, kb_context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return result


# ── Chat Synthesis ─────────────────────────────────────────────
@app.post("/api/synthesize")
def synthesize(req: SynthesizeRequest):
    """
    Synthesize a Discord chat export into structured insights.
    """
    if not req.chat_text.strip():
        raise HTTPException(status_code=400, detail="Chat text không được để trống.")
    
    if len(req.chat_text) < 50:
        raise HTTPException(
            status_code=400,
            detail="Chat text quá ngắn. Cần ít nhất 50 ký tự để tổng hợp."
        )
    
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=503, detail="Gemini API key chưa được cấu hình.")
    
    try:
        result = synthesize_chat(req.chat_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return result


# ── Serve frontend (MUST be last — after all /api routes) ─────
# html=True: tu dong serve index.html cho /
# CSS/JS duoc truy cap truc tiep: /style.css, /script.js
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
