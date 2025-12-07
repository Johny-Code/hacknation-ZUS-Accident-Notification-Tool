
from openai import OpenAI
import os
from typing import Optional
from prompts.check_if_valid import verification_system_prompt, verification_system_prompt_wyjasnienia
from pydantic import BaseModel
import json

class ValidityCheckModel(BaseModel):
    dataWypadku: Optional[str] = None
    godzinaWypadku: Optional[str] = None
    miejsceWypadku: Optional[str] = None
    planowanaGodzinaRozpoczeciaPracy: Optional[str] = None
    planowanaGodzinaZakonczeniaPracy: Optional[str] = None
    rodzajDoznanychUrazow: Optional[str] = None
    opisOkolicznosciMiejscaIPrzyczyn: Optional[str] = None
    placowkaUdzielajacaPierwszejPomocy: Optional[str] = None
    organProwadzacyPostepowanie: Optional[str] = None
    opisStanuMaszynyIUzytkowania: Optional[str] = None
    valid: bool
    comment: str


class ValidityCheckWyjasnieniaModel(BaseModel):
    """Model walidacji dla formularza 'Wyjaśnienia poszkodowanego'."""
    dataWypadku: Optional[str] = None
    miejsceWypadku: Optional[str] = None
    godzinaWypadku: Optional[str] = None
    planowanaGodzinaRozpoczeciaPracy: Optional[str] = None
    planowanaGodzinaZakonczeniaPracy: Optional[str] = None
    rodzajCzynnosciPrzedWypadkiem: Optional[str] = None
    opisOkolicznosciWypadku: Optional[str] = None
    czyWStanieNietrzezwosci: Optional[str] = None
    valid: bool
    comment: str


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def check_if_report_valid(report_data: dict) -> ValidityCheckModel:

    messages = [
        {"role": "system", "content": verification_system_prompt},
        {"role": "user", "content": str(report_data)}
    ]

    response = client.responses.parse(
        input=messages,
        model="gpt-5-mini",
        text_format=ValidityCheckModel
    )


    return response.output_parsed


def check_if_wyjasnienia_valid(form_data: dict) -> ValidityCheckWyjasnieniaModel:
    """
    Walidacja LLM dla formularza 'Wyjaśnienia poszkodowanego'.
    
    Args:
        form_data: Słownik z danymi formularza wyjaśnień poszkodowanego
        
    Returns:
        ValidityCheckWyjasnieniaModel z wynikiem walidacji i ewentualnymi uwagami do pól
    """
    messages = [
        {"role": "system", "content": verification_system_prompt_wyjasnienia},
        {"role": "user", "content": str(form_data)}
    ]

    response = client.responses.parse(
        input=messages,
        model="gpt-5-mini",
        text_format=ValidityCheckWyjasnieniaModel
    )

    return response.output_parsed