# TEST.md - account_manager 테스트 계획

## 1. 단위 테스트

### security.py
- [x] `encrypt()` - 평문 암호화
- [x] `decrypt()` - 복호화 및 원문 일치
- [x] `is_encrypted()` - Fernet 문자열 감지
- [x] 키 파일 자동 생성 및 권한 설정

### storage.py
- [x] `save_account()` - 신규 계정 저장
- [x] `load_account()` - 사이트명으로 조회
- [x] `list_accounts()` - 전체 목록 반환
- [x] `search_accounts()` - 키워드 검색
- [x] 민감 필드 자동 암호화
- [x] `get_display()` - 비밀번호 마스킹/표시

### memory.py
- [ ] `record_history()` - 이력 기록
- [ ] `append_memory()` - 기억 추가
- [ ] `read_memory()` / `read_history()` - 읽기

## 2. 통합 테스트

### 슬래시 명령어
- [ ] `/list` - 계정 목록 테이블 출력
- [ ] `/show <site>` - 계정 조회 (비밀번호 마스킹)
- [ ] `/show <site>` + 비밀번호 표시 확인
- [ ] `/new` - 대화형 계정 추가
- [ ] `/history` - 이력 출력
- [ ] `/memory` - 기억 출력
- [ ] `/help` - 도움말 출력

### AI 에이전트 (Ollama 필요)
- [ ] 자연어 계정 조회
- [ ] 자연어 비밀번호 요청 → show_password=True 호출
- [ ] 자연어 계정 저장
- [ ] 자연어 비밀번호 변경 + 이력 기록
- [ ] 카테고리 기반 검색

## 3. 보안 테스트
- [ ] 비밀번호가 파일에 암호화 저장되는지 확인
- [ ] 키 파일 권한 600 확인
- [ ] 직접 편집 후 AI 업데이트 시 재암호화 확인

## 테스트 실행 방법

```bash
# 단위 테스트
uv run python -c "
from account_manager.storage import save_account, load_account, list_accounts, delete_account
from account_manager.security import encrypt, decrypt, is_encrypted
from account_manager.memory import record_history, read_history, append_memory, read_memory

# 암호화 테스트
e = encrypt('mypassword')
assert decrypt(e) == 'mypassword', 'decrypt failed'
assert is_encrypted(e), 'is_encrypted failed'
print('✓ security tests passed')

# 저장 테스트
acc = save_account('TestSite', {'이메일': 'test@test.com', '비밀번호': 'pass123'})
assert is_encrypted(acc.metadata['비밀번호']), 'password not encrypted'
loaded = load_account('TestSite')
assert loaded.site == 'TestSite', 'load failed'
display_hidden = loaded.get_display(show_password=False)
assert '****' in display_hidden, 'password not masked'
display_shown = loaded.get_display(show_password=True)
assert 'pass123' in display_shown, 'password not shown'
delete_account('TestSite')
print('✓ storage tests passed')

# 이력 테스트
record_history('TestSite', '테스트', '단위 테스트')
history = read_history()
assert 'TestSite' in history, 'history not recorded'
print('✓ memory tests passed')

print('모든 테스트 통과!')
"

# 앱 실행 테스트
uv run account-mng
```
