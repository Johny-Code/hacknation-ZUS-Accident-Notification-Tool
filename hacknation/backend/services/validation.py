import json
import re
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from jsonschema import Draft7Validator


FILLED_FORMS_DIR = Path(__file__).resolve().parents[1] / "filled_forms"
SCHEMAS_DIR = Path(__file__).resolve().parents[1] / "schemas"


class SchemaType(str, Enum):
    """Typy schematów walidacji formularzy."""
    ZAWIADOMIENIE = "zawiadomienie"  # ZUS EWYP - Zawiadomienie o wypadku
    WYJASNIENIA = "wyjasnienia"       # Wyjaśnienia poszkodowanego


# Mapowanie nazw pól na polskie opisy (czytelne nazwy)
FIELD_NAME_TRANSLATIONS = {
    # Dane osobowe
    "imieNazwisko": "Imię i nazwisko",
    "dataUrodzenia": "Data urodzenia",
    "miejsceUrodzenia": "Miejsce urodzenia",
    "adresZamieszkania": "Adres zamieszkania",
    "zatrudnienie": "Zatrudnienie",
    "dokumentTozsamosci": "Dokument tożsamości",
    "pesel": "PESEL",
    "imie": "Imię",
    "nazwisko": "Nazwisko",
    "numerTelefonu": "Numer telefonu",
    
    # Informacje o wypadku
    "dataWypadku": "Data wypadku",
    "miejsceWypadku": "Miejsce wypadku",
    "godzinaWypadku": "Godzina wypadku",
    "planowanaGodzinaRozpoczeciaPracy": "Planowana godzina rozpoczęcia pracy",
    "planowanaGodzinaZakonczeniaPracy": "Planowana godzina zakończenia pracy",
    
    # Okoliczności wypadku
    "rodzajCzynnosciPrzedWypadkiem": "Rodzaj czynności przed wypadkiem",
    "opisOkolicznosciWypadku": "Opis okoliczności wypadku",
    "opisOkolicznosciMiejscaIPrzyczyn": "Opis okoliczności, miejsca i przyczyn",
    "rodzajDoznanychUrazow": "Rodzaj doznanych urazów",
    
    # Maszyny i urządzenia
    "czyWypadekPodczasObslugiMaszyn": "Czy wypadek podczas obsługi maszyn",
    "nazwaTypUrzadzenia": "Nazwa/typ urządzenia",
    "dataProdukcjiUrzadzenia": "Data produkcji urządzenia",
    "czyUrzadzenieSprawneIUzytkowanePrawidlowo": "Czy urządzenie sprawne i użytkowane prawidłowo",
    "wypadekPodczasObslugiMaszynLubUrzadzen": "Wypadek podczas obsługi maszyn lub urządzeń",
    "opisStanuMaszynyIUzytkowania": "Opis stanu maszyny i użytkowania",
    "maszynaPosiadaAtestLubDeklaracjeZgodnosci": "Maszyna posiada atest lub deklarację zgodności",
    "maszynaWpisanaDoEwidencjiSrodkowTrwalych": "Maszyna wpisana do ewidencji środków trwałych",
    
    # Zabezpieczenia
    "czyBylyZabezpieczenia": "Czy były zabezpieczenia",
    "rodzajZabezpieczen": "Rodzaj zabezpieczeń",
    "czySrodkiWlasciweISprawne": "Czy środki właściwe i sprawne",
    
    # Warunki pracy
    "czyAsekuracja": "Czy asekuracja",
    "czyObowiazekPracyPrzezDwieOsoby": "Czy obowiązek pracy przez dwie osoby",
    
    # BHP
    "czyPrzestrzeganoZasadBHP": "Czy przestrzegano zasad BHP",
    "czyPosiadamPrzygotowanieZawodowe": "Czy posiadam przygotowanie zawodowe",
    "czyOdbylemSzkolenieBHP": "Czy odbyłem szkolenie BHP",
    "czyPosiadamOceneRyzykaZawodowego": "Czy posiadam ocenę ryzyka zawodowego",
    "stosowaneSrodkiZmniejszajaceRyzyko": "Stosowane środki zmniejszające ryzyko",
    
    # Stan trzeźwości
    "czyWStanieNietrzezwosci": "Czy w stanie nietrzeźwości",
    "stanTrzezwosciBadany": "Stan trzeźwości badany",
    
    # Organy
    "czyOrganyPodejmowalyCzynnosci": "Czy organy podejmowały czynności",
    "organyISzczegoly": "Organy i szczegóły",
    "organProwadzacyPostepowanie": "Organ prowadzący postępowanie",
    
    # Pomoc medyczna
    "pierwszaPomocData": "Data pierwszej pomocy",
    "pierwszaPomocUdzielona": "Pierwsza pomoc udzielona",
    "nazwaPlacowkiZdrowia": "Nazwa placówki zdrowia",
    "placowkaUdzielajacaPierwszejPomocy": "Placówka udzielająca pierwszej pomocy",
    "okresIMiejsceHospitalizacji": "Okres i miejsce hospitalizacji",
    "rozpoznanyUraz": "Rozpoznany uraz",
    "niezdolnoscDoPracy": "Niezdolność do pracy",
    
    # Inne
    "czyNaZwolnieniuWLacuWypadku": "Czy na zwolnieniu w chwili wypadku",
    "dataPodpisania": "Data podpisania",
    "podpisPoszkodowanego": "Podpis poszkodowanego",
    "podpisPrzyjmujacego": "Podpis przyjmującego",
    
    # Adres
    "ulica": "Ulica",
    "numerDomu": "Numer domu",
    "numerLokalu": "Numer lokalu",
    "kodPocztowy": "Kod pocztowy",
    "miejscowosc": "Miejscowość",
    "nazwaPanstwa": "Nazwa państwa",
    
    # Sekcje formularza EWYP
    "daneOsobyPoszkodowanej": "Dane osoby poszkodowanej",
    "adresZamieszkaniaOsobyPoszkodowanej": "Adres zamieszkania osoby poszkodowanej",
    "informacjaOWypadku": "Informacja o wypadku",
    "daneSwiadkowWypadku": "Dane świadków wypadku",
    "zalaczniki": "Załączniki",
    "oswiadczenie": "Oświadczenie",
}


def _translate_field_name(field_name: str) -> str:
    """Tłumaczy nazwę pola na polski czytelny opis."""
    return FIELD_NAME_TRANSLATIONS.get(field_name, field_name)


def _translate_error_message(message: str) -> str:
    """
    Tłumaczy komunikat błędu z jsonschema na język polski.
    """
    # Pattern: 'field_name' is a required property
    required_match = re.match(r"'([^']+)' is a required property", message)
    if required_match:
        field_name = required_match.group(1)
        translated_name = _translate_field_name(field_name)
        return f"Pole '{translated_name}' jest wymagane"
    
    # Pattern: 'value' is not of type 'string'
    type_match = re.match(r"'([^']*)' is not of type '([^']+)'", message)
    if type_match:
        value = type_match.group(1)
        expected_type = type_match.group(2)
        type_translations = {
            "string": "tekst",
            "number": "liczba",
            "integer": "liczba całkowita",
            "boolean": "wartość logiczna (tak/nie)",
            "object": "obiekt",
            "array": "lista",
            "null": "pusta wartość",
        }
        polish_type = type_translations.get(expected_type, expected_type)
        return f"Wartość '{value}' ma nieprawidłowy typ - oczekiwano: {polish_type}"
    
    # Pattern: None is not of type 'string'
    none_type_match = re.match(r"None is not of type '([^']+)'", message)
    if none_type_match:
        expected_type = none_type_match.group(1)
        type_translations = {
            "string": "tekst",
            "number": "liczba",
            "integer": "liczba całkowita",
            "boolean": "wartość logiczna (tak/nie)",
            "object": "obiekt",
            "array": "lista",
        }
        polish_type = type_translations.get(expected_type, expected_type)
        return f"Pole nie może być puste - oczekiwano: {polish_type}"
    
    # Pattern: 'value' is not one of ['option1', 'option2']
    enum_match = re.match(r"'([^']*)' is not one of \[([^\]]+)\]", message)
    if enum_match:
        value = enum_match.group(1)
        options = enum_match.group(2)
        return f"Wartość '{value}' jest nieprawidłowa. Dozwolone wartości: {options}"
    
    # Pattern: 'value' does not match 'pattern'
    pattern_match = re.match(r"'([^']*)' does not match '([^']+)'", message)
    if pattern_match:
        value = pattern_match.group(1)
        return f"Wartość '{value}' ma nieprawidłowy format"
    
    # Pattern: 'value' is too short
    if "is too short" in message:
        return "Wartość jest za krótka"
    
    # Pattern: 'value' is too long
    if "is too long" in message:
        return "Wartość jest za długa"
    
    # Pattern: Additional properties are not allowed
    additional_match = re.match(r"Additional properties are not allowed \(([^)]+)\)", message)
    if additional_match:
        props = additional_match.group(1)
        return f"Niedozwolone dodatkowe pola: {props}"
    
    # Pattern: 'field' is a dependency of 'other_field'
    dependency_match = re.match(r"'([^']+)' is a dependency of '([^']+)'", message)
    if dependency_match:
        field1 = _translate_field_name(dependency_match.group(1))
        field2 = _translate_field_name(dependency_match.group(2))
        return f"Pole '{field1}' jest wymagane gdy pole '{field2}' jest wypełnione"
    
    # Pattern: minLength/maxLength
    if "is less than the minimum" in message:
        return "Wartość jest mniejsza niż minimalna dozwolona"
    
    if "is greater than the maximum" in message:
        return "Wartość jest większa niż maksymalna dozwolona"
    
    # Default - return original message if no translation found
    return message


# Mapowanie typów schematów na nazwy plików
SCHEMA_FILES = {
    SchemaType.ZAWIADOMIENIE: "schema_zawiadomienie.json",
    SchemaType.WYJASNIENIA: "schema_wyjasnienia.json",
}


def _find_schema_path(schema_type: SchemaType = SchemaType.ZAWIADOMIENIE) -> Path:
    """
    Zwraca ścieżkę do pliku schema dla danego typu formularza.
    
    Args:
        schema_type: Typ schematu (ZAWIADOMIENIE lub WYJASNIENIA)
    """
    schema_filename = SCHEMA_FILES.get(schema_type)
    if not schema_filename:
        raise ValueError(f"Nieznany typ schematu: {schema_type}")
    
    schema_path = SCHEMAS_DIR / schema_filename
    
    if schema_path.is_file():
        return schema_path
    
    raise FileNotFoundError(
        f"Nie znaleziono pliku {schema_filename} w katalogu schemas: {schema_path}"
    )


def _load_schema(schema_type: SchemaType = SchemaType.ZAWIADOMIENIE) -> Dict[str, Any]:
    """
    Ładuje schemat JSON dla danego typu formularza.
    
    Args:
        schema_type: Typ schematu (ZAWIADOMIENIE lub WYJASNIENIA)
    """
    schema_path = _find_schema_path(schema_type)
    print(f"🔍 Loading schema from: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    return schema


def _get_validator(schema_type: SchemaType = SchemaType.ZAWIADOMIENIE) -> Draft7Validator:
    """
    Zwraca walidator dla danego typu schematu.
    
    Args:
        schema_type: Typ schematu (ZAWIADOMIENIE lub WYJASNIENIA)
    """
    schema = _load_schema(schema_type)
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


def validate_data(
    data: Dict[str, Any],
    schema_type: SchemaType = SchemaType.ZAWIADOMIENIE
) -> Dict[str, Any]:
    """
    Waliduje przekazane dane formularza względem odpowiedniego schematu.
    Używane np. bezpośrednio przy POST /form (przed zapisaniem do pliku).

    Args:
        data: Dane formularza do walidacji
        schema_type: Typ schematu (ZAWIADOMIENIE lub WYJASNIENIA)

    Zwraca słownik z kluczami:
    - success: bool
    - errors: lista błędów (pusta gdy brak błędów)
    """
    normalized_data = _unwrap_value_fields(data)
    # Usuń pola z wartością None przed walidacją
    # (JSON Schema nie akceptuje None dla pól zdefiniowanych jako string/object)
    cleaned_data = _remove_none_fields(normalized_data)
    validator = _get_validator(schema_type)

    errors: List[Dict[str, Any]] = []
    for error in validator.iter_errors(cleaned_data):
        # Tłumacz komunikat błędu na polski
        translated_message = _translate_error_message(error.message)
        
        # Tłumacz ścieżkę pola na polski (dla lepszej czytelności)
        translated_path = [_translate_field_name(str(p)) for p in error.path]
        
        errors.append(
            {
                "path": list(error.path),  # Oryginalna ścieżka (do mapowania)
                "path_display": translated_path,  # Przetłumaczona ścieżka (do wyświetlania)
                "message": translated_message,
                "field_name": _translate_field_name(str(error.path[-1])) if error.path else "",
            }
        )

    return {
        "success": len(errors) == 0,
        "errors": errors,
    }


def validate_zawiadomienie(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Waliduje dane formularza 'Zawiadomienie o wypadku' (ZUS EWYP).
    
    Args:
        data: Dane formularza do walidacji
    """
    return validate_data(data, SchemaType.ZAWIADOMIENIE)


def validate_wyjasnienia(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Waliduje dane formularza 'Wyjaśnienia poszkodowanego'.
    
    Args:
        data: Dane formularza do walidacji
    """
    return validate_data(data, SchemaType.WYJASNIENIA)


def validate_latest_filled_form(
    schema_type: SchemaType = SchemaType.ZAWIADOMIENIE
) -> Dict[str, Any]:
    """
    Wczytuje najnowszy plik z filled_forms, normalizuje dane
    (usuwa wraper value/annotation/parsed) i waliduje je wg odpowiedniego schematu.

    Args:
        schema_type: Typ schematu (ZAWIADOMIENIE lub WYJASNIENIA)

    Zwraca słownik z kluczami:
    - success: bool
    - filename: nazwa pliku
    - errors: lista błędów (pusta gdy brak błędów)
    """
    latest_file = _get_latest_filled_form_file()

    with open(latest_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    base_result = validate_data(raw_data, schema_type)

    return {
        "success": base_result["success"],
        "filename": latest_file.name,
        "errors": base_result["errors"],
    }
