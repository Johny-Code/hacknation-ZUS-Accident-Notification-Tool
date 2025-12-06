from pathlib import Path

# Upload configuration
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def get_user_upload_dir(user_id: str) -> Path:
    """
    Get or create a user-specific upload directory.
    
    Args:
        user_id: Unique identifier for the user
        
    Returns:
        Path to the user's upload directory
    """
    user_dir = UPLOAD_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir

