from pathlib import Path
from openai import OpenAI
import os
import base64
from io import BytesIO
from typing import Optional, Literal
from pdf2image import convert_from_path
from pydantic import BaseModel
from prompts.ocr_prompt import OCR_SYSTEM_PROMPT

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class DokumentTozsamosci(BaseModel):
    rodzaj: Optional[str] = None
    seriaINumer: Optional[str] = None


class DaneOsobyPoszkodowanej(BaseModel):
    pesel: Optional[str] = None
    dokumentTozsamosci: Optional[DokumentTozsamosci] = None
    imie: str
    nazwisko: str
    dataUrodzenia: Optional[str] = None
    miejsceUrodzenia: Optional[str] = None
    numerTelefonu: Optional[str] = None


class AdresZamieszkania(BaseModel):
    ulica: Optional[str] = None
    numerDomu: Optional[str] = None
    numerLokalu: Optional[str] = None
    kodPocztowy: Optional[str] = None
    miejscowosc: Optional[str] = None
    nazwaPanstwa: Optional[str] = None


class AdresPolski(BaseModel):
    ulica: Optional[str] = None
    numerDomu: Optional[str] = None
    numerLokalu: Optional[str] = None
    kodPocztowy: Optional[str] = None
    miejscowosc: Optional[str] = None


class AdresDoKorespondencji(BaseModel):
    sposobKorespondencji: Optional[Literal["adres", "poste_restante", "skrytka_pocztowa", "przegrodka_pocztowa"]] = None
    ulica: Optional[str] = None
    numerDomu: Optional[str] = None
    numerLokalu: Optional[str] = None
    kodPocztowy: Optional[str] = None
    miejscowosc: Optional[str] = None
    nazwaPanstwa: Optional[str] = None


class AdresDzialalnosci(BaseModel):
    ulica: Optional[str] = None
    numerDomu: Optional[str] = None
    numerLokalu: Optional[str] = None
    kodPocztowy: Optional[str] = None
    miejscowosc: Optional[str] = None
    numerTelefonu: Optional[str] = None


class DaneOsobyKtoraZawiadamia(BaseModel):
    jestPoszkodowanym: Optional[bool] = None
    pesel: Optional[str] = None
    dokumentTozsamosci: Optional[DokumentTozsamosci] = None
    imie: Optional[str] = None
    nazwisko: Optional[str] = None
    dataUrodzenia: Optional[str] = None
    numerTelefonu: Optional[str] = None


class InformacjaOWypadku(BaseModel):
    dataWypadku: str
    godzinaWypadku: Optional[str] = None
    miejsceWypadku: str
    planowanaGodzinaRozpoczeciaPracy: Optional[str] = None
    planowanaGodzinaZakonczeniaPracy: Optional[str] = None
    rodzajDoznanychUrazow: Optional[str] = None
    opisOkolicznosciMiejscaIPrzyczyn: Optional[str] = None
    pierwszaPomocUdzielona: Optional[bool] = None
    placowkaUdzielajacaPierwszejPomocy: Optional[str] = None
    organProwadzacyPostepowanie: Optional[str] = None
    wypadekPodczasObslugiMaszynLubUrzadzen: Optional[bool] = None
    opisStanuMaszynyIUzytkowania: Optional[str] = None
    maszynaPosiadaAtestLubDeklaracjeZgodnosci: Optional[bool] = None
    maszynaWpisanaDoEwidencjiSrodkowTrwalych: Optional[bool] = None


class AdresSwiadka(BaseModel):
    ulica: Optional[str] = None
    numerDomu: Optional[str] = None
    numerLokalu: Optional[str] = None
    kodPocztowy: Optional[str] = None
    miejscowosc: Optional[str] = None
    nazwaPanstwa: Optional[str] = None


class Swiadek(BaseModel):
    imie: str
    nazwisko: str
    adres: Optional[AdresSwiadka] = None


class Zalaczniki(BaseModel):
    kartaInformacyjnaLubZaswiadczeniePierwszejPomocy: Optional[bool] = None
    postanowienieProkuratury: Optional[bool] = None
    dokumentyDotyczaceZgonu: Optional[bool] = None
    dokumentyPotwierdzajacePrawoDoKartyWypadkuDlaInnejOsoby: Optional[bool] = None
    inneDokumentyOpis: Optional[str] = None


class DokumentyDoDostarczeniaPozniej(BaseModel):
    dataDo: Optional[str] = None
    listaDokumentow: Optional[list[str]] = None


class Oswiadczenie(BaseModel):
    dataZlozenia: Optional[str] = None
    podpis: Optional[str] = None


class ZusEwypForm(BaseModel):
    daneOsobyPoszkodowanej: DaneOsobyPoszkodowanej
    adresZamieszkaniaOsobyPoszkodowanej: AdresZamieszkania
    adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuPoszkodowanego: Optional[AdresPolski] = None
    adresDoKorespondencjiOsobyPoszkodowanej: Optional[AdresDoKorespondencji] = None
    adresMiejscaProwadzeniaPozarolniczejDzialalnosci: Optional[AdresDzialalnosci] = None
    adresSprawowaniaOpiekiNadDzieckiemDoLat3: Optional[AdresDzialalnosci] = None
    daneOsobyKtoraZawiadamia: Optional[DaneOsobyKtoraZawiadamia] = None
    adresZamieszkaniaOsobyKtoraZawiadamia: Optional[AdresZamieszkania] = None
    adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuOsobyKtoraZawiadamia: Optional[AdresPolski] = None
    adresDoKorespondencjiOsobyKtoraZawiadamia: Optional[AdresDoKorespondencji] = None
    informacjaOWypadku: InformacjaOWypadku
    daneSwiadkowWypadku: Optional[list[Swiadek]] = None
    zalaczniki: Optional[Zalaczniki] = None
    dokumentyDoDostarczeniaPozniej: Optional[DokumentyDoDostarczeniaPozniej] = None
    sposobOdbioruOdpowiedzi: Optional[Literal["w_placowce_ZUS", "poczta_na_adres_wskazany_we_wniosku", "na_koncie_PUE_ZUS"]] = None
    oswiadczenie: Optional[Oswiadczenie] = None


def pdf_pages_to_base64_images(pdf_path: Path) -> list[str]:
    """
    Convert each page of a PDF to a base64-encoded JPEG image.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of base64-encoded image strings
    """
    # Convert PDF pages to PIL images
    pages = convert_from_path(pdf_path, dpi=200)
    
    base64_images = []
    for page in pages:
        # Convert PIL image to bytes
        buffer = BytesIO()
        page.save(buffer, format="JPEG", quality=85)
        buffer.seek(0)
        
        # Encode to base64
        base64_image = base64.b64encode(buffer.read()).decode("utf-8")
        base64_images.append(base64_image)
    
    return base64_images


def process_pdf_ocr(pdf_path: Path) -> str:
    """
    Process a PDF file and perform OCR to extract text using OpenAI Vision.
    
    Args:
        pdf_path: Path to the uploaded PDF file
        
    Returns:
        Extracted text from the PDF
    """
    # Convert PDF pages to base64 images
    base64_images = pdf_pages_to_base64_images(pdf_path)
    
    # Build content list - start with prompt, then add images
    content = [
        {
            "type": "input_text",
            "text": OCR_SYSTEM_PROMPT,
        }
    ]
    
    for base64_image in base64_images:
        content.append({
            "type": "input_image",
            "image_url": f"data:image/jpeg;base64,{base64_image}",
        })
    
    response = client.responses.parse(
        model="gpt-5-mini-2025-08-07",
        input=[
            {"role": "user", "content": content}
        ],
        text_format=ZusEwypForm,
    )
    
    result = response.output_parsed
    return result.model_dump_json(indent=2, exclude_none=True)
