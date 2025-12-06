"""
PDF Filler for ZUS EWYP (Accident Notification) form.

This module takes data in the JSON schema format and fills the PDF form.
"""

from pypdf import PdfReader, PdfWriter
from datetime import datetime
from typing import Any
import json

from field_mapping import (
    FIELD_MAPPING,
    BOOLEAN_FIELD_MAPPING,
    DATE_FORMAT_PDF,
    DATE_FORMAT_INPUT,
)


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
    Convert ISO date (YYYY-MM-DD) to PDF format (DD-MM-YY).
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
    template_path: str,
    output_path: str,
    schema_data: dict,
    flatten_form: bool = False
) -> dict:
    """
    Fill the ZUS EWYP PDF form with data from JSON schema.
    
    Args:
        template_path: Path to the blank PDF template
        output_path: Path where filled PDF will be saved
        schema_data: Data conforming to the ZUS EWYP JSON schema
        flatten_form: If True, flatten the form (make fields non-editable)
        
    Returns:
        Dictionary with statistics about the filling process
    """
    # Prepare the data
    pdf_data = prepare_pdf_data(schema_data)
    
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
    
    # Write the output
    with open(output_path, "wb") as f:
        writer.write(f)
    
    return {
        "output_path": output_path,
        "fields_filled": filled_fields,
        "total_fields_in_data": len(pdf_data),
    }


def fill_pdf_from_json_file(
    template_path: str,
    json_path: str,
    output_path: str,
    flatten_form: bool = False
) -> dict:
    """
    Fill PDF from a JSON file.
    
    Args:
        template_path: Path to the blank PDF template
        json_path: Path to JSON file with schema data
        output_path: Path where filled PDF will be saved
        flatten_form: If True, flatten the form
        
    Returns:
        Dictionary with statistics about the filling process
    """
    with open(json_path, "r", encoding="utf-8") as f:
        schema_data = json.load(f)
    
    return fill_pdf(template_path, output_path, schema_data, flatten_form)


# =============================================================================
# CLI Interface
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fill ZUS EWYP PDF form from JSON data"
    )
    parser.add_argument(
        "--template", "-t",
        default="1.pdf",
        help="Path to PDF template (default: 1.pdf)"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to JSON file with form data"
    )
    parser.add_argument(
        "--output", "-o",
        default="filled_form.pdf",
        help="Path for output PDF (default: filled_form.pdf)"
    )
    parser.add_argument(
        "--flatten", "-f",
        action="store_true",
        help="Flatten form fields (make non-editable)"
    )
    
    args = parser.parse_args()
    
    result = fill_pdf_from_json_file(
        template_path=args.template,
        json_path=args.input,
        output_path=args.output,
        flatten_form=args.flatten
    )
    
    print(f"✅ PDF filled successfully!")
    print(f"   Output: {result['output_path']}")
    print(f"   Fields filled: {result['fields_filled']}")

