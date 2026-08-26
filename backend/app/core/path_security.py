import os
import re
from pathlib import PurePosixPath, PureWindowsPath
from app.config import settings

# Characters/patterns forbidden in script paths to prevent command injection
FORBIDDEN_CHARS_REGEX = re.compile(r"[;&\|><\$`'\"]")
# Windows drive letter regex (e.g., C:, D:)
DRIVE_LETTER_REGEX = re.compile(r"^[a-zA-Z]:")


def sanitize_and_validate_script_path(script_path: str) -> str:
    r"""Validates and normalizes script paths against security rules.

    Rules:
    1. Must not be empty or whitespace only.
    2. Must not contain shell injection characters (; & | > < $ ` ' ").
    3. Must not be an absolute path (e.g., C:/..., /...).
    4. Must not contain path traversal (../ or ..\).
    5. Must end with .py extension.
    6. Must reside within or relative to approved settings.TEST_SCRIPTS_DIR.

    Returns:
        str: Normalized relative script path (e.g., "test_scripts/login_test.py").
    """

    if not script_path or not script_path.strip():
        raise ValueError("Script path cannot be blank.")

    cleaned_path = script_path.strip()

    # Reject shell injection characters
    if FORBIDDEN_CHARS_REGEX.search(cleaned_path):
        raise ValueError("Script path contains invalid security characters.")

    # Reject absolute paths (Windows drive letters or starting with slash)
    if DRIVE_LETTER_REGEX.match(cleaned_path) or cleaned_path.startswith("/") or cleaned_path.startswith("\\"):
        raise ValueError("Absolute script paths are strictly forbidden. Use relative paths.")

    # Normalize backslashes to forward slashes
    normalized_posix = cleaned_path.replace("\\", "/")

    # Check path parts for path traversal ("..")
    parts = normalized_posix.split("/")
    if ".." in parts or "." in parts:
        raise ValueError("Path traversal sequences (..) are strictly forbidden.")

    # Extension check
    if not normalized_posix.endswith(".py"):
        raise ValueError("Only Python test scripts (.py) are currently supported.")

    base_dir = settings.TEST_SCRIPTS_DIR.strip().strip("/").strip("\\")

    # If the path starts with base_dir, keep it; otherwise prepend base_dir
    if normalized_posix.startswith(f"{base_dir}/"):
        relative_script_path = normalized_posix
    elif normalized_posix == base_dir:
        raise ValueError("Script path must point to a file, not a directory.")
    else:
        relative_script_path = f"{base_dir}/{normalized_posix}"

    return relative_script_path
