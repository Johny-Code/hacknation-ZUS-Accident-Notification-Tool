"""
AI Analysis Service for accident documentation.

Provides LLM-based analysis for:
1. Consistency checking between accident report and victim explanation
2. Opinion document data generation
3. Karta Wypadku (Accident Card) data generation
"""

import os
import base64
from io import BytesIO
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from openai import OpenAI
from pdf2image import convert_from_path

from prompts.ai_analysis_prompts import (
    CONSISTENCY_CHECK_PROMPT,
    OPINION_GENERATION_PROMPT,
    KARTA_WYPADKU_GENERATION_PROMPT,
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# =============================================================================
# PYDANTIC MODELS FOR AI OUTPUTS
# =============================================================================

class ConsistencyCheckResult(BaseModel):
    """Result of consistency check between two documents."""
    is_consistent: bool = Field(
        description="True if documents are consistent, False if inconsistencies found"
    )
    inconsistencies: List[str] = Field(
        default_factory=list,
        description="List of detected inconsistencies between documents"
    )
    summary: str = Field(
        description="Brief summary of the analysis for ZUS employee"
    )


class OpinionData(BaseModel):
    """Data for generating legal opinion document."""
    # Basic case info
    case_number: Optional[str] = Field(
        None, description="Case number/identifier"
    )
    injured_person: str = Field(
        description="Full name of the injured person"
    )
    accident_date: str = Field(
        description="Date of the accident in DD-MM-YYYY format"
    )
    
    # Issue and conclusion
    issue_description: str = Field(
        description="Description of the legal issue to be resolved"
    )
    conclusion: str = Field(
        description="Proposed conclusion/recommendation"
    )
    justification: str = Field(
        description="Detailed legal justification for the conclusion"
    )
    
    # Specialist info
    specialist_name: Optional[str] = Field(
        None, description="Name of the specialist preparing the opinion"
    )
    
    # Approbant opinion
    approbant_opinion: Optional[str] = Field(
        None, description="Opinion of the person authorized for approval"
    )
    
    # Superapprobation opinion
    superapprobation_opinion: Optional[str] = Field(
        None, description="Opinion of the person authorized for super-approval"
    )


class KartaWypadkuData(BaseModel):
    """Data for filling Karta Wypadku (Accident Card) PDF.
    
    Fields can be left empty (None) if AI is unsure about the value.
    Use exactly these field names - they map to PDF form fields.
    """
    # Section I - Payer data (płatnik składek)
    PAYERNAME: Optional[str] = Field(
        None, description="Name of the contribution payer (employer)"
    )
    PAYERADDRESS: Optional[str] = Field(
        None, description="Address of the payer"
    )
    PAYERNIP: Optional[str] = Field(
        None, description="NIP number of the payer"
    )
    PAYERREGON: Optional[str] = Field(
        None, description="REGON number of the payer"
    )
    PAYERPESEL: Optional[str] = Field(
        None, description="PESEL of the payer (if individual)"
    )
    PAYERDOCUMENTTYPE: Optional[str] = Field(
        None, description="Type of identity document of the payer"
    )
    PAYERDOCUMENTTYPESERIES: Optional[str] = Field(
        None, description="Series of identity document"
    )
    PAYERDOCUMENTTYPENUMBER: Optional[str] = Field(
        None, description="Number of identity document"
    )
    
    # Section II - Victim data (poszkodowany)
    VICTIMNAME: str = Field(
        description="Full name of the victim (imię i nazwisko)"
    )
    VICTIMPESEL: str = Field(
        description="PESEL number of the victim"
    )
    VICTIMDOCUMENTTYPE: Optional[str] = Field(
        None, description="Type of victim's identity document"
    )
    VICTIMDOCUMENTTYPESERIES: Optional[str] = Field(
        None, description="Series of victim's identity document"
    )
    VICTIMDOCUMENTTYPENUMBER: Optional[str] = Field(
        None, description="Number of victim's identity document"
    )
    VICTIMDATEPLACEBIRTH: Optional[str] = Field(
        None, description="Date and place of birth (format: DD.MM.YYYY, City)"
    )
    VICTIMADDRESS: Optional[str] = Field(
        None, description="Full address of the victim"
    )
    INSURANCETITLE: Optional[str] = Field(
        None, description="Insurance title (tytuł ubezpieczenia)"
    )
    
    # Section III - Accident information
    REPORTDATEREPORTERNAME: Optional[str] = Field(
        None, description="Report date and reporter name (format: DD.MM.YYYY, Name)"
    )
    CIRCUMSTANCESINFORMATION: Optional[str] = Field(
        None, description="Description of accident circumstances"
    )
    WITNESS1: Optional[str] = Field(
        None, description="First witness name and address"
    )
    WITNESS2: Optional[str] = Field(
        None, description="Second witness name and address"
    )
    ACCIDENTIS: Optional[str] = Field(
        None, description="Classification of the accident"
    )
    VICTIMFAULT: Optional[str] = Field(
        None, description="Information about victim's fault"
    )
    VICTIMDRUNK: Optional[str] = Field(
        None, description="Information about victim's sobriety"
    )
    
    # Section IV - Other information
    VICTIMSFAMILYMEMBERNAME: Optional[str] = Field(
        None, description="Name of victim's family member (if applicable)"
    )
    VICTIMSFAMILYMEMBERDATE: Optional[str] = Field(
        None, description="Date (format: DD.MM.YYYY)"
    )
    CARDDATE: Optional[str] = Field(
        None, description="Date of card creation (format: DD.MM.YYYY)"
    )
    CARDISSUER: Optional[str] = Field(
        None, description="Card issuer (company/institution name)"
    )
    CARDISSUERNAME: Optional[str] = Field(
        None, description="Name of person issuing the card"
    )
    DIFFICULTIES: Optional[str] = Field(
        None, description="Difficulties in establishing circumstances"
    )
    RECEIVEDDATE: Optional[str] = Field(
        None, description="Date received (format: DD.MM.YYYY)"
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def pdf_pages_to_base64_images(pdf_path: Path, dpi: int = 150) -> List[str]:
    """
    Convert PDF pages to base64-encoded JPEG images.
    
    Args:
        pdf_path: Path to PDF file
        dpi: Resolution for conversion (lower = faster, 150 is good balance)
    
    Returns:
        List of base64-encoded image strings
    """
    pages = convert_from_path(pdf_path, dpi=dpi)
    
    base64_images = []
    for page in pages:
        buffer = BytesIO()
        page.save(buffer, format="JPEG", quality=80)
        buffer.seek(0)
        base64_image = base64.b64encode(buffer.read()).decode("utf-8")
        base64_images.append(base64_image)
    
    return base64_images


def get_pdf_files_in_folder(folder_path: Path) -> List[Path]:
    """Get all PDF files in a folder, sorted by name."""
    return sorted(folder_path.glob("*.pdf"))


# =============================================================================
# AI ANALYSIS FUNCTIONS
# =============================================================================

def check_document_consistency(folder_path: Path) -> ConsistencyCheckResult:
    """
    Check consistency between two PDF documents in a folder.
    
    Args:
        folder_path: Path to folder containing exactly 2 PDF files
    
    Returns:
        ConsistencyCheckResult with is_consistent flag and details
    
    Raises:
        ValueError: If folder doesn't contain exactly 2 PDFs
    """
    pdf_files = get_pdf_files_in_folder(folder_path)
    
    if len(pdf_files) != 2:
        raise ValueError(
            f"Expected exactly 2 PDF files, found {len(pdf_files)}"
        )
    
    # Convert both PDFs to images
    all_images = []
    for pdf_file in pdf_files:
        images = pdf_pages_to_base64_images(pdf_file)
        all_images.extend(images)
    
    # Build content for LLM
    content = []
    
    for i, base64_image in enumerate(all_images):
        content.append({
            "type": "input_image",
            "image_url": f"data:image/jpeg;base64,{base64_image}",
        })
    
    response = client.responses.parse(
        model="gpt-5-mini",
        input=[{"role": "system", "content": CONSISTENCY_CHECK_PROMPT}, {"role": "user", "content": content}],
        text_format=ConsistencyCheckResult,
    )
    
    return response.output_parsed


def generate_opinion_data(folder_path: Path) -> OpinionData:
    """
    Generate data for legal opinion document based on PDFs in folder.
    
    Args:
        folder_path: Path to folder containing PDF documents
    
    Returns:
        OpinionData with all fields for opinion document
    """
    pdf_files = get_pdf_files_in_folder(folder_path)
    
    # Convert PDFs to images
    all_images = []
    for pdf_file in pdf_files:
        images = pdf_pages_to_base64_images(pdf_file)
        all_images.extend(images)
    
    # Build content for LLM
    folder_name = folder_path.name
    today = datetime.now().strftime("%d-%m-%Y")
    
    content = []
    
    for base64_image in all_images:
        content.append({
            "type": "input_image",
            "image_url": f"data:image/jpeg;base64,{base64_image}",
        })
    
    response = client.responses.parse(
        model="gpt-5-mini",
        input=[{"role": "system", "content": OPINION_GENERATION_PROMPT}, {"role": "user", "content": content}],
        text_format=OpinionData,
    )
    
    return response.output_parsed


def generate_karta_wypadku_data(folder_path: Path) -> KartaWypadkuData:
    """
    Generate data for Karta Wypadku PDF based on PDFs in folder.
    
    Args:
        folder_path: Path to folder containing PDF documents
    
    Returns:
        KartaWypadkuData with fields to fill in the accident card
    """
    pdf_files = get_pdf_files_in_folder(folder_path)
    
    # Convert PDFs to images
    all_images = []
    for pdf_file in pdf_files:
        images = pdf_pages_to_base64_images(pdf_file)
        all_images.extend(images)
    
    # Build content for LLM
    folder_name = folder_path.name  # Format: {dataUrodzenia}_{dataWypadku}_N
    today = datetime.now().strftime("%d.%m.%Y")
    
    content = [
        {
            "type": "input_text",
            "text": f"{KARTA_WYPADKU_GENERATION_PROMPT}\n\n"
                   f"Nazwa folderu incydentu: {folder_name}\n"
                   f"Data dzisiejsza: {today}\n\n"
                   f"PESEL poszkodowanego powinien zostać wyodrębniony z dokumentów źródłowych.\n"
                   f"Poniżej znajdują się obrazy dokumentów źródłowych:",
        }
    ]
    
    for base64_image in all_images:
        content.append({
            "type": "input_image",
            "image_url": f"data:image/jpeg;base64,{base64_image}",
        })
    
    response = client.responses.parse(
        model="gpt-4o-mini",
        input=[{"role": "user", "content": content}],
        text_format=KartaWypadkuData,
    )
    
    return response.output_parsed

