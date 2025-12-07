"""
PDF Filler for ZUS EWYP (Accident Notification) form.

This module takes data in the JSON schema format and fills the PDF form.
"""

from pathlib import Path
from pypdf import PdfReader, PdfWriter
from datetime import datetime
from typing import Any, Optional
import json
import logging

from services.field_mapping import (
    FIELD_MAPPING,
    BOOLEAN_FIELD_MAPPING,
    DATE_FORMAT_PDF,
    DATE_FORMAT_INPUT,
)

logger = logging.getLogger(__name__)

# Path to the PDF template
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
DEFAULT_TEMPLATE = TEMPLATES_DIR / "ZUS_EWYP_template.pdf"


def flatten_dict(data: dict, parent_key: str = "", sep: str = ".") -> dict:
    """
    Flatten a nested dictionary into dot-notation keys.
    
    Example:
        {"a": {"b": 1}} -> {"a.b": 1}
    """
    items = []
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        
        if isinstance(value, dict):
            # Handle nested objects (but not dokumentTozsamosci which should be combined)
            if key == "dokumentTozsamosci":
                # Combine rodzaj and seriaINumer into single string
                rodzaj = value.get("rodzaj", "")
                seria = value.get("seriaINumer", "")
                combined = f"{rodzaj} {seria}".strip()
                items.append((new_key, combined))
            else:
                items.extend(flatten_dict(value, new_key, sep).items())
        elif isinstance(value, list):
            # Handle arrays (like witnesses or documents list)
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, f"{new_key}.{i}", sep).items())
                else:
                    items.append((f"{new_key}.{i}", item))
        else:
            items.append((new_key, value))
    
    return dict(items)


def format_date(date_str: str) -> str:
    """
    Convert ISO date (YYYY-MM-DD) to PDF format (DDMMYYYY).
    PDF fields have max 8 characters.
    """
    if not date_str:
        return ""
    try:
        date_obj = datetime.strptime(date_str, DATE_FORMAT_INPUT)
        return date_obj.strftime(DATE_FORMAT_PDF)
    except ValueError:
        # If already in different format, return as-is
        return date_str


def is_date_field(key: str) -> bool:
    """Check if a field is a date field based on its name."""
    date_indicators = ["data", "urodzenia", "wypadku", "zlozenia"]
    key_lower = key.lower()
    return any(indicator in key_lower for indicator in date_indicators)


def prepare_pdf_data(schema_data: dict) -> dict:
    """
    Transform JSON schema data into PDF field data.
    
    Args:
        schema_data: Data conforming to the ZUS EWYP JSON schema
        
    Returns:
        Dictionary mapping PDF field names to values
    """
    pdf_data = {}
    
    # Flatten the nested structure
    flat_data = flatten_dict(schema_data)
    
    # Process each field
    for schema_key, value in flat_data.items():
        if value is None:
            continue
            
        # Handle boolean fields (TAK/NIE checkboxes)
        if schema_key in BOOLEAN_FIELD_MAPPING:
            checkbox_mapping = BOOLEAN_FIELD_MAPPING[schema_key]
            if isinstance(value, bool):
                # Set the appropriate checkbox
                pdf_field = checkbox_mapping[value]
                pdf_data[pdf_field] = "/1"
            continue
        
        # Handle sposobKorespondencji enum (correspondence type checkboxes)
        if "sposobKorespondencji" in schema_key and not schema_key.endswith("sposobKorespondencji"):
            continue  # Skip the sub-keys, handled below
            
        if schema_key.endswith("sposobKorespondencji"):
            # Determine which page's checkboxes to use
            if "OsobyPoszkodowanej" in schema_key:
                page = "Page2[0]"
            else:
                page = "Page3[0]"
            
            checkbox_map = {
                "adres": f"topmostSubform[0].{page}.adres[0]",
                "poste_restante": f"topmostSubform[0].{page}.posterestante[0]",
                "skrytka_pocztowa": f"topmostSubform[0].{page}.skrytkapocztowa[0]",
                "przegrodka_pocztowa": f"topmostSubform[0].{page}.przegrodkapocztowa[0]",
            }
            if value in checkbox_map:
                pdf_data[checkbox_map[value]] = "/1"
            continue
        
        # Handle sposobOdbioruOdpowiedzi enum (response method checkboxes)
        if schema_key == "sposobOdbioruOdpowiedzi":
            checkbox_map = {
                "w_placowce_ZUS": "topmostSubform[0].Page6[0].wplacowce[0]",
                "poczta_na_adres_wskazany_we_wniosku": "topmostSubform[0].Page6[0].poczta[0]",
                "na_koncie_PUE_ZUS": "topmostSubform[0].Page6[0].PUE[0]",
            }
            if value in checkbox_map:
                pdf_data[checkbox_map[value]] = "/1"
            continue
        
        # Handle attachment checkboxes (zalaczniki)
        if schema_key.startswith("zalaczniki.") and isinstance(value, bool):
            attachment_checkboxes = {
                "zalaczniki.kartaInformacyjnaLubZaswiadczeniePierwszejPomocy": "topmostSubform[0].Page5[0].ZaznaczX1[0]",
                "zalaczniki.postanowienieProkuratury": "topmostSubform[0].Page5[0].ZaznaczX2[0]",
                "zalaczniki.dokumentyDotyczaceZgonu": "topmostSubform[0].Page5[0].ZaznaczX3[0]",
                "zalaczniki.dokumentyPotwierdzajacePrawoDoKartyWypadkuDlaInnejOsoby": "topmostSubform[0].Page6[0].ZaznaczX4[0]",
            }
            if schema_key in attachment_checkboxes and value:
                pdf_data[attachment_checkboxes[schema_key]] = "/1"
            continue
        
        # Look up the PDF field name from mapping
        if schema_key in FIELD_MAPPING:
            pdf_field = FIELD_MAPPING[schema_key]
            
            # Format dates
            if is_date_field(schema_key):
                value = format_date(str(value))
            
            pdf_data[pdf_field] = str(value)
    
    return pdf_data


def fill_pdf(
    output_path: Path,
    schema_data: dict,
    template_path: Optional[Path] = None,
    flatten_form: bool = False
) -> dict:
    """
    Fill the ZUS EWYP PDF form with data from JSON schema.
    
    Args:
        output_path: Path where filled PDF will be saved
        schema_data: Data conforming to the ZUS EWYP JSON schema
        template_path: Path to the blank PDF template (defaults to bundled template)
        flatten_form: If True, flatten the form (make fields non-editable)
        
    Returns:
        Dictionary with statistics about the filling process
    """
    if template_path is None:
        template_path = DEFAULT_TEMPLATE
    
    if not template_path.exists():
        raise FileNotFoundError(f"PDF template not found: {template_path}")
    
    # Prepare the data
    pdf_data = prepare_pdf_data(schema_data)
    
    logger.info(f"Filling PDF with {len(pdf_data)} fields")
    
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
    
    logger.info(f"PDF saved to {output_path}")
    
    return {
        "output_path": str(output_path),
        "fields_filled": filled_fields,
        "total_fields_in_data": len(pdf_data),
    }


def generate_filled_pdf(
    form_data: dict,
    output_dir: Path,
    filename_prefix: str = "EWYP"
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
    
    result = fill_pdf(output_path, form_data)
    
    return output_path

