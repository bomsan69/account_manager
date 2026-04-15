## 2026-04-15

### /new 명령어 auth_method 선택 흐름 추가
- `src/account_manager/main.py` — /new 등록 시 password/oauth/apikey/passkey 방식 선택 메뉴 추가 및 방식별 입력 필드 분기 처리

### commit-push-pr 스킬 수정 (job-log 자동 실행)
- `~/.claude/plugins/…/commit-push-pr.md` (3개 파일) — 커밋 전 job-log 스킬을 먼저 실행하도록 순서 변경, `Skill` allowed-tools 추가

## 2026-04-14

### vLLM (Private AI 서버) 지원 추가
- `pyproject.toml` — `langchain-openai` 의존성 추가
- `src/account_manager/agent.py` — `LLM_PROVIDER=vllm` 옵션 추가, `_create_llm()` 헬퍼로 Ollama/vLLM 분기 처리
- `src/account_manager/agent.py` — vLLM 헬스체크 로직 추가 (401 인증 오류, 모델 미설정 감지)
- `uv.lock` — `langchain-openai` 설치에 따른 lock 파일 업데이트
