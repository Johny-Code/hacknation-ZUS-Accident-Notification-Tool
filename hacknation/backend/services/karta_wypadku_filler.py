"""
Karta Wypadku PDF Filler Service.

Uses PyMuPDF (fitz) for both filling and flattening to ensure:
- No blue background highlighting
- Dotted lines preserved
- Polish characters (ąćęłńóśźż) properly rendered
"""

import fitz  # PyMuPDF
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Path to the PDF template
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
KARTA_TEMPLATE = TEMPLATES_DIR / "karta_wypadku.pdf"

# Font with Polish character support
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_NAME = "dejavu"


def normalize_name(name: str) -> str:
    """Normalize field names to improve matching.

    - Uppercase
    - Remove all non-alphanumeric characters (underscores, spaces, etc.)
    """
    return "".join(ch for ch in str(name).upper() if ch.isalnum())


def fill_karta_wypadku(
    output_path: Path,
    data: Dict[str, Any],
    flatten: bool = True
) -> Dict[str, Any]:
    """
    Fill the Karta Wypadku PDF form with data.

    Args:
        output_path: Path where filled PDF will be saved
        data: Dictionary with field names and values to fill
        flatten: If True, flatten the form (make fields non-editable, draw text directly)

    Returns:
        Dictionary with statistics about the filling process
    """
    if not KARTA_TEMPLATE.exists():
        raise FileNotFoundError(f"Karta Wypadku template not found: {KARTA_TEMPLATE}")

    # Precompute normalized-name -> value map
    normalized_data = {
        normalize_name(k): str(v)
        for k, v in data.items()
        if v  # only non-empty values
    }

    logger.info(f"Opening PDF template: {KARTA_TEMPLATE}")
    doc = fitz.open(KARTA_TEMPLATE)

    # List all fields for debugging
    all_fields = []
    for page in doc:
        for w in page.widgets():
            if w.field_name:
                all_fields.append(w.field_name)

    logger.info(f"Found {len(all_fields)} form fields")

    # Fill fields
    filled_count = 0
    for page in doc:
        for w in page.widgets():
            field_name = w.field_name or ""
            norm_name = normalize_name(field_name)
            value = normalized_data.get(norm_name)

            if value:
                w.field_value = value
                w.text_font = "helv"
                w.update()
                filled_count += 1
                logger.debug(f"Filled {field_name} with {value[:40]}...")

    logger.info(f"Filled {filled_count} fields")

    if flatten:
        # Save intermediate filled PDF
        temp_path = output_path.with_suffix('.temp.pdf')
        doc.save(str(temp_path))
        doc.close()

        # Reopen for flattening
        doc_flat = fitz.open(str(temp_path))

        # Check if font file exists
        use_custom_font = os.path.exists(FONT_PATH)
        if use_custom_font:
            logger.info(f"Using font: {FONT_PATH}")
        else:
            logger.warning(f"Font {FONT_PATH} not found, falling back to default")

        for page in doc_flat:
            # Register the custom font for this page if available
            if use_custom_font:
                page.insert_font(fontname=FONT_NAME, fontfile=FONT_PATH)

            # Get all widgets on this page
            widgets = list(page.widgets())

            for w in widgets:
                field_name = w.field_name or ""
                norm_name = normalize_name(field_name)

                # Get value from our data or from the widget
                value = normalized_data.get(norm_name) or w.field_value

                if value:
                    rect = w.rect

                    # Use a smaller fontsize and ensure text fits
                    fontsize = 9

                    # Insert the text directly on the page
                    if use_custom_font:
                        text_result = page.insert_textbox(
                            rect,
                            str(value),
                            fontsize=fontsize,
                            fontname=FONT_NAME,
                            fontfile=FONT_PATH,
                            align=0,  # left-aligned
                            color=(0, 0, 0),  # black text
                        )

                        # If text didn't fit (negative result), try smaller font
                        if text_result < 0:
                            page.insert_textbox(
                                rect,
                                str(value),
                                fontsize=7,
                                fontname=FONT_NAME,
                                fontfile=FONT_PATH,
                                align=0,
                                color=(0, 0, 0),
                            )
                    else:
                        # Fallback to standard font
                        text_result = page.insert_textbox(
                            rect,
                            str(value),
                            fontsize=fontsize,
                            fontname="helv",
                            align=0,
                            color=(0, 0, 0),
                        )
                        if text_result < 0:
                            page.insert_textbox(
                                rect,
                                str(value),
                                fontsize=7,
                                fontname="helv",
                                align=0,
                                color=(0, 0, 0),
                            )

                # Delete the widget to flatten the form
                try:
                    page.delete_widget(w)
                except Exception:
                    pass

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc_flat.save(str(output_path))
        doc_flat.close()

        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()

        logger.info(f"Created flattened PDF: {output_path}")
    else:
        # Just save the filled (non-flattened) PDF
        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(output_path))
        doc.close()
        logger.info(f"Created filled PDF: {output_path}")

    return {
        "output_path": str(output_path),
        "fields_filled": filled_count,
        "total_fields": len(all_fields),
        "flattened": flatten,
    }


def generate_karta_wypadku_proposal(
    folder_path: Path,
    folder_name: str,
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a Karta Wypadku proposal PDF for a given PESEL folder.

    Args:
        folder_path: Path to the PESEL folder
        folder_name: Name of the folder (usually PESEL number)
        data: Dictionary with data to fill from AI analysis.
              If None, uses minimal placeholder data.

    Returns:
        Dictionary with success status and generated filename
    """
    # If no data provided, use minimal placeholders
    # In the new workflow, AI-generated data should always be provided
    if data is None:
        logger.warning("No AI-generated data provided, using minimal placeholders")
        data = {
            # Only set PESEL from folder name, rest should come from AI
            "VICTIMPESEL": folder_name,
            "CARDDATE": datetime.now().strftime("%d.%m.%Y"),
            "RECEIVEDDATE": datetime.now().strftime("%d.%m.%Y"),
        }
    else:
        # Ensure VICTIMPESEL is set from folder name if not provided
        if "VICTIMPESEL" not in data or not data.get("VICTIMPESEL"):
            data["VICTIMPESEL"] = folder_name
        
        # Add default dates if not provided
        today = datetime.now().strftime("%d.%m.%Y")
        if "CARDDATE" not in data or not data.get("CARDDATE"):
            data["CARDDATE"] = today
        if "RECEIVEDDATE" not in data or not data.get("RECEIVEDDATE"):
            data["RECEIVEDDATE"] = today

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Karta_Wypadku_Proposal_{timestamp}.pdf"
    output_path = folder_path / filename

    try:
        result = fill_karta_wypadku(output_path, data, flatten=True)
        return {
            "success": True,
            "filename": filename,
            "path": str(output_path),
            "fields_filled": result["fields_filled"],
        }
    except Exception as e:
        logger.error(f"Error generating Karta Wypadku: {e}")
        return {
            "success": False,
            "error": str(e)
        }

