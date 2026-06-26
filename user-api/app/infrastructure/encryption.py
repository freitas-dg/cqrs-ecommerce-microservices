import base64
import hashlib
import logging
from cryptography.fernet import Fernet, InvalidToken
from app.infrastructure.config import get_settings

logger = logging.getLogger(__name__)

class EncryptionService:

    def __init__(self) -> None:
        settings = get_settings()
        raw_key = settings.encryption_key.encode()
        derived = hashlib.sha256(raw_key).digest()
        self._fernet = Fernet(base64.urlsafe_b64encode(derived))

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return plaintext
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext:
            return ciphertext
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken:
            logger.warning('Failed to decrypt value — returning as-is.')
            return ciphertext
