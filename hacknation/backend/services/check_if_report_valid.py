
from openai import OpenAI
import os
from typing import Optional
from prompts.check_if_valid import verification_system_prompt
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



client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def check_if_report_valid(report_data: dict) -> bool:

    messages = [
        {"role": "system", "content": verification_system_prompt},
        {"role": "user", "content": str(report_data)}
    ]

    response = client.responses.parse(
        input=messages,
        model="gpt-5-nano-2025-08-07",
        text_format=ValidityCheckModel
    )


    return response.output_parsed