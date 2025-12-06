import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models import FormResponse, ZawiadomienieOWypadku
from services.validation import validate_data
from services.check_if_report_valid import check_if_report_valid
from services.pdf_filler import generate_filled_pdf
from prompts.voice_assistant import voice_system_prompt

logger = logging.getLogger(__name__)

router = APIRouter(tags=["voice"])

# Directory for storing filled forms
FILLED_FORMS_DIR = Path(__file__).parent.parent / "filled_forms"
FILLED_FORMS_DIR.mkdir(exist_ok=True)

# Directory for PESEL-based PDF storage
PDFS_DIR = Path(__file__).parent.parent / "pdfs"
PDFS_DIR.mkdir(exist_ok=True)


class SessionRequest(BaseModel):
    """Request for creating a voice session."""
    voice: Optional[str] = "alloy"  # Voice to use: alloy, echo, fable, onyx, nova, shimmer


class SessionResponse(BaseModel):
    """Response containing session token for WebRTC connection."""
    client_secret: str
    session_id: str
    expires_at: int


class VoiceFormSubmission(BaseModel):
    """Form data collected from voice conversation."""
    form_data: dict
    conversation_id: Optional[str] = None


@router.get("/voice")
async def voice_chat():
    """
    Voice chat info endpoint.
    Returns information about the voice assistant feature.
    """
    return {
        "status": "available",
        "message": "Voice assistant is ready. Use POST /voice/session to start.",
        "supported_voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    }


@router.post("/voice/session", response_model=SessionResponse)
async def create_voice_session(request: SessionRequest = SessionRequest()):
    """
    Create an ephemeral session token for WebRTC connection to OpenAI Realtime API.
    
    This token is used by the browser to establish a direct WebRTC connection
    with OpenAI's Realtime API for voice conversations.
    
    Returns:
        SessionResponse with client_secret for WebRTC connection
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/realtime/sessions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-realtime-preview-2024-12-17",
                    "voice": request.voice,
                    "instructions": voice_system_prompt,
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    },
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 500
                    }
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to create voice session: {response.text}"
                )
            
            data = response.json()
            logger.info(f"Voice session created: {data.get('id', 'unknown')}")
            
            return SessionResponse(
                client_secret=data["client_secret"]["value"],
                session_id=data["id"],
                expires_at=data["client_secret"]["expires_at"]
            )
            
    except httpx.RequestError as e:
        logger.error(f"Request error creating voice session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to connect to OpenAI: {str(e)}")


@router.post("/voice/submit", response_model=FormResponse)
async def submit_voice_form(submission: VoiceFormSubmission):
    """
    Submit form data collected from voice conversation.
    
    This endpoint receives the structured form data extracted from the voice
    conversation and processes it using the same validation and PDF generation
    logic as the regular form submission.
    
    Args:
        submission: Form data collected from voice conversation
        
    Returns:
        FormResponse with validation results and PDF filename if successful
    """
    form_dict = submission.form_data
    
    # Step 1: Schema validation
    validation = validate_data(form_dict)
    
    if not validation["success"]:
        return FormResponse(
            success=False,
            message="Formularz zawiera błędy walidacji. Popraw zaznaczone pola.",
            data={
                "form": form_dict,
                "errors": validation["errors"],
                "source": "voice"
            },
        )
    
    # Step 2: Save to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    json_filename = f"voice_{timestamp}.json"
    json_filepath = FILLED_FORMS_DIR / json_filename
    
    with open(json_filepath, "w", encoding="utf-8") as f:
        json.dump(form_dict, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Voice form saved to {json_filename}")
    
    # Step 3: Validate with LLM
    info_wypadku = form_dict.get("informacjaOWypadku", {})
    if info_wypadku:
        logger.info(f"Validating voice form data with LLM")
        validity_check = check_if_report_valid(info_wypadku)
        
        # Build field errors dict
        field_errors = {}
        field_mapping = [
            "dataWypadku",
            "godzinaWypadku",
            "miejsceWypadku",
            "planowanaGodzinaRozpoczeciaPracy",
            "planowanaGodzinaZakonczeniaPracy",
            "rodzajDoznanychUrazow",
            "opisOkolicznosciMiejscaIPrzyczyn",
            "placowkaUdzielajacaPierwszejPomocy",
            "organProwadzacyPostepowanie",
            "opisStanuMaszynyIUzytkowania",
        ]
        
        for field in field_mapping:
            field_value = getattr(validity_check, field, None)
            if field_value:
                field_errors[field] = field_value
        
        # If LLM validation failed, return errors
        if not validity_check.valid:
            return FormResponse(
                success=False,
                message=validity_check.comment,
                data={
                    "valid": False,
                    "comment": validity_check.comment,
                    "fieldErrors": field_errors,
                    "json_filename": json_filename,
                    "pdf_filename": None,
                    "source": "voice"
                }
            )
    else:
        validity_check = None
        field_errors = {}
    
    # Step 4: Generate filled PDF
    try:
        pdf_path = generate_filled_pdf(
            form_data=form_dict,
            output_dir=FILLED_FORMS_DIR,
            filename_prefix=f"voice_EWYP_{timestamp}"
        )
        pdf_filename = pdf_path.name
        logger.info(f"Generated PDF from voice: {pdf_filename}")
    except FileNotFoundError as e:
        logger.error(f"PDF template not found: {e}")
        return FormResponse(
            success=True,
            message="Formularz zweryfikowany, ale generowanie PDF nie powiodło się: brak szablonu",
            data={
                "valid": True,
                "comment": validity_check.comment if validity_check else "OK",
                "fieldErrors": field_errors,
                "json_filename": json_filename,
                "pdf_filename": None,
                "source": "voice"
            }
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return FormResponse(
            success=True,
            message=f"Formularz zweryfikowany, ale generowanie PDF nie powiodło się: {str(e)}",
            data={
                "valid": True,
                "comment": validity_check.comment if validity_check else "OK",
                "fieldErrors": field_errors,
                "json_filename": json_filename,
                "pdf_filename": None,
                "source": "voice"
            }
        )
    
    # Step 5: Auto-save to PESEL folder
    pesel = form_dict.get("daneOsobyPoszkodowanej", {}).get("pesel", "")
    pesel_folder_path = None
    
    if pesel and len(pesel) == 11 and pesel.isdigit():
        try:
            target_folder = get_pesel_folder(pesel)
            target_path = target_folder / pdf_filename
            import shutil
            shutil.copy2(pdf_path, target_path)
            pesel_folder_path = f"{target_folder.name}/{pdf_filename}"
            logger.info(f"Voice PDF saved to PESEL folder: {target_path}")
        except Exception as e:
            logger.error(f"Failed to save PDF to PESEL folder: {e}")
    
    # Step 6: Return success
    return FormResponse(
        success=True,
        message="Formularz głosowy został zweryfikowany pomyślnie i PDF został wygenerowany.",
        data={
            "valid": True,
            "comment": validity_check.comment if validity_check else "Dane zostały poprawnie zebrane.",
            "fieldErrors": field_errors,
            "json_filename": json_filename,
            "pdf_filename": pdf_filename,
            "pesel_folder_path": pesel_folder_path,
            "source": "voice"
        }
    )


def get_pesel_folder(pesel: str) -> Path:
    """
    Get the appropriate folder for a given PESEL.
    Same logic as in form.py for consistency.
    """
    existing_folders = sorted(
        [f for f in PDFS_DIR.iterdir() if f.is_dir() and f.name.startswith(f"{pesel}_")],
        key=lambda x: int(x.name.split("_")[-1]) if x.name.split("_")[-1].isdigit() else 0
    )
    
    if not existing_folders:
        new_folder = PDFS_DIR / f"{pesel}_1"
        new_folder.mkdir(parents=True, exist_ok=True)
        return new_folder
    
    latest_folder = existing_folders[-1]
    files_in_folder = list(latest_folder.glob("*.pdf"))
    
    if len(files_in_folder) < 2:
        return latest_folder
    
    latest_num = int(latest_folder.name.split("_")[-1])
    new_folder = PDFS_DIR / f"{pesel}_{latest_num + 1}"
    new_folder.mkdir(parents=True, exist_ok=True)
    return new_folder
