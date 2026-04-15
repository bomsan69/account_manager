# CLAUDE.md — account_manager

## 개발 규칙
- 패키지 관리: `uv` 사용 (`pip install` 금지)
- 커밋: Conventional Commits 형식 (`feat(tools): ...`, `fix(agent): ...`)
- `accounts/accounts.yaml`, `memory/`, `.env` 절대 커밋 금지

## 브랜치
- `master`: Ollama 전용 (프라이버시 우선, `LLM_PROVIDER` 무시됨)
- `openai`: OpenAI 실험용 브랜치 (프로덕션 비권장)

## 알려진 이슈
- Intel Mac에서 Ollama 응답 40~115초 (CPU-only, 개선 불가)
- `REFLECTION_ENABLED=false` 권장: 소형 모델이 메타 코멘트("유지합니다") 반환하는 버그
- `recursion_limit=50` 필수: 기본값 25로는 tool 다중 호출 시 GraphRecursionError 발생
- 소형 모델(llama3.2 등) tool-calling 불안정, `glm-4.7-flash` 이상 권장
