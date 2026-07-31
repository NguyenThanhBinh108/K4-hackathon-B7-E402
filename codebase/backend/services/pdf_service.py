import fitz  # PyMuPDF
import io
from typing import Optional

VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".mp3", ".wav", ".m4a")
SUPPORTED_EXTENSIONS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".doc": "docx",
    ".pptx": "pptx",
    ".ppt": "pptx",
    ".txt": "txt",
    ".md": "txt",
}


class UnsupportedDocError(Exception):
    """Raised when a file type is recognized but not processable (e.g. video/audio)."""
    def __init__(self, doc_type: str):
        self.doc_type = doc_type
        super().__init__(f"Unsupported doc type: {doc_type}")


def detect_doc_type(filename: str) -> str:
    """Nhận diện loại file theo phần mở rộng.
    Trả về: pdf | docx | pptx | txt | video | unsupported
    """
    name = filename.lower()
    for ext, doc_type in SUPPORTED_EXTENSIONS.items():
        if name.endswith(ext):
            return doc_type
    if name.endswith(VIDEO_EXTENSIONS):
        return "video"
    return "unsupported"


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


def extract_text_from_docx(file_bytes: bytes) -> tuple[str, int]:
    """Extract plain text from a .docx file. Returns: (text, "page"_count ước lượng)."""
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        full_text = "\n\n".join(paragraphs)
        # Word không có khái niệm trang cố định khi đọc XML — ước lượng ~1500 ký tự/trang
        page_count = max(1, (len(full_text) // 1500) + 1)
        return full_text, page_count
    except Exception as e:
        raise ValueError(f"Không thể đọc file Word: {str(e)}")


def extract_text_from_pptx(file_bytes: bytes) -> tuple[str, int]:
    """Extract plain text from a .pptx file. Returns: (text với marker [Slide N], slide_count)."""
    try:
        from pptx import Presentation
        prs = Presentation(io.BytesIO(file_bytes))
        text_parts = []
        for i, slide in enumerate(prs.slides, 1):
            lines = []
            for shape in slide.shapes:
                if shape.has_text_frame and shape.text_frame.text.strip():
                    lines.append(shape.text_frame.text.strip())
            if lines:
                text_parts.append(f"[Slide {i}]\n" + "\n".join(lines))
        full_text = "\n\n".join(text_parts)
        return full_text, len(prs.slides)
    except Exception as e:
        raise ValueError(f"Không thể đọc file PowerPoint: {str(e)}")


def extract_text_from_txt(file_bytes: bytes) -> tuple[str, int]:
    """Extract plain text from a .txt/.md file. Returns: (text, "page"_count ước lượng)."""
    try:
        text = file_bytes.decode("utf-8", errors="replace").strip()
        page_count = max(1, (len(text) // 2000) + 1)
        return text, page_count
    except Exception as e:
        raise ValueError(f"Không thể đọc file text: {str(e)}")


def extract_text(file_bytes: bytes, filename: str) -> tuple[str, int, str]:
    """Điều phối extraction theo loại file. Trả về (text, page_count, doc_type).
    Raise UnsupportedDocError("video") nếu là video/audio — không xử lý nội dung (non-goal).
    Raise ValueError nếu định dạng không hỗ trợ hoặc lỗi đọc file.
    """
    doc_type = detect_doc_type(filename)
    if doc_type == "video":
        raise UnsupportedDocError("video")
    if doc_type == "unsupported":
        raise UnsupportedDocError("unsupported")

    if doc_type == "pdf":
        text, page_count = extract_text_from_pdf(file_bytes)
    elif doc_type == "docx":
        text, page_count = extract_text_from_docx(file_bytes)
    elif doc_type == "pptx":
        text, page_count = extract_text_from_pptx(file_bytes)
    elif doc_type == "txt":
        text, page_count = extract_text_from_txt(file_bytes)
    else:
        raise UnsupportedDocError("unsupported")

    return text, page_count, doc_type


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


def validate_file_size(file_bytes: bytes, max_mb: int = 20) -> Optional[str]:
    """Validate generic file size (dùng cho docx/pptx/txt cùng giới hạn PDF)."""
    if len(file_bytes) > max_mb * 1024 * 1024:
        return f"File quá lớn (tối đa {max_mb}MB). Vui lòng chọn file nhỏ hơn."
    return None
