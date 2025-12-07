"""
PDF Filler for 'Wyjaśnienia poszkodowanego' (Victim's Explanation) form.

This module takes data in the JSON schema format and fills the PDF form.
"""

from pathlib import Path
from pypdf import PdfReader, PdfWriter
from datetime import datetime
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

# Path to the PDF template
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
WYJASNIENIA_TEMPLATE = TEMPLATES_DIR / "wyjasnienia_template.pdf"

# =============================================================================
# FIELD MAPPING: JSON Schema Path -> PDF Field Name
# =============================================================================
# 
# PDF Template Fields:
#   imieNazwisko, dataUrodzenia, miejsceUrodzenia, adresZamieszkania,
#   czynnosciPrzedWypadkiem, zatrudnienie, dokumentTozsamosci, 
#   dataWypadkuGlowne, dataWypadku, miejsceWypadku, godzinaWypadku, 
#   planowanaGodzinaRozpoczeciaPracy, planowanaGodzinaZakonczeniaPracy, 
#   opisOkolicznosciWypadku, obslugaMaszynTakNie, nazwaTypUrzadzenia, 
#   dataProdukcjiUrzadzenia, czyUrzadzenieSprawne, zabezpieczeniaTakNie, 
#   rodzajZabezpieczen, zabezpieczeniaSprawnosc, asekuracjaTakNie, 
#   obowiazekDwieOsoby, bhpPrzestrzeganie, przygotowanieZawodowe, 
#   szkolenieBhp, ocenaRyzyka, stosowaneSrodkiRyzyko, stanNietrzezwosci, 
#   organyPanstwowe, organyKontroli, pierwszaPomocData, placowkaZdrowia, 
#   hospitalizacja, rozpoznanyUraz, niezdolnoscDoPracy, zwolnienieLekarskie, 
#   dataPodpisania
#
# Field mapping:
#   - adresZamieszkania -> adresZamieszkania (address field)
#   - rodzajCzynnosciPrzedWypadkiem -> czynnosciPrzedWypadkiem (activities before accident)

WYJASNIENIA_FIELD_MAPPING = {
    # Personal data
    "imieNazwisko": "imieNazwisko",
    "dataUrodzenia": "dataUrodzenia",
    "miejsceUrodzenia": "miejsceUrodzenia",
    "adresZamieszkania": "adresZamieszkania",
    "zatrudnienie": "zatrudnienie",
    "dokumentTozsamosci": "dokumentTozsamosci",
    
    # Accident data - header (shown at top with "w dniu ...")
    "dataWypadku": "dataWypadkuGlowne",
    
    # Accident details - Section 1 (Data, miejsce, godzina wypadku)
    "dataWypadku_sekcja": "dataWypadku",  # Section 1 date field
    "miejsceWypadku": "miejsceWypadku",
    "godzinaWypadku": "godzinaWypadku",
    
    # Section 2 - Work hours and activities before accident
    "planowanaGodzinaRozpoczeciaPracy": "planowanaGodzinaRozpoczeciaPracy",
    "planowanaGodzinaZakonczeniaPracy": "planowanaGodzinaZakonczeniaPracy",
    "rodzajCzynnosciPrzedWypadkiem": "czynnosciPrzedWypadkiem",
    
    # Section 3 - Circumstances
    "opisOkolicznosciWypadku": "opisOkolicznosciWypadku",
    
    # Section 4 - Machinery
    "nazwaTypUrzadzenia": "nazwaTypUrzadzenia",
    "dataProdukcjiUrzadzenia": "dataProdukcjiUrzadzenia",
    "czyUrzadzenieSprawneIUzytkowanePrawidlowo": "czyUrzadzenieSprawne",
    
    # Section 5 - Safety equipment
    "rodzajZabezpieczen": "rodzajZabezpieczen",
    
    # Section 11 - Risk measures
    "stosowaneSrodkiZmniejszajaceRyzyko": "stosowaneSrodkiRyzyko",
    
    # Section 13 - Government authorities
    "organyISzczegoly": "organyKontroli",
    
    # Section 14 - First aid
    "pierwszaPomocData": "pierwszaPomocData",
    "nazwaPlacowkiZdrowia": "placowkaZdrowia",
    "okresIMiejsceHospitalizacji": "hospitalizacja",
    "rozpoznanyUraz": "rozpoznanyUraz",
    
    # Section 15 - Incapacity
    "niezdolnoscDoPracy": "niezdolnoscDoPracy",
    
    # Date of signing
    "dataPodpisania": "dataPodpisania",
}

# =============================================================================
# BOOLEAN FIELD MAPPING: Maps boolean fields to TAK/NIE text
# =============================================================================

WYJASNIENIA_BOOLEAN_FIELDS = {
    "czyWypadekPodczasObslugiMaszyn": "obslugaMaszynTakNie",
    "czyBylyZabezpieczenia": "zabezpieczeniaTakNie",
    "czySrodkiWlasciweISprawne": "zabezpieczeniaSprawnosc",
    "czyAsekuracja": "asekuracjaTakNie",
    "czyObowiazekPracyPrzezDwieOsoby": "obowiazekDwieOsoby",
    "czyPrzestrzeganoZasadBHP": "bhpPrzestrzeganie",
    "czyPosiadamPrzygotowanieZawodowe": "przygotowanieZawodowe",
    "czyOdbylemSzkolenieBHP": "szkolenieBhp",
    "czyPosiadamOceneRyzykaZawodowego": "ocenaRyzyka",
    "czyWStanieNietrzezwosci": "stanNietrzezwosci",
    "czyOrganyPodejmowalyCzynnosci": "organyPanstwowe",
    "czyNaZwolnieniuWLacuWypadku": "zwolnienieLekarskie",
}

# =============================================================================
# ENUM FIELD MAPPING
# =============================================================================

STAN_TRZEZWOSCI_MAPPING = {
    "badany_przez_policje": "badany przez policję",
    "badany_podczas_pierwszej_pomocy": "badany podczas udzielania pierwszej pomocy",
    "nie_badany": "nie badany",
}


def format_date(date_str: str) -> str:
    """
    Convert ISO date (YYYY-MM-DD) to Polish format (DD.MM.YYYY).
    """
    if not date_str:
        return ""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d.%m.%Y")
    except ValueError:
        # If already in different format, return as-is
        return date_str


def bool_to_tak_nie(value: bool) -> str:
    """Convert boolean to TAK/NIE string."""
    return "TAK" if value else "NIE"


def prepare_wyjasnienia_pdf_data(schema_data: dict) -> dict:
    """
    Transform JSON schema data into PDF field data.
    
    Args:
        schema_data: Data conforming to the Wyjaśnienia poszkodowanego JSON schema
        
    Returns:
        Dictionary mapping PDF field names to values
    """
    pdf_data = {}
    
    # Process regular text fields
    for schema_key, pdf_field in WYJASNIENIA_FIELD_MAPPING.items():
        # Handle special case for dataWypadku which fills two fields
        if schema_key == "dataWypadku":
            value = schema_data.get("dataWypadku", "")
            if value:
                formatted_date = format_date(str(value))
                pdf_data["dataWypadkuGlowne"] = formatted_date
                pdf_data["dataWypadku"] = formatted_date
            continue
        
        # Skip the duplicate key
        if schema_key == "dataWypadku_sekcja":
            continue
        
        value = schema_data.get(schema_key)
        if value is not None:
            # Format dates
            if "data" in schema_key.lower() or "urodzenia" in schema_key.lower():
                value = format_date(str(value))
            pdf_data[pdf_field] = str(value)
    
    # Process boolean fields
    for schema_key, pdf_field in WYJASNIENIA_BOOLEAN_FIELDS.items():
        value = schema_data.get(schema_key)
        if value is not None:
            pdf_data[pdf_field] = bool_to_tak_nie(value)
    
    # Process enum field for sobriety status
    stan_trzezwosci = schema_data.get("stanTrzezwosciBadany")
    if stan_trzezwosci and stan_trzezwosci in STAN_TRZEZWOSCI_MAPPING:
        # Append the sobriety status to the existing stanNietrzezwosci field
        existing = pdf_data.get("stanNietrzezwosci", "")
        if existing:
            pdf_data["stanNietrzezwosci"] = f"{existing} ({STAN_TRZEZWOSCI_MAPPING[stan_trzezwosci]})"
        else:
            pdf_data["stanNietrzezwosci"] = STAN_TRZEZWOSCI_MAPPING[stan_trzezwosci]
    
    return pdf_data


def fill_wyjasnienia_pdf(
    output_path: Path,
    schema_data: dict,
    template_path: Optional[Path] = None,
    flatten_form: bool = False
) -> dict:
    """
    Fill the Wyjaśnienia poszkodowanego PDF form with data from JSON schema.
    
    Args:
        output_path: Path where filled PDF will be saved
        schema_data: Data conforming to the Wyjaśnienia JSON schema
        template_path: Path to the blank PDF template (defaults to bundled template)
        flatten_form: If True, flatten the form (make fields non-editable)
        
    Returns:
        Dictionary with statistics about the filling process
    """
    if template_path is None:
        template_path = WYJASNIENIA_TEMPLATE
    
    if not template_path.exists():
        raise FileNotFoundError(f"PDF template not found: {template_path}")
    
    # Prepare the data
    pdf_data = prepare_wyjasnienia_pdf_data(schema_data)
    
    logger.info(f"Filling Wyjaśnienia PDF with {len(pdf_data)} fields")
    logger.debug(f"PDF data: {pdf_data}")
    
    # Read the template
    reader = PdfReader(template_path)
    writer = PdfWriter(clone_from=reader)
    
    # Fill all pages
    filled_fields = 0
    for page in writer.pages:
        writer.update_page_form_field_values(page, pdf_data)
    
    # Count how many fields were actually filled
    for field_name in pdf_data:
        if pdf_data[field_name]:
            filled_fields += 1
    
    # Optionally flatten the form
    if flatten_form:
        for page in writer.pages:
            for annot in page.get("/Annots", []):
                annot_obj = annot.get_object()
                if annot_obj.get("/Subtype") == "/Widget":
                    annot_obj["/Ff"] = 1  # Read-only flag
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the output
    with open(output_path, "wb") as f:
        writer.write(f)
    
    logger.info(f"Wyjaśnienia PDF saved to {output_path}")
    
    return {
        "output_path": str(output_path),
        "fields_filled": filled_fields,
        "total_fields_in_data": len(pdf_data),
    }


def generate_wyjasnienia_pdf(
    form_data: dict,
    output_dir: Path,
    filename_prefix: str = "WYJASNIENIA"
) -> Path:
    """
    Generate a filled PDF from form data.
    
    This is the main entry point for the form submission flow.
    
    Args:
        form_data: The validated form data (dict from Pydantic model)
        output_dir: Directory where the PDF will be saved
        filename_prefix: Prefix for the generated filename
        
    Returns:
        Path to the generated PDF file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_filename = f"{filename_prefix}_{timestamp}.pdf"
    output_path = output_dir / output_filename
    
    result = fill_wyjasnienia_pdf(output_path, form_data)
    
    return output_path

