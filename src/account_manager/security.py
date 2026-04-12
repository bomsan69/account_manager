"""암호화/복호화 모듈 - Fernet 대칭 암호화 사용"""
import os
from pathlib import Path
from cryptography.fernet import Fernet


KEY_FILE = Path(os.environ.get("KEY_FILE", "~/.account_manager/.key")).expanduser()


def _load_or_create_key() -> bytes:
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEY_FILE.parent.chmod(0o700)
    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)
    KEY_FILE.chmod(0o600)
    return key


def _fernet() -> Fernet:
    return Fernet(_load_or_create_key())


def encrypt(plaintext: str) -> str:
    """평문 문자열을 암호화하여 문자열로 반환"""
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """암호화된 문자열을 복호화"""
    return _fernet().decrypt(ciphertext.encode()).decode()


def is_encrypted(value: str) -> bool:
    """값이 Fernet 암호화된 문자열인지 확인"""
    return value.startswith("gAAAAA")
