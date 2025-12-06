from pathlib import Path
from openai import OpenAI
import os
import base64
from io import BytesIO
from pdf2image import convert_from_path
from prompts.ocr_prompt import OCR_SYSTEM_PROMPT


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def pdf_pages_to_base64_images(pdf_path: Path) -> list[str]:
    """
    Convert each page of a PDF to a base64-encoded JPEG image.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of base64-encoded image strings
    """
    # Convert PDF pages to PIL images
    pages = convert_from_path(pdf_path, dpi=200)
    
    base64_images = []
    for page in pages:
        # Convert PIL image to bytes
        buffer = BytesIO()
        page.save(buffer, format="JPEG", quality=85)
        buffer.seek(0)
        
        # Encode to base64
        base64_image = base64.b64encode(buffer.read()).decode("utf-8")
        base64_images.append(base64_image)
    
    return base64_images


def process_pdf_ocr(pdf_path: Path) -> str:
    """
    Process a PDF file and perform OCR to extract text using OpenAI Vision.
    
    Args:
        pdf_path: Path to the uploaded PDF file
        
    Returns:
        Extracted text from the PDF
    """
    # Convert PDF pages to base64 images
    base64_images = pdf_pages_to_base64_images(pdf_path)
    
    # Build content list with all page images
    content = [{"type": "input_text", "text": "Extract all text from these document pages:"}]
    
    for i, base64_image in enumerate(base64_images):
        content.append({
            "type": "input_image",
            "image_url": f"data:image/jpeg;base64,{base64_image}",
        })
    
    messages = [
        {"role": "system", "content": OCR_SYSTEM_PROMPT},
        {"role": "user", "content": content}
    ]
    
    response = client.responses.create(
        input=messages,
        model="gpt-5-nano-2025-08-07"
    )
    
    return response.output_text
