# Account Manager

AI 기반 로컬 계정 정보 관리 챗봇 - 자연어로 웹사이트 가입 정보를 안전하게 관리합니다.

> **지원 OS**: macOS, Linux (Windows 미지원)

## Project Info

| 항목 | 값 |
|---|---|
| **Path** | `/Users/jeahyungchung/Project/claude_code/account_manager` |
| **Repository** | `https://github.com/bomsan69/account_manager` |

## 특징

- **완전 로컬**: 모든 데이터가 로컬 PC에서만 저장·처리
- **실행 비밀번호 보호**: 앱 실행 시 마스터 비밀번호 인증 (PBKDF2-SHA256)
- **멀티 LLM**: Ollama(로컬) 또는 vLLM(프라이빗 서버) 선택 가능
- **다양한 인증 방식**: 비밀번호 / OAuth / API 키 / 패스키 구분 저장
- **암호화 보안**: Fernet 대칭 암호화로 비밀번호·API 키 보호
- **AI 챗봇**: 자연어로 계정 정보 조회·저장·수정·삭제
- **일괄 등록**: CSV 파일로 여러 계정을 한 번에 가져오기
- **변경 이력**: 모든 계정 변경 사항 자동 기록
- **장기 기억**: 세션 간 중요 정보 유지

---

## 설치 방법

### 방법 1 — curl로 한 번에 설치 (권장)

```bash
  curl -fsSL https://raw.githubusercontent.com/bomsan69/account_manager/master/install.sh | bash
```

스크립트가 자동으로 처리하는 항목:
- OS 확인 (macOS / Linux만 허용)
- Python 3.10+ 확인
- pipx 미설치 시 자동 설치
- account_manager 설치 (`~/.local/bin/accounts`)
- 데이터 디렉토리 초기화 (`~/.account_manager/`)

---

### 방법 2 — 저장소 클론 후 수동 설치

개발 목적이나 코드를 직접 수정하고 싶을 때 사용합니다.

**사전 요구사항**

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) 패키지 관리자

```bash
# uv 설치 (미설치 시)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**설치**

```bash
# 저장소 클론
git clone https://github.com/bomsan69/account_manager.git
cd account_manager

# 패키지 설치
uv sync

# 환경 설정 복사 후 편집
cp .env.example .env
vi .env
```

**실행**

```bash
uv run accounts
```

---

## 코드 수정 후 로컬 재설치

로컬에서 코드를 변경한 뒤 `accounts` 명령어에 반영하는 방법입니다.

### uv로 개발 중 실행 (코드 변경 즉시 반영)

저장소 클론 후 개발하는 경우, 매번 재설치 없이 바로 실행할 수 있습니다.

```bash
uv run accounts
```

`src/` 코드를 수정하면 다음 실행 시 자동으로 반영됩니다.

---

### pipx로 전역 명령어 재설치

`accounts` 명령어를 전역에서 사용하려면 수정 후 pipx로 재설치합니다.

**방법 1 — GitHub에 푸시한 경우 (원격 소스 기준)**

```bash
pipx install git+https://github.com/bomsan69/account_manager.git --force
```

**방법 2 — 로컬 저장소 기준 (푸시 전에도 반영 가능)**

```bash
# 저장소 폴더 안에서 실행
pipx install . --force
```

설치 완료 후 `accounts` 명령어에 변경 내용이 반영됩니다.

---

### 데이터 이전 불필요

재설치해도 `~/.account_manager/` 폴더(계정 데이터, 암호화 키, 설정)는 건드리지 않습니다.
기존 데이터를 그대로 유지한 채로 업데이트됩니다.

---

## 실행 비밀번호 인증

앱 시작 시 마스터 비밀번호를 입력해야 합니다. 3회 틀리면 자동 종료됩니다.

```
비밀번호 (1/3):
```

- 비밀번호는 PBKDF2-SHA256(200,000 iterations)으로 해시하여 코드에 저장
- 평문 비밀번호는 코드 어디에도 존재하지 않음

---

## LLM 설정

`.env`의 `LLM_PROVIDER`로 AI 백엔드를 선택합니다.

### 옵션 A — Ollama (로컬, 기본값)

모든 AI 처리가 내 PC에서만 동작합니다. 외부로 데이터가 전송되지 않습니다.

```bash
# Ollama 설치: https://ollama.ai
ollama pull llama3.2   # 모델 다운로드 (최초 1회)
ollama serve           # 서버 실행
```

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

> **참고**: Intel Mac에서는 GPU 가속 없이 CPU로만 추론하여 응답이 40~115초 걸릴 수 있습니다.  
> Apple Silicon Mac이나 GPU 서버를 사용하면 정상 속도로 동작합니다.

---

### 옵션 B — vLLM (프라이빗 AI 서버)

직접 구성한 vLLM 서버에 연결합니다. OpenAI 호환 API를 제공하는 모든 서버와 호환됩니다.

```env
LLM_PROVIDER=vllm
VLLM_BASE_URL=https://your-vllm-server.example.com/v1
VLLM_MODEL=Qwen/Qwen2.5-14B-Instruct
VLLM_API_KEY=your-api-key
```

Ollama보다 빠른 응답 속도를 기대할 수 있으며, 데이터는 자신의 서버에서만 처리됩니다.

---

## 슬래시 명령어

| 명령어 | 설명 |
|--------|------|
| `/help` | 사용법 표시 |
| `/list` | 저장된 계정 목록 |
| `/categories` | 카테고리 목록 및 계정 수 |
| `/new [사이트명]` | 새 계정 추가 (대화형) |
| `/show <사이트명>` | 계정 정보 조회 |
| `/batch <파일.csv>` | CSV 파일로 계정 일괄 등록 |
| `/history [사이트명]` | 변경 이력 조회 |
| `/memory` | 저장된 기억 조회 |
| `/clear` | 화면 지우기 |
| `/exit` | 종료 |

## CSV 일괄 등록 (`/batch`)

여러 계정을 CSV 파일로 한 번에 가져올 수 있습니다.

```bash
/batch ~/sample.csv
/batch /path/to/accounts.csv
```

**CSV 형식** (`sample.csv` 참고):

```csv
site,url,category,auth_method,email,username,password,oauth_provider,oauth_account,api_key,memo
Gmail,https://gmail.com,이메일,password,user@gmail.com,,MyP@ssw0rd!,,,, 2FA 활성화
Notion,https://notion.so,업무,oauth,,,,Google,user@gmail.com,,
OpenAI,https://platform.openai.com,API,apikey,user@gmail.com,,,,,sk-proj-xxx,GPT-4 API 키
iCloud,https://icloud.com,이메일,passkey,user@icloud.com,,,,,,Face ID 등록
```

> 비밀번호·API 키는 CSV에 평문으로 적어도 저장 시 자동으로 Fernet 암호화됩니다.

---

## 자연어 사용 예시

```
> google 계정 정보 보여줘
> naver 비밀번호 알려줘
> notion은 Google로 소셜 로그인 해. user@gmail.com 계정으로 저장해줘
> openai API 키 저장해줘. sk-xxxx...
> siteground 비밀번호를 newpass456으로 변경하고 이력 남겨줘
> 이메일 API 서비스 관련 계정 목록 보여줘
```

---

## 인증 방식 (auth_method)

계정 저장 시 AI가 인증 방식을 자동으로 파악하여 구분 저장합니다.

| auth_method | 설명 | 저장 필드 |
|---|---|---|
| `password` | 이메일/아이디 + 비밀번호 | 이메일, 비밀번호 (암호화) |
| `oauth` | 소셜 로그인 (Google, GitHub 등) | oauth_provider, oauth_account |
| `apikey` | API 키 인증 | api_key (암호화) |
| `passkey` | 패스키/WebAuthn | 이메일 (비밀번호 없음) |

---

## 데이터 파일 구조

모든 데이터는 `~/.account_manager/`에 저장됩니다.

```
~/.account_manager/
├── .env              # 설정 파일
├── .key              # 암호화 키 (권한 600, 절대 공유 금지)
├── accounts.yaml     # 계정 정보 (카테고리별 구조)
└── memory/
    ├── MEMORY.md     # AI 장기 기억
    └── HISTORY.md    # 변경 이력
```

`accounts.yaml` 형식 예시:

```yaml
이메일:
  gmail:
    site: Gmail
    url: https://gmail.com
    auth_method: password
    이메일: user@gmail.com
    비밀번호: gAAAAA...   # Fernet 암호화됨
    메모: 2FA 활성화
    updated: '2026-04-14'

SNS:
  notion:
    site: Notion
    url: https://notion.so
    auth_method: oauth
    oauth_provider: Google
    oauth_account: user@gmail.com
    updated: '2026-04-14'

API:
  openai:
    site: OpenAI
    url: https://platform.openai.com
    auth_method: apikey
    이메일: user@gmail.com
    api_key: gAAAAA...    # Fernet 암호화됨
    updated: '2026-04-14'
```

> **주의**: 비밀번호·API 키를 직접 평문으로 입력하면 다음 AI 업데이트 시 자동 암호화됩니다.

---

## 보안

- **실행 인증**: 앱 시작 시 마스터 비밀번호 요구 (PBKDF2-SHA256, 200,000 iterations)
- **암호화**: Fernet 대칭 암호화 (AES-128-CBC)
- **키 파일**: `~/.account_manager/.key` (권한 600)
- **git 제외**: `accounts.yaml`, `memory/`, `.env` 등 민감 파일은 `.gitignore`로 보호
- **외부 전송 없음**: Ollama 및 프라이빗 vLLM 서버 사용 시 데이터가 외부로 나가지 않음

### 암호화 키 백업

> ⚠️ **중요**: 키를 분실하면 저장된 모든 비밀번호를 복구할 수 없습니다.

```bash
# 안전한 곳에 백업 (USB, 외장 드라이브 등)
cp ~/.account_manager/.key /path/to/safe/backup/.key

# 복원 시
cp /path/to/safe/backup/.key ~/.account_manager/.key
chmod 600 ~/.account_manager/.key
```
