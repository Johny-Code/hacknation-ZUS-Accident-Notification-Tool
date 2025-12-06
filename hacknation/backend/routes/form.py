import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from models import FormResponse, ZawiadomienieOWypadku
from services.validation import validate_data
from services.check_if_report_valid import check_if_report_valid
from services.pdf_filler import generate_filled_pdf

logger = logging.getLogger(__name__)

router = APIRouter(tags=["form"])

# Directory for storing filled forms (JSON and PDF)
FILLED_FORMS_DIR = Path(__file__).parent.parent / "filled_forms"
FILLED_FORMS_DIR.mkdir(exist_ok=True)

# Directory for PESEL-based PDF storage
PDFS_DIR = Path(__file__).parent.parent / "pdfs"
PDFS_DIR.mkdir(exist_ok=True)


class SavePdfRequest(BaseModel):
    """Request to save a PDF to the PESEL-based folder structure."""
    pesel: str
    pdf_filename: str


@router.post("/form", response_model=FormResponse)
async def submit_zawiadomienie(form_data: ZawiadomienieOWypadku):
    """
    Zawiadomienie o wypadku (druk ZUS EWYP).

    Flow:
    1. Validates the form data against JSON schema
    2. Saves the form as JSON
    3. Validates with LLM (check_if_report_valid)
    4. If LLM validation passes, generates a filled PDF
    5. Returns success response with the PDF filename
    """
    form_dict = form_data.model_dump()
    
    # Step 1: Schema validation
    validation = validate_data(form_dict)

    if not validation["success"]:
        return FormResponse(
            success=False,
            message="Formularz zawiera błędy walidacji. Popraw zaznaczone pola.",
            data={
                "form": form_dict,
                "errors": validation["errors"],
            },
        )

    # Step 2: Save to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    json_filename = f"{timestamp}.json"
    json_filepath = FILLED_FORMS_DIR / json_filename

    with open(json_filepath, "w", encoding="utf-8") as f:
        json.dump(form_dict, f, ensure_ascii=False, indent=2)

    logger.info(f"Form saved to {json_filename}")

    # Step 3: Validate with LLM
    logger.info(f"Validating form data with LLM: {form_dict['informacjaOWypadku']}")
    validity_check = check_if_report_valid(form_dict["informacjaOWypadku"])
    
    # Build field errors dict for frontend (only include fields that have warnings)
    field_errors = {}
    field_mapping = [
        "dataWypadku",
        "godzinaWypadku",
        "miejsceWypadku",
        "planowanaGodzinaRozpoczeciaPracy",
        "planowanaGodzinaZakonczeniaPracy",
        "rodzajDoznanychUrazow",
        "opisOkolicznosciMiejscaIPrzyczyn",
        "placowkaUdzielajacaPierwszejPomocy",
        "organProwadzacyPostepowanie",
        "opisStanuMaszynyIUzytkowania",
    ]
    
    for field in field_mapping:
        field_value = getattr(validity_check, field, None)
        if field_value:
            field_errors[field] = field_value
    
    # If LLM validation failed, return errors without generating PDF
    if not validity_check.valid:
        return FormResponse(
            success=False,
            message=validity_check.comment,
            data={
                "valid": False,
                "comment": validity_check.comment,
                "fieldErrors": field_errors,
                "json_filename": json_filename,
                "pdf_filename": None
            }
        )
    
    # Step 4: LLM validation passed - generate filled PDF
    try:
        pdf_path = generate_filled_pdf(
            form_data=form_dict,
            output_dir=FILLED_FORMS_DIR,
            filename_prefix=f"EWYP_{timestamp}"
        )
        pdf_filename = pdf_path.name
        logger.info(f"Generated PDF: {pdf_filename}")
    except FileNotFoundError as e:
        logger.error(f"PDF template not found: {e}")
        return FormResponse(
            success=True,
            message="Formularz zweryfikowany, ale generowanie PDF nie powiodło się: brak szablonu",
            data={
                "valid": True,
                "comment": validity_check.comment,
                "fieldErrors": field_errors,
                "json_filename": json_filename,
                "pdf_filename": None
            }
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return FormResponse(
            success=True,
            message=f"Formularz zweryfikowany, ale generowanie PDF nie powiodło się: {str(e)}",
            data={
                "valid": True,
                "comment": validity_check.comment,
                "fieldErrors": field_errors,
                "json_filename": json_filename,
                "pdf_filename": None
            }
        )

    # Step 5: Automatically save PDF to PESEL folder
    pesel = form_dict.get("daneOsobyPoszkodowanej", {}).get("pesel", "")
    pesel_folder_path = None
    
    if pesel and len(pesel) == 11 and pesel.isdigit():
        try:
            target_folder = get_pesel_folder(pesel)
            target_path = target_folder / pdf_filename
            shutil.copy2(pdf_path, target_path)
            pesel_folder_path = f"{target_folder.name}/{pdf_filename}"
            logger.info(f"PDF automatically saved to PESEL folder: {target_path}")
        except Exception as e:
            logger.error(f"Failed to save PDF to PESEL folder: {e}")
            # Continue anyway - the PDF is still in filled_forms
    
    # Step 6: All done - return success
    return FormResponse(
        success=True,
        message="Formularz został zweryfikowany pomyślnie i PDF został wygenerowany.",
        data={
            "valid": True,
            "comment": validity_check.comment,
            "fieldErrors": field_errors,
            "json_filename": json_filename,
            "pdf_filename": pdf_filename,
            "pesel_folder_path": pesel_folder_path
        }
    )


@router.get("/form/download/{filename}")
async def download_filled_pdf(filename: str):
    """
    Download a generated PDF form (force download).
    
    Args:
        filename: The PDF filename returned from the form submission
        
    Returns:
        The PDF file for download
    """
    # Security: only allow PDF files from the filled_forms directory
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    filepath = FILLED_FORMS_DIR / filename
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/form/view-filled/{filename}")
async def view_filled_pdf(filename: str):
    """
    View a PDF from filled_forms folder (inline display, no download).
    Fallback for when PESEL folder path is not available.
    
    Args:
        filename: The PDF filename
        
    Returns:
        The PDF file for inline viewing
    """
    # Security: only allow PDF files
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    filepath = FILLED_FORMS_DIR / filename
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    
    return FileResponse(
        path=filepath,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline",
            "Cache-Control": "no-cache"
        }
    )


@router.get("/form/view/{pesel_folder}/{filename}")
async def view_pdf_from_pesel_folder(pesel_folder: str, filename: str):
    """
    View a PDF from the PESEL folder (inline display, no download).
    
    Args:
        pesel_folder: The PESEL folder name (e.g., "90010112345_1")
        filename: The PDF filename
        
    Returns:
        The PDF file for inline viewing
    """
    # Security: only allow PDF files
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if ".." in pesel_folder or "/" in pesel_folder or "\\" in pesel_folder:
        raise HTTPException(status_code=400, detail="Invalid folder name")
    
    filepath = PDFS_DIR / pesel_folder / filename
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    
    # Return without filename parameter to ensure inline display
    return FileResponse(
        path=filepath,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline",
            "Cache-Control": "no-cache"
        }
    )


@router.get("/form/download-from-pesel/{pesel_folder}/{filename}")
async def download_pdf_from_pesel_folder(pesel_folder: str, filename: str):
    """
    Download a PDF from the PESEL folder.
    
    Args:
        pesel_folder: The PESEL folder name (e.g., "90010112345_1")
        filename: The PDF filename
        
    Returns:
        The PDF file for download
    """
    # Security: only allow PDF files
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if ".." in pesel_folder or "/" in pesel_folder or "\\" in pesel_folder:
        raise HTTPException(status_code=400, detail="Invalid folder name")
    
    filepath = PDFS_DIR / pesel_folder / filename
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/form/list")
async def list_filled_forms():
    """
    List all generated PDF forms.
    
    Returns:
        List of PDF filenames available for download
    """
    pdf_files = sorted(
        [f.name for f in FILLED_FORMS_DIR.glob("*.pdf")],
        reverse=True  # Most recent first
    )
    return {"files": pdf_files, "count": len(pdf_files)}


def get_pesel_folder(pesel: str) -> Path:
    """
    Get the appropriate folder for a given PESEL.
    
    Logic:
    - Look for existing folders named {PESEL}_N
    - If no folder exists, create {PESEL}_1
    - If the latest folder has less than 2 files, use it
    - Otherwise, create a new folder with incremented N
    
    Args:
        pesel: The PESEL number
        
    Returns:
        Path to the folder to use
    """
    # Find all existing folders for this PESEL
    existing_folders = sorted(
        [f for f in PDFS_DIR.iterdir() if f.is_dir() and f.name.startswith(f"{pesel}_")],
        key=lambda x: int(x.name.split("_")[-1]) if x.name.split("_")[-1].isdigit() else 0
    )
    
    if not existing_folders:
        # No folder exists, create the first one
        new_folder = PDFS_DIR / f"{pesel}_1"
        new_folder.mkdir(parents=True, exist_ok=True)
        return new_folder
    
    # Check the latest folder
    latest_folder = existing_folders[-1]
    files_in_folder = list(latest_folder.glob("*.pdf"))
    
    if len(files_in_folder) < 2:
        # Use the existing folder
        return latest_folder
    
    # Create a new folder with incremented number
    latest_num = int(latest_folder.name.split("_")[-1])
    new_folder = PDFS_DIR / f"{pesel}_{latest_num + 1}"
    new_folder.mkdir(parents=True, exist_ok=True)
    return new_folder


@router.post("/form/save-to-pesel")
async def save_pdf_to_pesel_folder(request: SavePdfRequest):
    """
    Save a generated PDF to the PESEL-based folder structure.
    
    The folder structure is: pdfs/{PESEL}_N/
    where N starts at 1 and increments when a folder has 2 files.
    
    Args:
        request: Contains pesel and pdf_filename
        
    Returns:
        Information about where the PDF was saved
    """
    # Validate PESEL format (basic check - 11 digits)
    if not request.pesel or len(request.pesel) != 11 or not request.pesel.isdigit():
        raise HTTPException(status_code=400, detail="Invalid PESEL format - must be 11 digits")
    
    # Find the source PDF
    source_pdf = FILLED_FORMS_DIR / request.pdf_filename
    if not source_pdf.exists():
        raise HTTPException(status_code=404, detail=f"PDF not found: {request.pdf_filename}")
    
    # Get the appropriate folder
    target_folder = get_pesel_folder(request.pesel)
    
    # Copy the PDF to the target folder
    target_path = target_folder / request.pdf_filename
    shutil.copy2(source_pdf, target_path)
    
    logger.info(f"PDF saved to PESEL folder: {target_path}")
    
    # Count files in the folder
    files_in_folder = list(target_folder.glob("*.pdf"))
    
    return {
        "success": True,
        "message": "PDF został zapisany w folderze osoby poszkodowanej",
        "folder": target_folder.name,
        "folder_path": str(target_folder.relative_to(PDFS_DIR.parent)),
        "files_in_folder": len(files_in_folder),
        "saved_as": request.pdf_filename
    }


@router.get("/form/pesel-folders/{pesel}")
async def get_pesel_folders(pesel: str):
    """
    Get all folders and files for a given PESEL.
    
    Args:
        pesel: The PESEL number
        
    Returns:
        List of folders and their contents for this PESEL
    """
    if not pesel or len(pesel) != 11 or not pesel.isdigit():
        raise HTTPException(status_code=400, detail="Invalid PESEL format")
    
    folders = []
    for folder in sorted(PDFS_DIR.iterdir()):
        if folder.is_dir() and folder.name.startswith(f"{pesel}_"):
            files = sorted([f.name for f in folder.glob("*.pdf")])
            folders.append({
                "folder_name": folder.name,
                "files": files,
                "file_count": len(files)
            })
    
    return {
        "pesel": pesel,
        "folders": folders,
        "total_folders": len(folders)
    }
