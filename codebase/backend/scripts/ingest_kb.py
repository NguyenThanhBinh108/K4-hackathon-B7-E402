"""
Ingest data/vlearn-pack/ (transcript + slide + chatlog thật) vao Chroma vector store.
Idempotent: xoa va build lai collection moi lan chay.
Chay: python scripts/ingest_kb.py  (tu thu muc codebase/backend/)
"""
import os
import re
import csv
import sys
import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from services.pdf_service import extract_text_from_pdf  # noqa: E402
from services.vector_kb import CHROMA_PATH, COLLECTION_NAME  # noqa: E402

DATA_PACK = os.path.join(BACKEND_DIR, "..", "..", "data", "vlearn-pack")
TRANSCRIPT_DIR = os.path.join(DATA_PACK, "transcript")
SLIDES_DIR = os.path.join(DATA_PACK, "slides")
CHATLOG_CSV = os.path.join(DATA_PACK, "chatlog", "chat_history_anonymized_for_hackathon.csv")

# Mapping module theo knowledge_base.json.metadata.sources
MODULE_MAP = {
    "T01": "Day 2", "T02": "Day 2", "T03": "Day 2", "T05": "Day 2",
    "T04": "Day 1", "T06": "Day 1",
}
SEGMENTS_PER_CHUNK = 4


def chunk_transcripts():
    chunks = []
    if not os.path.isdir(TRANSCRIPT_DIR):
        print(f"[WARN] Khong tim thay {TRANSCRIPT_DIR}")
        return chunks

    for fname in sorted(os.listdir(TRANSCRIPT_DIR)):
        if not fname.endswith(".md") or fname == "README.md":
            continue
        path = os.path.join(TRANSCRIPT_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        # Tach theo **[Txx-NNN]** ... noi dung ... den truoc marker tiep theo
        pattern = re.compile(r"\*\*\[(T\d{2}-\d{3})\]\*\*\s*(.*?)(?=\*\*\[T\d{2}-\d{3}\]\*\*|\Z)", re.DOTALL)
        segments = [(m.group(1), m.group(2).strip()) for m in pattern.finditer(text)]

        for i in range(0, len(segments), SEGMENTS_PER_CHUNK):
            group = segments[i:i + SEGMENTS_PER_CHUNK]
            codes = [c for c, _ in group]
            body = "\n".join(t for _, t in group if t)

            # Bo qua chunk chi chua noi dung hanh chinh [Hoat dong lop: ...]
            stripped = re.sub(r"\[Hoạt động lớp:.*?\]", "", body, flags=re.DOTALL).strip()
            if len(stripped) < 40:
                continue

            doc_prefix = codes[0].split("-")[0]  # vd "T06"
            citation = f"{codes[0]}~{codes[-1]}" if len(codes) > 1 else codes[0]
            chunks.append({
                "id": f"vec-{codes[0]}",
                "text": stripped[:1200],
                "citation": f"[{citation}]",
                "source_label": f"Transcript {fname}",
                "module": MODULE_MAP.get(doc_prefix, "Không xác định"),
                "source": "transcript",
            })
    return chunks


def chunk_slides():
    chunks = []
    slide_map = {
        "d1-slide-hackathon.pdf": ("D1-slide", "Day 1"),
        "d2-slide-hackathon.pdf": ("D2-slide", "Day 2"),
    }
    if not os.path.isdir(SLIDES_DIR):
        print(f"[WARN] Khong tim thay {SLIDES_DIR}")
        return chunks

    for fname, (prefix, module) in slide_map.items():
        path = os.path.join(SLIDES_DIR, fname)
        if not os.path.exists(path):
            continue
        with open(path, "rb") as f:
            file_bytes = f.read()
        text, page_count = extract_text_from_pdf(file_bytes)

        pages = re.split(r"\[Trang (\d+)\]\n", text)
        # pages[0] la phan truoc trang dau (rong), sau do xen ke [so_trang, noi_dung, so_trang, noi_dung...]
        for i in range(1, len(pages), 2):
            page_num = pages[i]
            content = pages[i + 1].strip() if i + 1 < len(pages) else ""
            if len(content) < 40:
                continue
            chunks.append({
                "id": f"vec-{prefix}-p{page_num}",
                "text": content[:1200],
                "citation": f"[{prefix}-p{page_num}]",
                "source_label": f"Slide {fname} (trang {page_num})",
                "module": module,
                "source": "slide",
            })
    return chunks


def chunk_chatlog():
    chunks = []
    if not os.path.exists(CHATLOG_CSV):
        print(f"[WARN] Khong tim thay {CHATLOG_CSV}")
        return chunks

    with open(CHATLOG_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    by_turn = {}
    for row in rows:
        by_turn.setdefault(row["turn_id"], {})[row["role"]] = row

    count = 0
    for turn_id, pair in by_turn.items():
        tutor = pair.get("tutor")
        student = pair.get("student")
        if not tutor or not student:
            continue
        try:
            citations = json.loads(tutor["citations"]) if tutor["citations"] else []
        except (json.JSONDecodeError, TypeError):
            citations = []
        if not citations:
            continue  # chi lay cau tra loi tutor DA co can cu that

        text = f"Học viên hỏi: {student['content'][:400]}\nTutor trả lời: {tutor['content'][:600]}"
        chunks.append({
            "id": f"vec-chatlog-{turn_id}",
            "text": text,
            "citation": f"[Trang {','.join(str(c) for c in citations)}]",
            "source_label": f"Chatlog thật ({tutor['conversation_id']}/{turn_id})",
            "module": "Không xác định",
            "source": "chatlog",
        })
        count += 1
    return chunks


def main():
    transcript_chunks = chunk_transcripts()
    slide_chunks = chunk_slides()
    chatlog_chunks = chunk_chatlog()
    all_chunks = transcript_chunks + slide_chunks + chatlog_chunks

    print(f"Transcript chunks: {len(transcript_chunks)}")
    print(f"Slide chunks:      {len(slide_chunks)}")
    print(f"Chatlog chunks:    {len(chatlog_chunks)}")
    print(f"Tong:              {len(all_chunks)}")

    if not all_chunks:
        print("[ERROR] Khong sinh duoc chunk nao — kiem tra lai data/vlearn-pack/")
        return

    import chromadb
    from chromadb.utils import embedding_functions

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    ef = embedding_functions.DefaultEmbeddingFunction()
    collection = client.create_collection(name=COLLECTION_NAME, embedding_function=ef)

    collection.add(
        ids=[c["id"] for c in all_chunks],
        documents=[c["text"] for c in all_chunks],
        metadatas=[
            {
                "citation": c["citation"],
                "source_label": c["source_label"],
                "module": c["module"],
                "source": c["source"],
            }
            for c in all_chunks
        ],
    )
    print(f"[OK] Da index {collection.count()} chunk vao Chroma ({CHROMA_PATH})")


if __name__ == "__main__":
    main()
