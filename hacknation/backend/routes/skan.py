from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from typing import Optional
import uuid

from models import ScanResponse
from config import get_user_upload_dir
from services.ocr import process_pdf_ocr

router = APIRouter(tags=["scan"])


@router.post("/skan", response_model=ScanResponse)
async def upload_scan(
    file: UploadFile = File(...),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-ID")
):
    """
    Upload a PDF document for OCR processing.
    Only PDF files are accepted.
    """
    # Validate file type - only PDFs allowed
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted. Please upload a PDF document."
        )
    
    # Validate file extension as additional check
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file extension. Only .pdf files are allowed."
        )
    
    # Generate user ID if not provided (for demo purposes)
    user_id = x_user_id or str(uuid.uuid4())
    
    # Get user-specific directory
    user_dir = get_user_upload_dir(user_id)
    
    # Generate unique filename to avoid collisions
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}_{file.filename}"
    file_path = user_dir / safe_filename
    
    # Read and save the file
    contents = await file.read()
    file_size = len(contents)
    
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Process the PDF with OCR (includes document type detection)
    ocr_result = process_pdf_ocr(file_path)
    
    return ScanResponse(
        success=True,
        message=f"PDF '{file.filename}' uploaded and processed successfully",
        ocr_result=ocr_result["data"],
        data={
            "filename": file.filename,
            "file_id": file_id,
            "user_id": user_id,
            "size_bytes": file_size,
            "stored_path": str(file_path),
            "document_type": ocr_result["document_type"]
        }
    )

