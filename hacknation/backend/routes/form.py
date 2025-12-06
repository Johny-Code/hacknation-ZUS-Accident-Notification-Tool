import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter

from models import FormResponse, ZawiadomienieOWypadku

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

    return FormResponse(
        success=True,
        message=f"Zawiadomienie o wypadku saved as {filename}",
        data=form_dict
    )
