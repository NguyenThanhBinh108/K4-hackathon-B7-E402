import fitz  # PyMuPDF
import io
from typing import Optional

def extract_text_from_pdf(file_bytes: bytes) -> tuple[str, int]:
    """
    Extract plain text from PDF bytes.
    Returns: (extracted_text, page_count)
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page_count = len(doc)
        
        text_parts = []
        for page_num, page in enumerate(doc, 1):
            page_text = page.get_text("text")
            if page_text.strip():
                text_parts.append(f"[Trang {page_num}]\n{page_text.strip()}")
        
        doc.close()
        full_text = "\n\n".join(text_parts)
        
        if not full_text.strip():
            return "", page_count
            
        return full_text, page_count
    
    except Exception as e:
        raise ValueError(f"Không thể đọc file PDF: {str(e)}")

def truncate_text(text: str, max_chars: int = 12000) -> str:
    """Truncate text to fit within Gemini context limits."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... Nội dung đã được cắt bớt do quá dài ...]"

def validate_pdf(file_bytes: bytes, filename: str) -> Optional[str]:
    """Validate PDF file. Returns error message or None if valid."""
    if not filename.lower().endswith(".pdf"):
        return "Chỉ hỗ trợ file PDF. Vui lòng chọn file .pdf"
    
    if len(file_bytes) > 20 * 1024 * 1024:  # 20MB limit
        return "File quá lớn (tối đa 20MB). Vui lòng chọn file nhỏ hơn."
    
    # Check PDF magic bytes
    if not file_bytes.startswith(b"%PDF"):
        return "File không phải PDF hợp lệ."
    
    return None
