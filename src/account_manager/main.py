"""account_manager - 메인 진입점"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# .env 로드 (프로젝트 루트에서 실행 가정)
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
from .storage import list_accounts, load_account, save_account
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
        email = console.input("[cyan]이메일/아이디: [/cyan]").strip()
        if email:
            fields["이메일"] = email
        password = console.input("[cyan]비밀번호: [/cyan]").strip()
        if password:
            fields["비밀번호"] = password
        memo = console.input("[cyan]메모 (선택): [/cyan]").strip()
        # 빈 값 제거
        fields = {k: v for k, v in fields.items() if v}
        acc = save_account(site=site, fields=fields, body=memo)
        print_system(f"'{site}' 계정이 [{acc.category}] 카테고리에 저장되었습니다.")
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

    elif cmd in ("/exit", "/quit", "/q"):
        print_system("안녕히 계세요!")
        sys.exit(0)

    return False


def main():
    print_banner()

    # prompt_toolkit 세션 설정
    history_file = Path(".prompt_history")
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
