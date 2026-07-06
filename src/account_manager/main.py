"""account_manager - 메인 진입점"""
import csv
import getpass
import hashlib
import io
import os
import sys
from pathlib import Path

_AUTH_SALT = b"acct_mgr_v1_2024"
_AUTH_HASH = "598fb0c4be8b4bf3ff3559a7450af0c067394d7306d446848c7f8621a30d09f7"
_MAX_ATTEMPTS = 3


def _verify_password(pw: str) -> bool:
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), _AUTH_SALT, 200_000)
    return h.hex() == _AUTH_HASH


def _authenticate() -> bool:
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        pw = getpass.getpass(f"비밀번호 ({attempt}/{_MAX_ATTEMPTS}): ")
        if _verify_password(pw):
            return True
        if attempt < _MAX_ATTEMPTS:
            print("비밀번호가 틀렸습니다. 다시 시도하세요.")
    return False

from dotenv import load_dotenv

# ~/.account_manager/.env → 현재 디렉토리 .env 순으로 로드 (나중 것이 우선)
load_dotenv(Path.home() / ".account_manager" / ".env")
load_dotenv()

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style

from .ui import (
    console,
    print_banner,
    print_help,
    print_user_message,
    print_assistant_message,
    print_system,
    print_error,
    print_thinking,
    print_account_table,
    confirm,
)
from .storage import list_accounts, list_categories, load_account, save_account
from .memory import read_memory, read_history

# prompt_toolkit 스타일
PT_STYLE = Style.from_dict({
    "prompt": "#00ff00 bold",
})

# 대화 히스토리 (에이전트에 전달)
conversation_history: list[dict] = []


def handle_slash_command(command: str) -> bool:
    """슬래시 명령어 처리. True 반환 시 LLM으로 넘기지 않음."""
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd == "/help":
        print_help()
        return True

    elif cmd == "/list":
        accounts = list_accounts()
        print_account_table(accounts)
        return True

    elif cmd == "/categories":
        cats = list_categories()
        if not cats:
            print_system("저장된 카테고리가 없습니다.")
        else:
            console.print("\n[bold cyan]카테고리 목록[/bold cyan]")
            for i, cat in enumerate(cats, start=1):
                count = len(list_accounts(category=cat))
                console.print(f"  {i}. [green]{cat}[/green]  ({count}개)")
        return True

    elif cmd == "/show":
        if not arg:
            print_error("사용법: /show <사이트명>")
            return True
        account = load_account(arg)
        if not account:
            print_error(f"'{arg}' 계정을 찾을 수 없습니다.")
            return True
        show_pw = confirm("비밀번호도 표시하시겠습니까?")
        console.print(account.get_display(show_password=show_pw))
        return True

    elif cmd == "/new":
        site = arg or console.input("[cyan]사이트명: [/cyan]").strip()
        if not site:
            print_error("사이트명을 입력해주세요.")
            return True
        fields = {}
        fields["url"] = console.input("[cyan]URL (선택): [/cyan]").strip()
        fields["category"] = console.input("[cyan]카테고리 (예: 이메일, SNS): [/cyan]").strip()

        # 인증 방식 선택
        console.print("[cyan]인증 방식을 선택하세요:[/cyan]")
        console.print("  [bold]1[/bold]. password  - 이메일/아이디 + 비밀번호")
        console.print("  [bold]2[/bold]. oauth     - 소셜 로그인 (Google, GitHub 등)")
        console.print("  [bold]3[/bold]. apikey    - API 키")
        console.print("  [bold]4[/bold]. passkey   - 패스키 (비밀번호 없음)")
        auth_choice = console.input("[cyan]선택 (1~4, 기본값 1): [/cyan]").strip()
        auth_map = {"1": "password", "2": "oauth", "3": "apikey", "4": "passkey",
                    "password": "password", "oauth": "oauth", "apikey": "apikey", "passkey": "passkey"}
        auth_method = auth_map.get(auth_choice, "password")
        fields["auth_method"] = auth_method

        if auth_method == "password":
            email = console.input("[cyan]이메일/아이디: [/cyan]").strip()
            if email:
                fields["이메일"] = email
            password = getpass.getpass("비밀번호 (입력 내용 숨김): ").strip()
            if password:
                fields["비밀번호"] = password
        elif auth_method == "oauth":
            console.print("[dim]OAuth 제공자 예: Google, GitHub, Apple, Kakao, Naver[/dim]")
            provider = console.input("[cyan]OAuth 제공자: [/cyan]").strip()
            if provider:
                fields["oauth_provider"] = provider
            oauth_account = console.input("[cyan]OAuth 계정 이메일: [/cyan]").strip()
            if oauth_account:
                fields["oauth_account"] = oauth_account
        elif auth_method == "apikey":
            email = console.input("[cyan]이메일/아이디 (선택): [/cyan]").strip()
            if email:
                fields["이메일"] = email
            api_key = getpass.getpass("API 키 (입력 내용 숨김): ").strip()
            if api_key:
                fields["api_key"] = api_key
        elif auth_method == "passkey":
            email = console.input("[cyan]이메일/아이디: [/cyan]").strip()
            if email:
                fields["이메일"] = email

        memo = console.input("[cyan]메모 (선택): [/cyan]").strip()
        # 빈 값 제거
        fields = {k: v for k, v in fields.items() if v}
        acc = save_account(site=site, fields=fields, body=memo)
        print_system(f"'{site}' 계정이 [{acc.category}] 카테고리에 저장되었습니다.")
        return True

    elif cmd == "/edit":
        if not arg:
            print_error("사용법: /edit <사이트명>")
            return True
        account = load_account(arg)
        if not account:
            print_error(f"'{arg}' 계정을 찾을 수 없습니다.")
            return True

        site = account.site
        auth_method = account.fields.get("auth_method", "password")
        console.print(f"[cyan]'{site}' 계정 수정 (Enter를 누르면 기존 값을 유지합니다)[/cyan]")

        fields = {}

        cur_url = account.fields.get("url", "")
        new_url = console.input(f"[cyan]URL (현재: {cur_url or '없음'}): [/cyan]").strip()
        if new_url:
            fields["url"] = new_url

        if auth_method == "password":
            cur_email = account.fields.get("이메일", "")
            new_email = console.input(f"[cyan]이메일/아이디 (현재: {cur_email or '없음'}): [/cyan]").strip()
            if new_email:
                fields["이메일"] = new_email
            new_password = getpass.getpass("비밀번호 (변경하려면 입력, 유지하려면 Enter): ").strip()
            if new_password:
                fields["비밀번호"] = new_password
        elif auth_method == "oauth":
            cur_provider = account.fields.get("oauth_provider", "")
            new_provider = console.input(f"[cyan]OAuth 제공자 (현재: {cur_provider or '없음'}): [/cyan]").strip()
            if new_provider:
                fields["oauth_provider"] = new_provider
            cur_oauth_account = account.fields.get("oauth_account", "")
            new_oauth_account = console.input(f"[cyan]OAuth 계정 이메일 (현재: {cur_oauth_account or '없음'}): [/cyan]").strip()
            if new_oauth_account:
                fields["oauth_account"] = new_oauth_account
        elif auth_method == "apikey":
            cur_email = account.fields.get("이메일", "")
            new_email = console.input(f"[cyan]이메일/아이디 (현재: {cur_email or '없음'}): [/cyan]").strip()
            if new_email:
                fields["이메일"] = new_email
            new_api_key = getpass.getpass("API 키 (변경하려면 입력, 유지하려면 Enter): ").strip()
            if new_api_key:
                fields["api_key"] = new_api_key
        elif auth_method == "passkey":
            cur_email = account.fields.get("이메일", "")
            new_email = console.input(f"[cyan]이메일/아이디 (현재: {cur_email or '없음'}): [/cyan]").strip()
            if new_email:
                fields["이메일"] = new_email

        cur_memo = account.fields.get("메모", "")
        new_memo = console.input(f"[cyan]메모 (현재: {cur_memo or '없음'}): [/cyan]").strip()

        if not fields and not new_memo:
            print_system("변경된 내용이 없습니다.")
            return True

        save_account(site=site, fields=fields, body=new_memo, key=account.key)
        print_system(f"'{site}' 계정이 수정되었습니다.")
        return True

    elif cmd == "/history":
        from .memory import read_history
        history = read_history()
        if arg:
            lines = history.split("\n")
            filtered = [l for l in lines if arg.lower() in l.lower() or "날짜" in l or "---" in l or l.startswith("#")]
            console.print("\n".join(filtered))
        else:
            console.print(history)
        return True

    elif cmd == "/memory":
        console.print(read_memory())
        return True

    elif cmd == "/clear":
        console.clear()
        print_banner()
        return True

    elif cmd == "/batch":
        csv_path = Path(arg).expanduser() if arg else None
        if not csv_path:
            print_error("사용법: /batch <CSV파일경로>  (예: /batch ~/sample.csv)")
            return True
        if not csv_path.exists():
            print_error(f"파일을 찾을 수 없습니다: {csv_path}")
            return True

        # CSV 컬럼 정의 (대소문자 무시)
        # site, url, category, auth_method, email, username, password,
        # oauth_provider, oauth_account, api_key, memo
        ok_count = 0
        skip_count = 0
        errors: list[str] = []

        try:
            with csv_path.open(encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except Exception as e:
            print_error(f"CSV 파일 읽기 실패: {e}")
            return True

        if not rows:
            print_error("CSV 파일에 데이터 행이 없습니다.")
            return True

        # 헤더 정규화 (공백·대소문자 제거)
        def norm(s: str) -> str:
            return s.strip().lower().replace(" ", "_")

        console.print(f"[cyan]총 {len(rows)}개 항목을 일괄 등록합니다...[/cyan]")

        for i, raw_row in enumerate(rows, start=2):
            row = {norm(k): (v.strip() if v else "") for k, v in raw_row.items()}

            site = row.get("site", "")
            if not site:
                errors.append(f"행 {i}: site 값이 없습니다. 건너뜁니다.")
                skip_count += 1
                continue

            auth_method = row.get("auth_method", "password").lower()
            valid_methods = {"password", "oauth", "apikey", "passkey"}
            if auth_method not in valid_methods:
                errors.append(f"행 {i} ({site}): 알 수 없는 auth_method '{auth_method}'. 건너뜁니다.")
                skip_count += 1
                continue

            fields: dict = {
                "auth_method": auth_method,
                "category": row.get("category", "") or "기타",
            }
            if row.get("url"):
                fields["url"] = row["url"]

            if auth_method == "password":
                if row.get("email"):
                    fields["이메일"] = row["email"]
                if row.get("username"):
                    fields["아이디"] = row["username"]
                if row.get("password"):
                    fields["비밀번호"] = row["password"]
            elif auth_method == "oauth":
                if row.get("oauth_provider"):
                    fields["oauth_provider"] = row["oauth_provider"]
                if row.get("oauth_account"):
                    fields["oauth_account"] = row["oauth_account"]
            elif auth_method == "apikey":
                if row.get("email"):
                    fields["이메일"] = row["email"]
                if row.get("api_key"):
                    fields["api_key"] = row["api_key"]
            elif auth_method == "passkey":
                if row.get("email"):
                    fields["이메일"] = row["email"]

            memo = row.get("memo", "")

            # 같은 사이트에 여러 계정이 있을 경우 email/username으로 고유 키 생성
            identifier = row.get("email", "") or row.get("username", "")
            if identifier:
                raw = f"{site}_{identifier}".lower()
                unique_key = "".join(c if c.isalnum() or c == "_" else "_" for c in raw)
            else:
                unique_key = site.lower().replace(" ", "_").replace("/", "_")

            try:
                acc = save_account(site=site, fields=fields, body=memo, key=unique_key)
                console.print(f"  [green]✓[/green] {site} [{acc.category}] ({auth_method}) - {identifier or unique_key}")
                ok_count += 1
            except Exception as e:
                errors.append(f"행 {i} ({site}): 저장 실패 — {e}")
                skip_count += 1

        # 결과 요약
        console.print(f"\n[bold]일괄 등록 완료:[/bold] 성공 [green]{ok_count}[/green]건 / 실패 [red]{skip_count}[/red]건")
        if errors:
            console.print("[yellow]오류 내역:[/yellow]")
            for err in errors:
                console.print(f"  [red]✗[/red] {err}")
        return True

    elif cmd in ("/exit", "/quit", "/q"):
        print_system("안녕히 계세요!")
        sys.exit(0)

    return False


def main():
    if not _authenticate():
        print("인증 실패. 프로그램을 종료합니다.")
        sys.exit(1)

    print_banner()

    # prompt_toolkit 세션 설정 - 이력 파일을 홈 디렉토리에 저장 (프로젝트 폴더 노출 방지)
    history_file = Path.home() / ".account_manager" / ".prompt_history"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    session = PromptSession(
        history=FileHistory(str(history_file)),
        auto_suggest=AutoSuggestFromHistory(),
        style=PT_STYLE,
    )

    # 에이전트 지연 로드
    agent_chat = None

    def get_chat():
        nonlocal agent_chat
        if agent_chat is None:
            print_system("AI 에이전트 초기화 중...")
            try:
                from .agent import chat
                agent_chat = chat
                print_system("AI 에이전트 준비 완료.")
            except Exception as e:
                print_error(f"Ollama 연결 실패: {e}")
                print_system("Ollama가 실행 중인지 확인하세요: ollama serve")
        return agent_chat

    while True:
        try:
            user_input = session.prompt(
                "\n> ",
                style=PT_STYLE,
            ).strip()
        except (KeyboardInterrupt, EOFError):
            print_system("\n안녕히 계세요!")
            break

        if not user_input:
            continue

        # 슬래시 명령어 처리
        if user_input.startswith("/"):
            if not handle_slash_command(user_input):
                print_error(f"알 수 없는 명령어: {user_input}. /help로 명령어 목록을 확인하세요.")
            continue

        # AI 에이전트 처리
        print_user_message(user_input)
        print_thinking()

        chat_fn = get_chat()
        if chat_fn is None:
            continue

        try:
            response = chat_fn(user_input, conversation_history)
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": response})
            print_assistant_message(response)
        except Exception as e:
            print_error(f"에이전트 오류: {e}")


if __name__ == "__main__":
    main()
