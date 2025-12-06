import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter

from models import FormResponse, ZawiadomienieOWypadku
from services.validation import validate_data, validate_latest_filled_form

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
    form_dict = form_data.model_dump()
    validation = validate_data(form_dict)

    # Jeśli walidacja się nie powiedzie – NIE zapisujemy pliku
    if not validation["success"]:
        return FormResponse(
            success=False,
            message="Formularz zawiera błędy walidacji. Popraw zaznaczone pola.",
            data={
                "form": form_dict,
                "errors": validation["errors"],
            },
        )

    # Walidacja OK – dopiero teraz zapisujemy plik
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{timestamp}.json"
    filepath = FILLED_FORMS_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(form_dict, f, ensure_ascii=False, indent=2)

    return FormResponse(
        success=True,
        message=f"Zawiadomienie o wypadku saved as {filename}. Dane są poprawne.",
        data={
            "form": form_dict,
            "filename": filename,
            "errors": [],
        },
    )


@router.get("/form/validate-latest", response_model=FormResponse)
async def validate_latest_form():
    """
    Waliduje najnowszy zapisany plik z katalogu `filled_forms`
    względem `schema.json` (po znormalizowaniu pól typu value/annotation/parsed).

    Przeznaczone do wywołania z frontendu po kliknięciu „Wyślij”.
    """
    result = validate_latest_filled_form()

    if result["success"]:
        return FormResponse(
            success=True,
            message=f"Plik {result['filename']} jest poprawny.",
            data={"filename": result["filename"], "errors": []},
        )

    return FormResponse(
        success=False,
        message=f"Plik {result['filename']} zawiera błędy walidacji.",
        data={"filename": result["filename"], "errors": result["errors"]},
    )
