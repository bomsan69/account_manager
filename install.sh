#!/usr/bin/env bash
# account_manager 설치 스크립트
# 사용법: curl -fsSL https://raw.githubusercontent.com/bomsan69/account_manager/master/install.sh | bash

set -euo pipefail

# ── 색상 정의 ──────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[✓]${NC} $*"; }
warn()    { echo -e "${YELLOW}[!]${NC} $*"; }
error()   { echo -e "${RED}[✗]${NC} $*" >&2; exit 1; }

# ── OS 확인 (macOS / Linux만 지원) ────────────────────────────
OS=$(uname -s)
case "$OS" in
  Darwin) OS_NAME="macOS" ;;
  Linux)  OS_NAME="Linux" ;;
  *)      error "account_manager는 macOS와 Linux에서만 지원됩니다. (현재: $OS)" ;;
esac
success "$OS_NAME 확인"

# ── Python 3.11+ 확인 ─────────────────────────────────────────
# pyenv / asdf 등 버전 관리자 환경을 고려해 버전별 명령어 대신
# 실제 사용 가능한 python3 / python 명령어의 버전만 확인합니다.
PYTHON=""
VER=""
for cmd in python3 python; do
  if command -v "$cmd" &>/dev/null 2>&1; then
    _VER=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || true)
    if [[ -z "$_VER" ]]; then continue; fi
    MAJOR=$(echo "$_VER" | cut -d. -f1)
    MINOR=$(echo "$_VER" | cut -d. -f2)
    if [[ $MAJOR -ge 3 && $MINOR -ge 11 ]]; then
      PYTHON="$cmd"
      VER="$_VER"
      break
    fi
  fi
done

# pyenv가 있으면 전역 버전으로 재시도
if [[ -z "$PYTHON" ]] && command -v pyenv &>/dev/null; then
  warn "현재 활성 Python이 3.11 미만입니다. pyenv global 버전을 확인합니다..."
  PYENV_PYTHON=$(pyenv which python3 2>/dev/null || pyenv which python 2>/dev/null || true)
  if [[ -n "$PYENV_PYTHON" ]]; then
    _VER=$("$PYENV_PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || true)
    MAJOR=$(echo "$_VER" | cut -d. -f1)
    MINOR=$(echo "$_VER" | cut -d. -f2)
    if [[ $MAJOR -ge 3 && $MINOR -ge 11 ]]; then
      PYTHON="$PYENV_PYTHON"
      VER="$_VER"
    fi
  fi
fi

if [[ -z "$PYTHON" ]]; then
  error "Python 3.11 이상이 필요합니다.\n  설치: https://www.python.org/downloads/\n  pyenv 사용 시: pyenv install 3.12 && pyenv global 3.12"
fi
success "Python $VER 확인 ($PYTHON)"

# ── pipx 설치 확인 및 설치 ────────────────────────────────────
if ! command -v pipx &>/dev/null; then
  warn "pipx가 없습니다. 설치합니다..."

  if [[ "$OS_NAME" == "macOS" ]] && command -v brew &>/dev/null; then
    brew install pipx
  else
    "$PYTHON" -m pip install --user pipx
  fi

  # PATH 등록
  "$PYTHON" -m pipx ensurepath
  # 현재 셸에서 즉시 사용 가능하도록
  export PATH="$PATH:$HOME/.local/bin"
  success "pipx 설치 완료"
else
  success "pipx $(pipx --version) 확인"
fi

# ── account_manager 설치 ──────────────────────────────────────
info "account_manager를 설치합니다..."
pipx install git+https://github.com/bomsan69/account_manager.git --force
success "account_manager 설치 완료"

# ── 데이터 디렉토리 초기화 ────────────────────────────────────
DATA_DIR="$HOME/.account_manager"
mkdir -p "$DATA_DIR/memory"

# .env 파일이 없으면 기본값으로 생성
if [[ ! -f "$DATA_DIR/.env" ]]; then
  cat > "$DATA_DIR/.env" << 'EOF'
# Ollama 설정
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# 경로 설정 (기본값은 ~/.account_manager/)
# ACCOUNTS_FILE=~/.account_manager/accounts.yaml
# MEMORY_FILE=~/.account_manager/memory/MEMORY.md
# HISTORY_FILE=~/.account_manager/memory/HISTORY.md
# KEY_FILE=~/.account_manager/.key
EOF
  success ".env 생성: $DATA_DIR/.env"
fi

# ── 완료 메시지 ───────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  account_manager 설치 완료!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  데이터 디렉토리: ${BLUE}$DATA_DIR${NC}"
echo -e "  설정 파일:       ${BLUE}$DATA_DIR/.env${NC}"
echo ""
echo -e "${YELLOW}다음 단계:${NC}"
echo "  1. Ollama 설치:      https://ollama.ai"
echo "  2. 모델 다운로드:    ollama pull llama3.2"
echo "  3. Ollama 실행:      ollama serve"
echo "  4. 프로그램 실행:    account-mng"
echo ""
echo -e "${YELLOW}⚠️  PATH 적용을 위해 새 터미널을 열거나 다음을 실행하세요:${NC}"
echo "  source ~/.bashrc  # bash"
echo "  source ~/.zshrc   # zsh"
echo ""
