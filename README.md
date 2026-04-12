# Account Manager

AI 기반 로컬 계정 정보 관리 챗봇 - Ollama 프라이빗 모델을 사용하여 안전하게 웹사이트 가입 정보를 관리합니다.

> **지원 OS**: macOS, Linux (Windows 미지원)

## 특징

- **완전 로컬**: 모든 데이터와 AI 처리가 로컬 PC에서만 동작
- **단일 YAML**: `~/.account_manager/accounts.yaml` 한 파일로 전체 계정 관리
- **암호화 보안**: Fernet 대칭 암호화로 비밀번호 보호
- **AI 챗봇**: 자연어로 계정 정보 조회/수정
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
- account_manager 설치 (`~/.local/bin/account-mng`)
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

# 환경 설정 복사 (필요 시 수정)
cp .env.example .env
```

**실행**

```bash
uv run account-mng
```

---

## 설치 후 공통 설정

### 1. Ollama 설치 및 모델 준비

```bash
# Ollama 설치: https://ollama.ai
# 모델 다운로드 (최초 1회)
ollama pull llama3.2

# Ollama 서버 실행 (백그라운드)
ollama serve
```

### 2. 설정 파일 편집 (선택)

```bash
# curl 설치 시
vi ~/.account_manager/.env

# 클론 설치 시
vi .env
```

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2   # 사용할 Ollama 모델명
```

### 3. 프로그램 실행

```bash
account-mng
```

---

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

`accounts.yaml`을 직접 편집할 수 있습니다:

```yaml
이메일:
  gmail:
    site: Gmail
    url: https://gmail.com
    이메일: user@gmail.com
    비밀번호: gAAAAA...  # 암호화됨 (AI가 자동 처리)
    메모: 2FA 활성화
    updated: '2026-04-11'

호스팅:
  siteground:
    site: SiteGround
    url: https://siteground.com
    이메일: admin@mysite.com
    비밀번호: gAAAAA...
```

> **주의**: 비밀번호를 직접 평문으로 입력하면 다음번 AI 업데이트 시 자동 암호화됩니다.

---

## 보안

- **암호화**: Fernet 대칭 암호화 (AES-128-CBC)
- **키 파일**: `~/.account_manager/.key` (권한 600)
- **git 제외**: `accounts.yaml`, `memory/`, `.env` 등 민감 파일은 `.gitignore`로 보호

### 암호화 키 백업

> ⚠️ **중요**: 키를 분실하면 저장된 모든 비밀번호를 복구할 수 없습니다.

```bash
# 안전한 곳에 백업 (USB, 외장 드라이브 등)
cp ~/.account_manager/.key /path/to/safe/backup/.key

# 복원 시
cp /path/to/safe/backup/.key ~/.account_manager/.key
chmod 600 ~/.account_manager/.key
```
