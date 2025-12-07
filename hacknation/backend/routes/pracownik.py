from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from pathlib import Path
from typing import List, Optional
import os

from services.word_generator import generate_opinion_document
from services.karta_wypadku_filler import generate_karta_wypadku_proposal
from services.ai_analysis import (
    check_document_consistency,
    generate_opinion_data,
    generate_karta_wypadku_data,
    get_pdf_files_in_folder,
)

router = APIRouter(prefix="/pracownik", tags=["pracownik"])

# Directory for PESEL-based PDF storage
PDFS_DIR = Path(__file__).parent.parent / "pdfs"
PDFS_DIR.mkdir(exist_ok=True)


@router.get("/folders")
async def list_folders():
    """
    List all PESEL folders in the pdfs directory.
    Returns a list of folder names (PESEL-based folders).
    """
    try:
        folders = []
        for item in PDFS_DIR.iterdir():
            if item.is_dir():
                # Count PDFs and DOCXs in folder
                pdf_count = len(list(item.glob("*.pdf")))
                docx_count = len(list(item.glob("*.docx")))
                folders.append({
                    "name": item.name,
                    "type": "folder",
                    "pdf_count": pdf_count,
                    "docx_count": docx_count,
                    "total_count": pdf_count + docx_count
                })
        
        # Sort folders by name
        folders.sort(key=lambda x: x["name"])
        
        return {
            "success": True,
            "path": "/",
            "items": folders
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/folders/{folder_name}")
async def list_folder_contents(folder_name: str):
    """
    List contents of a specific PESEL folder.
    Returns a list of PDF and DOCX files in the folder.
    """
    folder_path = PDFS_DIR / folder_name
    
    if not folder_path.exists():
        raise HTTPException(status_code=404, detail="Folder not found")
    
    if not folder_path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a folder")
    
    try:
        items = []
        allowed_extensions = [".pdf", ".docx"]
        for item in folder_path.iterdir():
            if item.is_file() and item.suffix.lower() in allowed_extensions:
                file_type = "pdf" if item.suffix.lower() == ".pdf" else "docx"
                items.append({
                    "name": item.name,
                    "type": "file",
                    "file_type": file_type,
                    "size_bytes": item.stat().st_size,
                    "modified": item.stat().st_mtime
                })
        
        # Sort files by modification time (newest first)
        items.sort(key=lambda x: x["modified"], reverse=True)
        
        return {
            "success": True,
            "path": f"/{folder_name}",
            "folder_name": folder_name,
            "items": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/view/{folder_name}/{filename}")
async def view_pdf(folder_name: str, filename: str):
    """
    View a PDF file from a PESEL folder inline in the browser.
    """
    file_path = PDFS_DIR / folder_name / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    if file_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files can be viewed")
    
    # Read the PDF file
    with open(file_path, "rb") as f:
        pdf_content = f.read()
    
    # Return with Content-Disposition: inline to display in browser instead of downloading
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=\"{filename}\""
        }
    )


@router.post("/check-consistency/{folder_name}")
async def check_consistency(folder_name: str):
    """
    Check consistency between two PDF documents in a PESEL folder.
    
    Returns:
        - success: True if check completed
        - is_consistent: True if documents are consistent
        - inconsistencies: List of found inconsistencies
        - summary: Summary for the user
        - can_proceed: True if analysis can proceed (exactly 2 PDFs exist)
        - already_analyzed: True if more than 2 files exist (analysis already done)
    """
    folder_path = PDFS_DIR / folder_name
    
    if not folder_path.exists():
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Count PDF files
    pdf_files = list(folder_path.glob("*.pdf"))
    pdf_count = len(pdf_files)
    
    # Count generated files (DOCX or PDFs with specific names)
    docx_count = len(list(folder_path.glob("*.docx")))
    karta_count = len(list(folder_path.glob("Karta_Wypadku_*.pdf")))
    
    # Check if analysis was already performed
    if docx_count > 0 or karta_count > 0:
        return {
            "success": True,
            "can_proceed": False,
            "already_analyzed": True,
            "message": "Analiza AI została już przeprowadzona dla tego folderu. Znaleziono wygenerowane dokumenty.",
            "pdf_count": pdf_count,
            "generated_files_count": docx_count + karta_count
        }
    
    # Check if we have exactly 2 PDFs
    if pdf_count != 2:
        return {
            "success": True,
            "can_proceed": False,
            "already_analyzed": False,
            "message": f"Wymagane są dokładnie 2 dokumenty PDF (zawiadomienie o wypadku i wyjaśnienia poszkodowanego). Obecnie w folderze jest {pdf_count} PDF(ów).",
            "pdf_count": pdf_count
        }
    
    try:
        # Perform consistency check
        result = check_document_consistency(folder_path)
        
        return {
            "success": True,
            "can_proceed": True,
            "already_analyzed": False,
            "is_consistent": result.is_consistent,
            "inconsistencies": result.inconsistencies,
            "summary": result.summary,
            "pdf_count": pdf_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd podczas sprawdzania spójności: {str(e)}")


@router.post("/generate-documents/{folder_name}")
async def generate_documents(folder_name: str):
    """
    Generate AI-powered documents for a PESEL folder:
    1. Legal opinion document (Word)
    2. Karta Wypadku proposal (PDF)
    
    This endpoint should be called after consistency check confirmation.
    """
    folder_path = PDFS_DIR / folder_name
    
    if not folder_path.exists():
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Verify we have exactly 2 PDFs
    pdf_files = list(folder_path.glob("*.pdf"))
    if len(pdf_files) != 2:
        raise HTTPException(
            status_code=400, 
            detail=f"Wymagane są dokładnie 2 dokumenty PDF. Obecnie: {len(pdf_files)}"
        )
    
    generated_files = []
    errors = []
    
    try:
        # Generate opinion data using AI
        opinion_data = generate_opinion_data(folder_path)
        
        # Convert Pydantic model to dict for word generator
        opinion_context = {
            "case_number": f"Znak sprawy: {opinion_data.case_number or folder_name}/2025",
            "injured_person": opinion_data.injured_person,
            "issue_description": opinion_data.issue_description,
            "accident_date": opinion_data.accident_date,
            "conclusion": opinion_data.conclusion,
            "justification": opinion_data.justification,
            "specialist_name": opinion_data.specialist_name or "Starszy Specjalista ZUS",
            "specialist_signature_date": opinion_data.accident_date,
            "approbant_opinion": opinion_data.approbant_opinion or "",
            "approbant_date": "",
            "approbant_signature": "",
            "superapprobation_opinion": opinion_data.superapprobation_opinion or "",
            "superapprobation_date": "",
            "superapprobation_signature": "",
            "consultant_opinion": "",
            "consultant_date": "",
            "consultant_signature": "",
            "deputy_director_opinion": "",
            "deputy_director_date": "",
            "deputy_director_signature": "",
            "final_decision": "",
            "final_decision_date": "",
            "final_decision_signature": ""
        }
        
        # Generate opinion document
        opinion_result = generate_opinion_document(folder_path, folder_name, opinion_context)
        if opinion_result["success"]:
            generated_files.append(opinion_result["filename"])
        else:
            errors.append(f"Opinia prawna: {opinion_result.get('error', 'Nieznany błąd')}")
    except Exception as e:
        errors.append(f"Opinia prawna: {str(e)}")
    
    try:
        # Generate Karta Wypadku data using AI
        karta_data = generate_karta_wypadku_data(folder_path)
        
        # Convert Pydantic model to dict, excluding None values
        karta_dict = {k: v for k, v in karta_data.model_dump().items() if v is not None}
        
        # Generate Karta Wypadku PDF
        karta_result = generate_karta_wypadku_proposal(folder_path, folder_name, karta_dict)
        if karta_result["success"]:
            generated_files.append(karta_result["filename"])
        else:
            errors.append(f"Karta Wypadku: {karta_result.get('error', 'Nieznany błąd')}")
    except Exception as e:
        errors.append(f"Karta Wypadku: {str(e)}")
    
    if generated_files:
        message = f"Wygenerowano dokumenty: {', '.join(generated_files)}"
        if errors:
            message += f" (Błędy: {'; '.join(errors)})"
        return {
            "success": True,
            "message": message,
            "folder": folder_name,
            "generated_files": generated_files,
            "errors": errors if errors else None
        }
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"Błąd generowania dokumentów: {'; '.join(errors)}"
        )


@router.post("/analiza-ai/{folder_name}")
async def analyze_with_ai(folder_name: str):
    """
    DEPRECATED: Use /check-consistency and /generate-documents instead.
    
    This endpoint is kept for backwards compatibility but now returns
    a message directing to use the new two-step workflow.
    """
    return {
        "success": False,
        "message": "Ta funkcja została zaktualizowana. Użyj nowego przepływu: najpierw sprawdź spójność dokumentów (check-consistency), a następnie wygeneruj dokumenty (generate-documents).",
        "use_new_workflow": True
    }


@router.get("/download/{folder_name}/{filename}")
async def download_file(folder_name: str, filename: str):
    """
    Download a file (PDF or DOCX) from a PESEL folder.
    """
    file_path = PDFS_DIR / folder_name / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    # Determine media type based on extension
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        media_type = "application/pdf"
    elif suffix == ".docx":
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type
    )
