"""LangChain 에이전트 도구 정의"""
from langchain_core.tools import tool

from .storage import (
    load_account,
    list_accounts,
    save_account,
    delete_account,
    search_accounts,
)
from .memory import record_history, append_memory, read_memory, read_history


@tool
def tool_search_accounts(query: str) -> str:
    """
    계정 목록에서 키워드로 검색합니다.
    사이트명, URL, 카테고리, 메모 등에서 검색됩니다.
    비밀번호와 같은 민감한 정보는 검색 대상에서 제외됩니다.

    Args:
        query: 검색할 키워드 (예: "google", "이메일", "API")
    """
    results = search_accounts(query)
    if not results:
        return f"'{query}'에 해당하는 계정을 찾지 못했습니다."
    lines = [f"검색 결과 ({len(results)}개):"]
    for acc in results:
        url = acc.metadata.get("url", "")
        category = acc.metadata.get("category", "")
        lines.append(f"- **{acc.site}** {f'({url})' if url else ''} {f'[{category}]' if category else ''}")
    return "\n".join(lines)


@tool
def tool_list_accounts(category: str = "") -> str:
    """
    저장된 모든 계정 목록을 반환합니다.
    카테고리를 지정하면 해당 카테고리만 필터링합니다.

    Args:
        category: 필터링할 카테고리 (선택, 예: "이메일", "SNS")
    """
    accounts = list_accounts()
    if not accounts:
        return "저장된 계정이 없습니다."
    if category:
        accounts = [a for a in accounts if category.lower() in str(a.metadata.get("category", "")).lower()]
    if not accounts:
        return f"'{category}' 카테고리의 계정이 없습니다."
    lines = [f"계정 목록 ({len(accounts)}개):"]
    for acc in accounts:
        url = acc.metadata.get("url", "")
        cat = acc.metadata.get("category", "")
        lines.append(f"- **{acc.site}** {f'({url})' if url else ''} {f'[{cat}]' if cat else ''}")
    return "\n".join(lines)


@tool
def tool_get_account(site: str, show_password: bool = False) -> str:
    """
    특정 사이트의 계정 정보를 조회합니다.
    show_password가 True일 때만 비밀번호를 복호화하여 표시합니다.
    사용자가 명시적으로 비밀번호를 요청한 경우에만 show_password=True로 호출하세요.

    Args:
        site: 사이트명 또는 파일명 (예: "google", "naver")
        show_password: 비밀번호 표시 여부 (기본값: False)
    """
    account = load_account(site)
    if not account:
        return f"'{site}' 계정을 찾을 수 없습니다. /list 명령으로 목록을 확인하세요."
    return account.get_display(show_password=show_password)


@tool
def tool_save_account(site: str, fields_yaml: str, memo: str = "") -> str:
    """
    계정 정보를 저장하거나 업데이트합니다.
    비밀번호는 자동으로 암호화됩니다.

    Args:
        site: 사이트명 (예: "Google", "Naver")
        fields_yaml: YAML 형식의 필드 데이터
                     예: "이메일: test@gmail.com\\n비밀번호: mypass123\\nurl: https://google.com"
        memo: 자유 형식의 메모 (선택)
    """
    import yaml
    try:
        fields = yaml.safe_load(fields_yaml) or {}
    except Exception as e:
        return f"필드 파싱 오류: {e}\nYAML 형식으로 입력해주세요."

    account = save_account(site=site, fields=fields, body=memo)
    record_history(site, "저장", f"필드: {', '.join(fields.keys())}")
    return f"'{site}' 계정이 [{account.category}] 카테고리에 저장되었습니다."


@tool
def tool_update_field(site: str, field: str, new_value: str) -> str:
    """
    계정의 특정 필드를 업데이트합니다.
    비밀번호 변경 시 자동으로 이력이 기록됩니다.

    Args:
        site: 사이트명
        field: 변경할 필드명 (예: "비밀번호", "이메일")
        new_value: 새 값
    """
    account = load_account(site)
    if not account:
        return f"'{site}' 계정을 찾을 수 없습니다."
    save_account(site=site, fields={field: new_value}, body=account.body)
    record_history(site, f"{field} 변경", f"이전값 보존됨")
    return f"'{site}'의 {field}이(가) 업데이트되었습니다."


@tool
def tool_delete_account(site: str) -> str:
    """
    계정을 삭제합니다. 이 작업은 되돌릴 수 없습니다.

    Args:
        site: 삭제할 사이트명
    """
    if delete_account(site):
        record_history(site, "삭제", "계정 완전 삭제")
        return f"'{site}' 계정이 삭제되었습니다."
    return f"'{site}' 계정을 찾을 수 없습니다."


@tool
def tool_read_history(site: str = "") -> str:
    """
    계정 변경 이력을 조회합니다.

    Args:
        site: 특정 사이트 이력만 필터링 (선택, 비어있으면 전체 이력)
    """
    history = read_history()
    if not site:
        return history
    lines = history.split("\n")
    filtered = [l for l in lines if not l.startswith("|") or site.lower() in l.lower()
                or "날짜" in l or "---" in l]
    return "\n".join(filtered)


@tool
def tool_save_memory(content: str) -> str:
    """
    중요한 정보를 MEMORY.md에 저장합니다.
    향후 대화에서도 기억해야 할 내용을 저장하세요.

    Args:
        content: 저장할 내용
    """
    append_memory(content)
    return f"기억에 저장되었습니다: {content[:50]}..."


ALL_TOOLS = [
    tool_search_accounts,
    tool_list_accounts,
    tool_get_account,
    tool_save_account,
    tool_update_field,
    tool_delete_account,
    tool_read_history,
    tool_save_memory,
]
