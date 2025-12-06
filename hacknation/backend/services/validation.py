import json
from pathlib import Path
from typing import Any, Dict, List

from jsonschema import Draft7Validator


FILLED_FORMS_DIR = Path(__file__).resolve().parents[1] / "filled_forms"


def _find_schema_path() -> Path:
    """
    Zwraca ścieżkę do pliku schema.json w katalogu backend.
    """
    # Ścieżka relatywna względem tego pliku: backend/services/validation.py
    # Schema jest w: backend/schema.json
    schema_path = Path(__file__).resolve().parent.parent / "schema.json"
    
    if schema_path.is_file():
        return schema_path
    
    raise FileNotFoundError(f"Nie znaleziono pliku schema.json w oczekiwanej lokalizacji: {schema_path}")


def _load_schema() -> Dict[str, Any]:
    schema_path = _find_schema_path()
    print(f"🔍 Loading schema from: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    # Debug: sprawdź wymagania dla daneOsobyKtoraZawiadamia
    required = schema.get("properties", {}).get("daneOsobyKtoraZawiadamia", {}).get("required", [])
    print(f"📋 Schema daneOsobyKtoraZawiadamia required fields: {required}")
    return schema


def _get_validator() -> Draft7Validator:
    # USUNIĘTO globalny cache - zawsze ładuj świeży walidator
    schema = _load_schema()
    return Draft7Validator(schema)


def _unwrap_value_fields(data: Any) -> Any:
    """
    Rekurencyjnie zamienia obiekty w stylu:
    {"value": "...", "annotation": "...", "parsed": true}
    na samą wartość value, aby dane pasowały do JSON Schema.
    """
    if isinstance(data, dict):
        # typowy wrapper z OCR/LLM
        keys = set(data.keys())
        if {"value", "parsed"}.issubset(keys):
            return data.get("value")

        return {k: _unwrap_value_fields(v) for k, v in data.items()}

    if isinstance(data, list):
        return [_unwrap_value_fields(item) for item in data]

    return data


def _remove_none_fields(data: Any) -> Any:
    """
    Rekurencyjnie usuwa pola z wartością None z obiektów i list.
    JSON Schema wymaga, aby pola były konkretnego typu lub całkowicie pominięte,
    nie akceptuje None dla pól zdefiniowanych jako string/object.
    """
    if isinstance(data, dict):
        return {
            k: _remove_none_fields(v)
            for k, v in data.items()
            if v is not None
        }
    
    if isinstance(data, list):
        return [_remove_none_fields(item) for item in data if item is not None]
    
    return data


def _get_latest_filled_form_file() -> Path:
    json_files = sorted(
        FILLED_FORMS_DIR.glob("*.json"),
        key=lambda p: p.name,
        reverse=True,
    )
    if not json_files:
        raise FileNotFoundError("Brak plików w katalogu filled_forms.")
    return json_files[0]


def validate_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Waliduje przekazane dane formularza względem schema.json.
    Używane np. bezpośrednio przy POST /form (przed zapisaniem do pliku).

    Zwraca słownik z kluczami:
    - success: bool
    - errors: lista błędów (pusta gdy brak błędów)
    """
    normalized_data = _unwrap_value_fields(data)
    # Usuń pola z wartością None przed walidacją
    # (JSON Schema nie akceptuje None dla pól zdefiniowanych jako string/object)
    cleaned_data = _remove_none_fields(normalized_data)
    validator = _get_validator()

    errors: List[Dict[str, Any]] = []
    for error in validator.iter_errors(cleaned_data):
        errors.append(
            {
                "path": list(error.path),
                "message": error.message,
            }
        )

    return {
        "success": len(errors) == 0,
        "errors": errors,
    }


def validate_latest_filled_form() -> Dict[str, Any]:
    """
    Wczytuje najnowszy plik z filled_forms, normalizuje dane
    (usuwa wraper value/annotation/parsed) i waliduje je wg schema.json.

    Zwraca słownik z kluczami:
    - success: bool
    - filename: nazwa pliku
    - errors: lista błędów (pusta gdy brak błędów)
    """
    latest_file = _get_latest_filled_form_file()

    with open(latest_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    base_result = validate_data(raw_data)

    return {
        "success": base_result["success"],
        "filename": latest_file.name,
        "errors": base_result["errors"],
    }


