import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter
import logging
from models import FormResponse, ZawiadomienieOWypadku
from services.check_if_report_valid import check_if_report_valid

router = APIRouter(tags=["form"])

# Directory for storing filled forms
FILLED_FORMS_DIR = Path(__file__).parent.parent / "filled_forms"
FILLED_FORMS_DIR.mkdir(exist_ok=True)


@router.post("/form", response_model=FormResponse)
async def submit_zawiadomienie(form_data: ZawiadomienieOWypadku):
    """
    Zawiadomienie o wypadku (druk ZUS EWYP).

    Saves the form data as a JSON file with timestamp and returns success response.
    """
    # Generate timestamp filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{timestamp}.json"
    filepath = FILLED_FORMS_DIR / filename

    # Save form data to JSON file
    form_dict = form_data.model_dump()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(form_dict, f, ensure_ascii=False, indent=2)

    logging.info(form_dict["informacjaOWypadku"])
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
    
    response_data = {
        "valid": validity_check.valid,
        "comment": validity_check.comment,
        "fieldErrors": field_errors,
    }
    
    if validity_check.valid:
        return FormResponse(
            success=True,
            message="Formularz został zweryfikowany pomyślnie.",
            data=response_data
        )
    else:
        return FormResponse(
            success=False,
            message=validity_check.comment,
            data=response_data
        )
