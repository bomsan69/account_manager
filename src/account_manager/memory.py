"""MEMORY.md 및 HISTORY.md 관리 모듈"""
import os
from datetime import datetime
from pathlib import Path

MEMORY_FILE = Path(os.environ.get("MEMORY_FILE", "memory/MEMORY.md"))
HISTORY_FILE = Path(os.environ.get("HISTORY_FILE", "memory/HISTORY.md"))


def _ensure_files():
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not MEMORY_FILE.exists():
        MEMORY_FILE.write_text(
            "# MEMORY\n\n챗봇이 기억할 중요한 정보가 저장됩니다.\n", encoding="utf-8"
        )
    if not HISTORY_FILE.exists():
        HISTORY_FILE.write_text(
            "# HISTORY\n\n계정 변경 이력이 기록됩니다.\n", encoding="utf-8"
        )


def read_memory() -> str:
    _ensure_files()
    return MEMORY_FILE.read_text(encoding="utf-8")


def append_memory(content: str):
    """MEMORY.md에 새 내용 추가"""
    _ensure_files()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    text = MEMORY_FILE.read_text(encoding="utf-8")
    text += f"\n## {timestamp}\n{content}\n"
    MEMORY_FILE.write_text(text, encoding="utf-8")


def read_history() -> str:
    _ensure_files()
    return HISTORY_FILE.read_text(encoding="utf-8")


def record_history(site: str, action: str, detail: str = ""):
    """HISTORY.md에 변경 이력 기록"""
    _ensure_files()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n| {timestamp} | {site} | {action} | {detail} |"
    text = HISTORY_FILE.read_text(encoding="utf-8")

    # 테이블 헤더가 없으면 추가
    if "| 날짜시간 |" not in text:
        text += "\n\n| 날짜시간 | 사이트 | 액션 | 상세 |\n|---------|--------|------|------|\n"

    text += entry
    HISTORY_FILE.write_text(text, encoding="utf-8")
