"""Text extraction from PDFs using PyPDF2 (no Tesseract required).

For images, returns empty string — the bill_service will route
those to Groq's vision model instead.
"""

import os
import PyPDF2


def extract_text(file_path: str) -> str:
    """Extract selectable text from a PDF file.

    For images (png/jpg/etc), returns empty string so the caller
    can fall back to the Groq vision model.
    """
    ext = os.path.splitext(file_path)[1].lower()

    # Images → no text extraction, will use vision model
    if ext in (".png", ".jpg", ".jpeg", ".bmp", ".tiff"):
        return ""

    # PDF → try PyPDF2 for selectable text
    if ext == ".pdf":
        text = ""
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as exc:
            print(f"PyPDF2 extraction failed: {exc}")
        return text.strip()

    raise ValueError(f"Unsupported file format: {ext}")
