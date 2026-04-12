# PLAN.md - account_manager

## 프로젝트 개요
로컬 PC에서 웹사이트 가입 정보를 안전하게 관리하는 터미널 챗봇 프로그램

## 아키텍처

### 저장 구조
- `accounts/` 디렉토리 내 사이트별 `.md` 파일
- YAML frontmatter로 구조화된 데이터 + 자유 메모 형식
- 직접 텍스트 편집기로 수정 가능

### 보안
- Fernet 대칭 암호화로 비밀번호 암호화 저장
- 암호화 키는 `~/.account_manager/.key`에 별도 저장
- 평문 표시 시 사용자 확인 요청

### 에이전트 구조 (LangChain + LangGraph)
- **Self-correction Agent**: 답변 생성 후 정확도 검증
- **Reflection Pattern**: 도구 실행 결과를 반성하여 재시도
- **Tools**: 계정 CRUD, 검색, 이력 기록

### UI
- Rich 라이브러리로 터미널 UI 구성
- 슬래시 명령어 지원
- 대화형 챗봇 인터페이스

## 디렉토리 구조
```
account_manager/
├── pyproject.toml
├── .env.example
├── .env              # 사용자 설정 (gitignore)
├── PLAN.md
├── README.md
├── TEST.md
├── accounts/         # 계정 정보 마크다운 파일들
│   └── example.md
├── memory/
│   ├── MEMORY.md     # 챗봇 장기 기억
│   └── HISTORY.md    # 변경 이력
└── src/
    └── account_manager/
        ├── __init__.py
        ├── main.py       # 진입점, CLI 루프
        ├── agent.py      # LangGraph 에이전트
        ├── tools.py      # 에이전트 도구들
        ├── storage.py    # 마크다운 파일 CRUD
        ├── security.py   # 암호화/복호화
        ├── memory.py     # MEMORY.md 관리
        └── ui.py         # Rich 터미널 UI
```

## 슬래시 명령어
| 명령어 | 설명 |
|--------|------|
| `/help` | 사용법 표시 |
| `/list` | 계정 파일 목록 |
| `/new <site>` | 새 계정 추가 |
| `/show <site>` | 계정 정보 표시 |
| `/history` | 변경 이력 조회 |
| `/memory` | 저장된 기억 조회 |
| `/clear` | 화면 지우기 |
| `/exit` | 종료 |

## 계정 파일 형식 (accounts/google.md)
```yaml
---
site: Google
url: https://google.com
category: 이메일/검색
updated: 2026-04-11
---

## 계정 정보
- **이메일**: example@gmail.com
- **비밀번호**: [암호화됨]
- **2FA**: 활성화

## 메모
- 복구 이메일: backup@email.com
```

## 구현 단계

### Phase 1: 기반 구조
- [x] 프로젝트 설정 (pyproject.toml, .env)
- [ ] storage.py - 마크다운 파일 CRUD
- [ ] security.py - Fernet 암호화

### Phase 2: 에이전트
- [ ] tools.py - LangChain 도구 정의
- [ ] agent.py - LangGraph self-correction 에이전트

### Phase 3: UI
- [ ] ui.py - Rich 터미널 인터페이스
- [ ] main.py - 슬래시 명령어 처리, 메인 루프

### Phase 4: 기억/이력
- [ ] memory.py - MEMORY.md 관리
- [ ] HISTORY.md 변경 이력 자동 기록

## 기술 스택
- Python 3.11+
- uv 패키지 관리
- LangChain + LangGraph
- Ollama (로컬 LLM)
- Rich (터미널 UI)
- cryptography (Fernet 암호화)
- python-frontmatter (마크다운 파싱)
