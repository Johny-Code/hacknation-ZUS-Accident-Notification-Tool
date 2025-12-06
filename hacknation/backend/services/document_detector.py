"""
Document type detection service.
Detects whether uploaded document is EWYP form or Wyjaśnienia poszkodowanego.
"""
from pathlib import Path
from openai import OpenAI
import os
import base64
from io import BytesIO
from typing import Literal
from pdf2image import convert_from_path
from pydantic import BaseModel

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class DocumentTypeResult(BaseModel):
    """Result of document type detection."""
    document_type: Literal["EWYP", "WYJASNIENIA_POSZKODOWANEGO"]


DETECTION_PROMPT = """Look at the TOP of this document image. 
Your task is to identify the document type:

1. If you see "EWYP" - it's an EWYP form
2. If you see "Zapis wyjaśnień poszkodowanego" at the top - it's WYJASNIENIA_POSZKODOWANEGO form

Return ONLY the document type."""


def get_first_page_top_crop(pdf_path: Path) -> str:
    """
    Get the top portion of the first page as base64 image.
    We only need the top ~20% to detect the document type.
    """
    pages = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=1)
    
    if not pages:
        return ""
    
    first_page = pages[0]
    width, height = first_page.size
    
    # Crop top 25% of the page - enough to see the header
    top_crop = first_page.crop((0, 0, width, int(height * 0.25)))
    
    buffer = BytesIO()
    top_crop.save(buffer, format="JPEG", quality=80)
    buffer.seek(0)
    
    return base64.b64encode(buffer.read()).decode("utf-8")


def detect_document_type(pdf_path: Path) -> str:
    """
    Detect the type of document by looking at the top of the first page.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Document type: "EWYP", "WYJASNIENIA_POSZKODOWANEGO", or "UNKNOWN"
    """
    base64_image = get_first_page_top_crop(pdf_path)
    
    if not base64_image:
        return "UNKNOWN"
    
    response = client.responses.parse(
        model="gpt-5-nano-2025-08-07",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": DETECTION_PROMPT},
                    {"type": "input_image", "image_url": f"data:image/jpeg;base64,{base64_image}"}
                ]
            }
        ],
        text_format=DocumentTypeResult,
    )
    
    return response.output_parsed.document_type

