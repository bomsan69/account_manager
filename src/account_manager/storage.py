"""계정 정보 단일 YAML 파일 CRUD 모듈

저장 구조:
  accounts/accounts.yaml
    카테고리명:
      사이트키:
        site: 사이트 표시명
        url: ...
        auth_method: password | oauth | apikey | passkey
        # password 방식
        이메일: ...
        비밀번호: [암호화됨]
        # oauth 방식
        oauth_provider: Google | GitHub | Apple | Kakao | Naver 등
        oauth_account: provider 계정 이메일
        # apikey 방식
        api_key: [암호화됨]
        메모: ...
        updated: YYYY-MM-DD

auth_method 종류:
  password - 이메일/아이디 + 비밀번호
  oauth    - 소셜 로그인 (Google, GitHub 등), 비밀번호 없음
  apikey   - API 키 인증
  passkey  - 패스키/WebAuthn, 비밀번호 없음
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

from .security import encrypt, decrypt, is_encrypted

_DEFAULT_DATA_DIR = Path.home() / ".account_manager"
ACCOUNTS_FILE = Path(
    os.environ.get("ACCOUNTS_FILE", str(_DEFAULT_DATA_DIR / "accounts.yaml"))
).expanduser()
DEFAULT_CATEGORY = "기타"

# 암호화가 필요한 필드
SENSITIVE_FIELDS = {"password", "비밀번호", "pw", "passwd", "secret", "api_key", "token"}

# 인증 방식 레이블
AUTH_METHOD_LABELS = {
    "password": "🔑 비밀번호",
    "oauth":    "🔗 소셜 로그인 (OAuth)",
    "apikey":   "🗝️  API 키",
    "passkey":  "🛡️  패스키",
}


class Account:
    def __init__(self, site: str, key: str, category: str, fields: dict):
        self.site = site        # 표시명 (예: "Google")
        self.key = key          # YAML 키 (예: "google")
        self.category = category
        self.fields = fields    # 나머지 필드 (url, 이메일, 비밀번호, 메모 등)

    @property
    def metadata(self) -> dict:
        """tools.py 하위 호환용 - fields를 metadata처럼 노출"""
        return {**self.fields, "category": self.category}

    @property
    def body(self) -> str:
        return self.fields.get("메모", "")

    def get_display(self, show_password: bool = False) -> str:
        auth_method = self.fields.get("auth_method", "password")
        auth_label = AUTH_METHOD_LABELS.get(auth_method, auth_method)
        lines = [f"## {self.site}  `[{self.category}]`  {auth_label}"]

        # 인증 방식별 표시 순서 정의
        if auth_method == "oauth":
            ordered_keys = ["url", "oauth_provider", "oauth_account", "아이디", "이메일"]
        elif auth_method == "apikey":
            ordered_keys = ["url", "이메일", "아이디", "api_key"]
        elif auth_method == "passkey":
            ordered_keys = ["url", "이메일", "아이디"]
        else:  # password (기본)
            ordered_keys = ["url", "이메일", "아이디", "비밀번호"]

        skip = {"site", "메모", "auth_method", "updated", "category"}

        # 정의된 순서로 먼저 출력
        shown = set()
        for key in ordered_keys:
            val = self.fields.get(key)
            if not val:
                continue
            if key.lower() in SENSITIVE_FIELDS and isinstance(val, str) and is_encrypted(val):
                display_val = decrypt(val) if show_password else "****"
            else:
                display_val = val
            lines.append(f"- **{key}**: {display_val}")
            shown.add(key)

        # 나머지 필드 출력 (skip 제외)
        for key, val in self.fields.items():
            if key in skip or key in shown:
                continue
            if key.lower() in SENSITIVE_FIELDS and isinstance(val, str) and is_encrypted(val):
                display_val = decrypt(val) if show_password else "****"
            else:
                display_val = val
            lines.append(f"- **{key}**: {display_val}")

        updated = self.fields.get("updated", "")
        if updated:
            lines.append(f"- **최종 수정**: {updated}")
        memo = self.fields.get("메모", "")
        if memo:
            lines.append(f"\n**메모**: {memo}")
        return "\n".join(lines)


# ── YAML 파일 I/O ──────────────────────────────────────────────

def _ensure_file() -> None:
    ACCOUNTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not ACCOUNTS_FILE.exists():
        ACCOUNTS_FILE.write_text("# Account Manager\n", encoding="utf-8")


def _load_yaml() -> dict:
    _ensure_file()
    text = ACCOUNTS_FILE.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    return data if isinstance(data, dict) else {}


def _save_yaml(data: dict) -> None:
    _ensure_file()
    ACCOUNTS_FILE.write_text(
        yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


def _site_key(site: str) -> str:
    """사이트명 → YAML 키 (소문자, 공백→_)"""
    return site.lower().replace(" ", "_").replace("/", "_")


# ── Public API ─────────────────────────────────────────────────

def list_accounts(category: str = "") -> list[Account]:
    """전체 또는 특정 카테고리의 계정 목록 반환"""
    data = _load_yaml()
    accounts = []
    for cat, entries in data.items():
        if not isinstance(entries, dict):
            continue
        if category and category.lower() not in cat.lower():
            continue
        for key, fields in entries.items():
            if not isinstance(fields, dict):
                continue
            site = fields.get("site", key)
            accounts.append(Account(site=site, key=key, category=cat, fields=fields))
    return accounts


def list_categories() -> list[str]:
    """저장된 카테고리 목록 반환"""
    data = _load_yaml()
    return [k for k, v in data.items() if isinstance(v, dict)]


def load_account(site: str) -> Optional[Account]:
    """사이트명 또는 키로 계정 조회 (대소문자 무시)"""
    query = site.lower().strip()
    for acc in list_accounts():
        if acc.key == query or acc.site.lower() == query:
            return acc
    # 부분 일치 허용
    for acc in list_accounts():
        if query in acc.key or query in acc.site.lower():
            return acc
    return None


def save_account(
    site: str,
    fields: dict,
    body: str = "",
    encrypt_sensitive: bool = True,
    category: str = "",
    key: str = "",
) -> Account:
    """계정 저장 (신규 또는 업데이트). 비밀번호 자동 암호화."""
    data = _load_yaml()

    if key:
        # 명시적 key가 주어진 경우: 해당 key로 직접 조회 (같은 사이트 다계정 지원)
        existing_cat = None
        existing_fields = None
        for cat_name, entries in data.items():
            if isinstance(entries, dict) and key in entries:
                existing_cat = cat_name
                existing_fields = entries[key]
                break
        if existing_cat:
            cat = category or existing_cat
            merged = dict(existing_fields)
        else:
            cat = category or fields.pop("category", DEFAULT_CATEGORY)
            merged = {"site": site}
    else:
        # 기존 동작: 사이트명으로 조회
        existing = load_account(site)
        if existing:
            cat = category or existing.category
            key = existing.key
            merged = dict(existing.fields)
        else:
            cat = category or fields.pop("category", DEFAULT_CATEGORY)
            key = _site_key(site)
            merged = {"site": site}

    # 카테고리 섹션 없으면 생성
    if cat not in data:
        data[cat] = {}

    # 필드 병합
    if body:
        merged["메모"] = body
    for k, v in fields.items():
        if k == "category":
            continue
        if encrypt_sensitive and k.lower() in SENSITIVE_FIELDS and isinstance(v, str):
            if not is_encrypted(v):
                v = encrypt(v)
        merged[k] = v

    merged["updated"] = datetime.now().strftime("%Y-%m-%d")
    data[cat][key] = merged
    _save_yaml(data)

    return Account(site=site, key=key, category=cat, fields=merged)


def delete_account(site: str) -> bool:
    """계정 삭제. 카테고리가 비면 카테고리도 제거."""
    acc = load_account(site)
    if not acc:
        return False
    data = _load_yaml()
    cat_data = data.get(acc.category, {})
    cat_data.pop(acc.key, None)
    if not cat_data:
        data.pop(acc.category, None)
    else:
        data[acc.category] = cat_data
    _save_yaml(data)
    return True


def search_accounts(query: str) -> list[Account]:
    """사이트명·URL·카테고리·메모에서 키워드 검색 (비밀번호 제외)"""
    q = query.lower()
    results = []
    for acc in list_accounts():
        searchable = f"{acc.site} {acc.key} {acc.category}".lower()
        for k, v in acc.fields.items():
            if k.lower() not in SENSITIVE_FIELDS:
                searchable += " " + str(v).lower()
        if q in searchable:
            results.append(acc)
    return results
