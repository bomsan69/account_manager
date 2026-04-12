"""Rich 기반 터미널 UI 컴포넌트"""
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme
from rich import box

APP_THEME = Theme({
    "user": "bold cyan",
    "assistant": "bold green",
    "system": "bold yellow",
    "error": "bold red",
    "info": "dim",
    "title": "bold magenta",
})

console = Console(theme=APP_THEME)

BANNER = """
╔══════════════════════════════════════════╗
║       🔐 Account Manager v0.1.0          ║
║    AI 기반 계정 정보 관리 챗봇           ║
╚══════════════════════════════════════════╝
"""

HELP_TEXT = """
## 슬래시 명령어

| 명령어 | 설명 |
|--------|------|
| `/help` | 이 도움말 표시 |
| `/list` | 저장된 계정 목록 |
| `/new <site>` | 새 계정 추가 (대화형) |
| `/show <site>` | 계정 정보 조회 |
| `/history [site]` | 변경 이력 조회 |
| `/memory` | 저장된 기억 조회 |
| `/clear` | 화면 지우기 |
| `/exit` | 프로그램 종료 |

## 자연어 사용 예시

- `google 계정 정보 보여줘`
- `naver 비밀번호 알려줘`
- `clickpresso 로그인 정보 저장해줘. 아이디: user1, 비밀번호: pass123`
- `siteground 비밀번호를 newpass456으로 변경해줘`
- `이메일 관련 계정 목록 보여줘`
"""


def print_banner():
    console.print(BANNER, style="title")
    console.print("  '/help'로 사용법을 확인하세요. '/exit'로 종료합니다.\n", style="info")


def print_help():
    console.print(Markdown(HELP_TEXT))


def print_user_message(message: str):
    console.print(f"\n[user]You:[/user] {message}")


def print_assistant_message(content: str):
    console.print(f"\n[assistant]Assistant:[/assistant]")
    try:
        console.print(Markdown(content))
    except Exception:
        console.print(content)


def print_system(message: str):
    console.print(f"[system]{message}[/system]")


def print_error(message: str):
    console.print(f"[error]오류: {message}[/error]")


def print_thinking():
    console.print("[info]생각 중...[/info]", end="\r")


def print_account_table(accounts: list) -> None:
    if not accounts:
        console.print("[info]저장된 계정이 없습니다.[/info]")
        return
    table = Table(box=box.ROUNDED, title=f"계정 목록 ({len(accounts)}개)")
    table.add_column("사이트", style="bold cyan")
    table.add_column("URL", style="dim")
    table.add_column("카테고리")
    table.add_column("최근 수정")
    for acc in accounts:
        table.add_row(
            acc.site,
            acc.fields.get("url", "") if hasattr(acc, "fields") else acc.metadata.get("url", ""),
            getattr(acc, "category", acc.metadata.get("category", "")),
            acc.fields.get("updated", "") if hasattr(acc, "fields") else acc.metadata.get("updated", ""),
        )
    console.print(table)


def confirm(prompt: str) -> bool:
    """사용자 확인 요청"""
    response = console.input(f"[yellow]{prompt} (y/N): [/yellow]").strip().lower()
    return response in ("y", "yes", "예", "네")
