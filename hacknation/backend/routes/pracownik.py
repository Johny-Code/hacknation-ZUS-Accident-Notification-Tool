from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from pathlib import Path
from typing import List, Optional
import os

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
                # Count PDFs in folder
                pdf_count = len(list(item.glob("*.pdf")))
                folders.append({
                    "name": item.name,
                    "type": "folder",
                    "pdf_count": pdf_count
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
    Returns a list of PDF files in the folder.
    """
    folder_path = PDFS_DIR / folder_name
    
    if not folder_path.exists():
        raise HTTPException(status_code=404, detail="Folder not found")
    
    if not folder_path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a folder")
    
    try:
        items = []
        for item in folder_path.iterdir():
            if item.is_file() and item.suffix.lower() == ".pdf":
                items.append({
                    "name": item.name,
                    "type": "file",
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


@router.post("/analiza-ai/{folder_name}")
async def analyze_with_ai(folder_name: str):
    """
    Trigger AI analysis for a PESEL folder.
    Currently returns a placeholder response.
    """
    folder_path = PDFS_DIR / folder_name
    
    if not folder_path.exists():
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Placeholder response - will be implemented later
    return {
        "success": True,
        "message": "Połączyłeś się do backendu :)",
        "folder": folder_name
    }

