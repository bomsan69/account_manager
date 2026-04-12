# Account Manager

AI 기반 로컬 계정 정보 관리 챗봇 - Ollama 프라이빗 모델을 사용하여 안전하게 웹사이트 가입 정보를 관리합니다.

## 특징

- **완전 로컬**: 모든 데이터와 AI 처리가 로컬 PC에서만 동작
- **Markdown 저장**: `accounts/` 디렉토리에 사이트별 `.md` 파일로 저장 (일반 편집기로도 수정 가능)
- **암호화 보안**: Fernet 대칭 암호화로 비밀번호 보호
- **AI 챗봇**: 자연어로 계정 정보 조회/수정
- **변경 이력**: `memory/HISTORY.md`에 모든 변경 사항 기록
- **장기 기억**: `memory/MEMORY.md`로 세션 간 정보 유지

## 사전 요구사항

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) 패키지 관리자
- [Ollama](https://ollama.ai) 설치 및 실행

```bash
# Ollama 모델 다운로드 (최초 1회)
ollama pull llama3.2
ollama serve
```

## 설치

```bash
# 저장소 클론
git clone <repo-url>
cd account_manager

# 환경 설정
cp .env.example .env
# .env 파일에서 OLLAMA_MODEL 등 설정 확인

# 패키지 설치
uv sync
```

## 실행

```bash
uv run account-mng
```

또는 개발 모드:

```bash
uv run python -m account_manager.main
```

## 슬래시 명령어

| 명령어 | 설명 |
|--------|------|
| `/help` | 사용법 표시 |
| `/list` | 저장된 계정 목록 |
| `/new [사이트명]` | 새 계정 추가 (대화형) |
| `/show <사이트명>` | 계정 정보 조회 |
| `/history [사이트명]` | 변경 이력 조회 |
| `/memory` | 저장된 기억 조회 |
| `/clear` | 화면 지우기 |
| `/exit` | 종료 |

## 자연어 사용 예시

```
> google 계정 정보 보여줘
> naver 비밀번호 알려줘
> clickpresso 로그인 정보 저장해줘. 아이디: user1, 비밀번호: pass123
> siteground 비밀번호를 newpass456으로 변경하고 이력 남겨줘
> 이메일 API 서비스 관련 계정 목록 보여줘
```

## 계정 파일 형식

`accounts/accounts.yaml`을 직접 편집할 수 있습니다:

```yaml
이메일:
  gmail:
    site: Gmail
    url: https://gmail.com
    이메일: user@gmail.com
    비밀번호: gAAAAA...  # 암호화됨 (AI가 자동 처리)
    메모: 2FA 활성화
    updated: '2026-04-11'
```

> **주의**: 비밀번호를 직접 평문으로 입력하면 다음번 AI 업데이트 시 자동 암호화됩니다.

## 보안 구조

- 암호화 키: `~/.account_manager/.key` (권한: 600)
- 비밀번호: Fernet 대칭 암호화로 저장
- 계정 파일: `accounts/accounts.yaml` (`.gitignore`로 git 제외)
- 터미널 입력 이력: `~/.account_manager/.prompt_history` (프로젝트 외부)

## 암호화 키 백업

> ⚠️ **중요**: 암호화 키를 분실하면 저장된 모든 비밀번호를 복구할 수 없습니다.

```bash
# 키 파일 위치 확인
ls -la ~/.account_manager/.key

# 안전한 곳에 백업 (USB, 외장 드라이브 등)
cp ~/.account_manager/.key /path/to/safe/backup/.key

# 복원 시
cp /path/to/safe/backup/.key ~/.account_manager/.key
chmod 600 ~/.account_manager/.key
```

## 환경 설정 (.env)

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
ACCOUNTS_DIR=accounts
MEMORY_FILE=memory/MEMORY.md
HISTORY_FILE=memory/HISTORY.md
KEY_FILE=~/.account_manager/.key
```
