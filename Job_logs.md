## 2026-04-14

### vLLM (Private AI 서버) 지원 추가
- `pyproject.toml` — `langchain-openai` 의존성 추가
- `src/account_manager/agent.py` — `LLM_PROVIDER=vllm` 옵션 추가, `_create_llm()` 헬퍼로 Ollama/vLLM 분기 처리
- `src/account_manager/agent.py` — vLLM 헬스체크 로직 추가 (401 인증 오류, 모델 미설정 감지)
- `uv.lock` — `langchain-openai` 설치에 따른 lock 파일 업데이트
