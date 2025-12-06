from fastapi import APIRouter

router = APIRouter(tags=["voice"])


@router.get("/voice")
async def voice_chat():
    """
    Voice chat endpoint placeholder.
    Later: Will handle voice-to-text and AI assistant interaction.
    """
    return {
        "status": "placeholder",
        "message": "Voice chat endpoint - coming soon"
    }

