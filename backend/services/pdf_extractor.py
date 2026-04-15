"""
Extrator de texto de documentos PDF usando PyMuPDF.
"""
import fitz
from backend.config import logger


def extract_text(pdf_bytes: bytes) -> dict:
    """
    Extrai texto e metadados de um PDF.

    Args:
        pdf_bytes: conteúdo binário do PDF

    Returns:
        dict com: raw_text, num_pages, metadata
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        pages.append({
            "page_number": i + 1,
            "text": text,
            "char_count": len(text)
        })

    raw_text = "\n".join([p["text"] for p in pages])
    num_pages = len(doc)

    # Metadados do PDF (título, autor, etc.)
    meta = doc.metadata or {}
    pdf_metadata = {
        "title": meta.get("title", ""),
        "author": meta.get("author", ""),
        "subject": meta.get("subject", ""),
        "creator": meta.get("creator", ""),
        "producer": meta.get("producer", ""),
        "creation_date": meta.get("creationDate", ""),
    }
    # Remove campos vazios
    pdf_metadata = {k: v for k, v in pdf_metadata.items() if v}

    doc.close()

    logger.info(f"📄 Extraído: {len(raw_text)} chars | {num_pages} páginas")

    return {
        "raw_text": raw_text,
        "num_pages": num_pages,
        "pages": pages,
        "pdf_metadata": pdf_metadata
    }
