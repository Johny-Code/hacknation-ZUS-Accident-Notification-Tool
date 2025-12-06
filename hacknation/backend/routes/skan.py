from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from typing import Optional
import uuid
import json
import logging
from datetime import datetime
from pathlib import Path

from models import ScanResponse
from config import get_user_upload_dir
from services.ocr import process_pdf_ocr
from services.validation import validate_data
from services.check_if_report_valid import check_if_report_valid
from services.pdf_filler import generate_filled_pdf

logger = logging.getLogger(__name__)

router = APIRouter(tags=["scan"])

# Directory for storing filled forms (JSON and PDF) from scans
FILLED_FORMS_DIR = Path(__file__).parent.parent / "filled_forms"
FILLED_FORMS_DIR.mkdir(exist_ok=True)


@router.post("/skan", response_model=ScanResponse)
async def upload_scan(
    file: UploadFile = File(...),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-ID")
):
    """
    Upload a PDF document for OCR processing with validation.
    
    Flow:
    1. Validates file type (PDF only)
    2. Processes PDF with OCR
    3. Validates extracted data against JSON schema
    4. Performs LLM-driven validation on accident information
    5. If validation passes, generates filled PDF
    6. Returns result with any warnings/errors
    """
    # Validate file type - only PDFs allowed
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted. Please upload a PDF document."
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
    logger.info(f"Processing PDF with OCR: {file.filename}")
    ocr_result = process_pdf_ocr(file_path)
    ocr_result_json = ocr_result["data"]  # Extract JSON string from result
    
    # Parse OCR result to dict
    try:
        ocr_data = json.loads(ocr_result_json)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OCR result: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse OCR result: {str(e)}"
        )
    
    # Step 1: Schema validation (Basic validation)
    logger.info("Validating OCR data against schema")
    validation = validate_data(ocr_data)
    
    if not validation["success"]:
        logger.warning(f"Schema validation failed with {len(validation['errors'])} errors")
        
        # Build user-friendly error messages for each field
        field_error_messages = {}
        for error in validation["errors"]:
            field_path = ".".join(str(p) for p in error["path"])
            field_error_messages[field_path] = error["message"]
        
        return ScanResponse(
            success=False,
            message="Wstępna walidacja nie przebiegła pomyślnie. Dane z dokumentu są niekompletne lub niepoprawne.",
            ocr_result=ocr_result_json,
            data={
                "filename": file.filename,
                "file_id": file_id,
                "user_id": user_id,
                "size_bytes": file_size,
                "stored_path": str(file_path),
                "validationStage": "schema",
                "valid": False,
                "errors": validation["errors"],
                "fieldErrors": field_error_messages,
                "json_filename": None,
                "pdf_filename": None,
                "formData": ocr_data,  # Pre-filled data for form
                "userOptions": [
                    "reload_scan",  # Option 1: Upload scan again
                    "fill_form"     # Option 2: Go to form with pre-filled data
                ]
            }
        )
    else:
        # TODO Jan please handle this to wyświetlanie PDF
        pass


    # Schema validation passed
    logger.info("Schema validation passed - proceeding to LLM validation")
    
    # Step 2: Save to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    json_filename = f"scan_{timestamp}.json"
    json_filepath = FILLED_FORMS_DIR / json_filename
    
    with open(json_filepath, "w", encoding="utf-8") as f:
        json.dump(ocr_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"OCR data saved to {json_filename}")
    
    # Step 3: Validate with LLM (content validation)
    logger.info("Starting LLM content validation")
    field_errors = {}
    validity_check = None
    
    if "informacjaOWypadku" in ocr_data and ocr_data["informacjaOWypadku"]:
        logger.info("Validating OCR data with LLM")
        validity_check = check_if_report_valid(ocr_data["informacjaOWypadku"])
        
        # Build field errors dict for frontend (only include fields that have warnings)
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
        
        # If LLM validation failed, return with options (no PDF generation)
        if not validity_check.valid:
            logger.warning(f"LLM content validation failed: {validity_check.comment}")
            
            return ScanResponse(
                success=False,
                message=f"Walidacja merytoryczna nie przebiegła pomyślnie. {validity_check.comment}",
                ocr_result=ocr_result_json,
                data={
                    "filename": file.filename,
                    "file_id": file_id,
                    "user_id": user_id,
                    "size_bytes": file_size,
                    "stored_path": str(file_path),
                    "validationStage": "llm",
                    "valid": False,
                    "comment": validity_check.comment,
                    "fieldErrors": field_errors,
                    "json_filename": json_filename,
                    "pdf_filename": None,
                    "formData": ocr_data,  # Pre-filled data for form
                    "userOptions": [
                        "reload_scan",  # Option 1: Upload scan again
                        "fill_form"     # Option 2: Go to form with pre-filled data
                    ]
                }
            )
    
    # Step 4: All validation passed - generate filled PDF
    logger.info("All validations passed - generating PDF")
    try:
        pdf_path = generate_filled_pdf(
            form_data=ocr_data,
            output_dir=FILLED_FORMS_DIR,
            filename_prefix=f"EWYP_scan_{timestamp}"
        )
        pdf_filename = pdf_path.name
        logger.info(f"Generated PDF: {pdf_filename}")
    except FileNotFoundError as e:
        logger.error(f"PDF template not found: {e}")
        return ScanResponse(
            success=True,
            message="Wstępna walidacja przebiegła pomyślnie, dane są poprawnie wypełnione. Walidacja merytoryczna zakończona sukcesem, ale generowanie PDF nie powiodło się: brak szablonu",
            ocr_result=ocr_result_json,
            data={
                "filename": file.filename,
                "file_id": file_id,
                "user_id": user_id,
                "size_bytes": file_size,
                "stored_path": str(file_path),
                "validationStage": "completed",
                "valid": True,
                "comment": validity_check.comment if validity_check else "Wszystkie walidacje przebiegły pomyślnie",
                "fieldErrors": field_errors,
                "json_filename": json_filename,
                "pdf_filename": None
            }
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return ScanResponse(
            success=True,
            message=f"Wstępna walidacja przebiegła pomyślnie, dane są poprawnie wypełnione. Walidacja merytoryczna zakończona sukcesem, ale generowanie PDF nie powiodło się: {str(e)}",
            ocr_result=ocr_result_json,
            data={
                "filename": file.filename,
                "file_id": file_id,
                "user_id": user_id,
                "size_bytes": file_size,
                "stored_path": str(file_path),
                "validationStage": "completed",
                "valid": True,
                "comment": validity_check.comment if validity_check else "Wszystkie walidacje przebiegły pomyślnie",
                "fieldErrors": field_errors,
                "json_filename": json_filename,
                "pdf_filename": None
            }
        )
    
    # Step 5: Success - all done
    return ScanResponse(
        success=True,
        message="Wstępna walidacja przebiegła pomyślnie, dane są poprawnie wypełnione. Walidacja merytoryczna zakończona sukcesem. PDF został wygenerowany.",
        ocr_result=ocr_result_json,
        data={
            "filename": file.filename,
            "file_id": file_id,
            "user_id": user_id,
            "size_bytes": file_size,
            "stored_path": str(file_path),
            "validationStage": "completed",
            "valid": True,
            "comment": validity_check.comment if validity_check else "Wszystkie walidacje przebiegły pomyślnie",
            "fieldErrors": field_errors,
            "json_filename": json_filename,
            "pdf_filename": pdf_filename,
            "document_type": ocr_result["document_type"]
        }
    )

