"""OCR text extraction from PDFs and images.

Supports:
  - PDF with selectable text (PyPDF2)
  - PDF with scanned pages (pdfplumber → pytesseract OCR fallback)
  - Images: PNG, JPG, JPEG, BMP, TIFF (pytesseract)
"""

import os

import pdfplumber
import pytesseract
from PIL import Image
import PyPDF2

from app.core.config import settings

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD


def extract_text(file_path: str) -> str:
    """Extract text from a PDF or image file.

    For PDFs: tries PyPDF2 first (selectable text), falls back to OCR.
    For images: uses pytesseract directly.

    Returns the extracted text as a string.
    """
    text = ""
    ext = os.path.splitext(file_path)[1].lower()

    # ── PDF ────────────────────────────────────────────────────
    if ext == ".pdf":
        # Try PyPDF2 (selectable text)
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as exc:
            print(f"PyPDF2 extraction failed: {exc}")

        # OCR fallback if no selectable text found
        if not text.strip():
            print("No selectable text found → Using OCR...")
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        pil_img = page.to_image(resolution=300).original
                        ocr_text = pytesseract.image_to_string(pil_img)
                        text += ocr_text + "\n"
            except Exception as exc:
                print(f"OCR extraction failed: {exc}")

    # ── Image ─────────────────────────────────────────────────
    elif ext in (".png", ".jpg", ".jpeg", ".bmp", ".tiff"):
        try:
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img)
        except Exception as exc:
            print(f"Image OCR failed: {exc}")

    else:
        raise ValueError(f"Unsupported file format: {ext}")

    return text.strip()
