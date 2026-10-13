import base64
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


TOKEN_URL = "https://iras.iub.edu.bd:8079/v3/account/token"
AES_KEY = b"rW7aT6RZoP3hjtz0"
AES_IV = b"V3k6oMP7C8Jt3E4z"


def _pkcs7_pad(value: bytes, block_size: int = 16) -> bytes:
    padding_length = block_size - len(value) % block_size
    return value + bytes([padding_length]) * padding_length


def encrypt_password(password: str) -> str:
    """Encrypt a plaintext password using the IRAS frontend algorithm."""
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(AES_IV))
    encryptor = cipher.encryptor()
    padded = _pkcs7_pad(password.encode("utf-8"))
    encrypted = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(encrypted).decode("ascii")


def get_token(
    student_id: str, password: str, timeout: float = 20.0
) -> dict[str, Any]:
    """Return the IRAS access token and its server-provided expiry value."""
    payload = json.dumps(
        {
            "email": student_id,
            "password": encrypt_password(password),
        }
    ).encode("utf-8")
    request = Request(
        TOKEN_URL,
        data=payload,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://irasv1.iub.edu.bd",
            "Referer": "https://irasv1.iub.edu.bd/",
            "User-Agent": "Mozilla/5.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            result: Any = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"IRAS rejected the request ({error.code}): {detail}") from error
    except URLError as error:
        raise RuntimeError(f"Could not reach IRAS: {error.reason}") from error

    if not isinstance(result, dict):
        raise RuntimeError("IRAS returned an unexpected response.")
    if result.get("message") == "EPF":
        raise RuntimeError("Invalid student ID or password.")

    data = result.get("data")
    token_data = data[0] if isinstance(data, list) and data and isinstance(data[0], dict) else result
    token = token_data.get("access_token") if isinstance(token_data, dict) else None
    if not isinstance(token, str) or not token:
        raise RuntimeError(f"IRAS returned no access token: {result}")

    expires = token_data.get("expires")
    return {
        "access_token": token,
        "expires": expires,
    }
    