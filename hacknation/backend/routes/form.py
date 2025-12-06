import json
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from models import FormResponse, ZawiadomienieOWypadku
from services.validation import validate_data
from services.check_if_report_valid import check_if_report_valid
from services.pdf_filler import generate_filled_pdf

logger = logging.getLogger(__name__)

router = APIRouter(tags=["form"])

# Directory for storing filled forms (JSON and PDF)
FILLED_FORMS_DIR = Path(__file__).parent.parent / "filled_forms"
FILLED_FORMS_DIR.mkdir(exist_ok=True)


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

    # Step 5: All done - return success
    return FormResponse(
        success=True,
        message="Formularz został zweryfikowany pomyślnie i PDF został wygenerowany.",
        data={
            "valid": True,
            "comment": validity_check.comment,
            "fieldErrors": field_errors,
            "json_filename": json_filename,
            "pdf_filename": pdf_filename
        }
    )


@router.get("/form/download/{filename}")
async def download_filled_pdf(filename: str):
    """
    Download a generated PDF form.
    
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
        media_type="application/pdf"
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
