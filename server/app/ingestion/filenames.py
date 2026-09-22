from pathlib import PurePosixPath

from app.core.exceptions import InvalidDocumentError

_MAX_LENGTH = 200


def safe_filename(raw: str) -> str:
    """The bare file name of an upload; any folder part is dropped so it cannot leave docs/."""
    name = PurePosixPath(raw.replace("\\", "/")).name.strip()
    if name in {"", ".", ".."} or any(ord(char) < 32 for char in name):
        raise InvalidDocumentError("The file needs a valid name.")
    if len(name) > _MAX_LENGTH:
        raise InvalidDocumentError(f"The file name is longer than {_MAX_LENGTH} characters.")
    return name
