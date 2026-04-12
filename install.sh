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

# ── Python 3.10+ 확인 ─────────────────────────────────────────
_check_python_ver() {
  local cmd="$1"
  local ver
  ver=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null) || return 1
  local major minor
  major=$(echo "$ver" | cut -d. -f1)
  minor=$(echo "$ver" | cut -d. -f2)
  # 3.10 이상, 3.14 미만 (Pydantic V1 호환 범위)
  [[ $major -ge 3 && $minor -ge 10 && $minor -lt 14 ]] && echo "$ver" && return 0
  return 1
}

PYTHON=""
VER=""

# 1) 현재 PATH의 python3 / python 시도
for cmd in python3 python; do
  if command -v "$cmd" &>/dev/null 2>&1; then
    if _VER=$(_check_python_ver "$cmd"); then
      PYTHON="$cmd"; VER="$_VER"; break
    fi
  fi
done

# 2) pyenv가 있으면 설치된 버전 중 3.10+ 탐색
if [[ -z "$PYTHON" ]] && command -v pyenv &>/dev/null; then
  warn "현재 활성 Python이 3.10 미만입니다. pyenv 설치 버전을 탐색합니다..."
  while IFS= read -r pyver; do
    pyver=$(echo "$pyver" | tr -d ' *')
    [[ -z "$pyver" ]] && continue
    candidate=$(pyenv root)/versions/${pyver}/bin/python3
    [[ -x "$candidate" ]] || candidate=$(pyenv root)/versions/${pyver}/bin/python
    [[ -x "$candidate" ]] || continue
    if _VER=$(_check_python_ver "$candidate"); then
      PYTHON="$candidate"; VER="$_VER"
      warn "pyenv $pyver 버전을 사용합니다."
      break
    fi
  done < <(pyenv versions --bare 2>/dev/null | sort -Vr)
fi

if [[ -z "$PYTHON" ]]; then
  error "Python 3.10 이상 3.14 미만이 필요합니다. (Pydantic 호환 범위)\n  설치: https://www.python.org/downloads/\n  pyenv 사용 시: pyenv install 3.12 && pyenv global 3.12"
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
info "account_manager를 설치합니다... (Python $VER 사용)"

# 기존 venv가 다른 Python 버전으로 만들어져 있으면 충돌하므로 무조건 제거 후 재설치
warn "기존 account-manager 설치가 있으면 제거합니다..."
pipx uninstall account-manager 2>/dev/null || true

# --python 으로 확인된 버전을 명시적으로 지정 (--force 없이 fresh install)
pipx install git+https://github.com/bomsan69/account_manager.git \
  --python "$PYTHON"
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
