#!/bin/bash
set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SHOP_DATA="$SCRIPT_DIR/shop_data"
ATTACKER="$SCRIPT_DIR/manager-agent"
DEFENDER="$SCRIPT_DIR/defender"
BACKUP_DIR="$SCRIPT_DIR/backups"

MODE="full"
for arg in "$@"; do
    case $arg in
        --attack-only)  MODE="attack" ;;
        --defend-only)  MODE="defend" ;;
        --help)
            echo "Usage: bash demo.sh [--attack-only | --defend-only]"
            echo "  (no args)       Full demo: attack + defense + recovery"
            echo "  --attack-only   Chi chay phan tan cong"
            echo "  --defend-only   Chi chay phan phong thu + phuc hoi"
            exit 0 ;;
    esac
done

sep() { echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }
step() { echo -e "\n${CYAN}${BOLD}[BUOC $1]${NC} $2"; }
ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC}  $1"; }
info() { echo -e "  ${BLUE}→${NC} $1"; }

backup_shop() {
    mkdir -p "$BACKUP_DIR"
    python3 - <<PYEOF
import tarfile, datetime, os
ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
archive = os.path.join('$BACKUP_DIR', f'shop_data_{ts}.tar.gz')
with tarfile.open(archive, 'w:gz') as tar:
    tar.add('$SHOP_DATA', arcname='shop_data')
print(f"  Backup: {os.path.basename(archive)}")
PYEOF
}

restore_shop() {
    latest=$(ls -t "$BACKUP_DIR"/shop_data_*.tar.gz 2>/dev/null | head -1)
    if [ -z "$latest" ]; then warn "Khong tim thay backup."; return; fi
    rm -rf "$SHOP_DATA" && mkdir -p "$SHOP_DATA"
    python3 - <<PYEOF
import tarfile, os
with tarfile.open('$latest', 'r:gz') as tar:
    for m in tar.getmembers():
        m.name = os.path.relpath(m.name, 'shop_data')
        tar.extract(m, '$SHOP_DATA', filter='data')
print(f"  Restored from: $(basename $latest)")
PYEOF
}

echo -e "\n${BOLD}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   DEMO AN TOAN THONG TIN — ATBMHTTT     ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════╝${NC}"
echo -e "  Mode: ${YELLOW}${MODE}${NC}"

# ─────────────────────────────────────────────────
#  PHAN TAN CONG
# ─────────────────────────────────────────────────
if [ "$MODE" = "full" ] || [ "$MODE" = "attack" ]; then

    sep
    step "1" "Backup du lieu shop truoc khi tan cong"
    backup_shop
    ok "Da backup shop_data/"

    sep
    step "2" "Hien thi du lieu TMDT ban dau"
    echo ""
    ls -lh "$SHOP_DATA"

    sep
    step "3" "KICH BAN TAN CONG: Nan nhan mo ProManager Suite"
    warn "Nan nhan duoc lua nhap API key vao phan mem gia mao"
    info "Chay: python3 manager-agent/fake_manager.py"
    echo ""
    python3 "$ATTACKER/fake_manager.py"

    sep
    step "4" "Ket qua sau tan cong"
    echo ""
    ls -lh "$SHOP_DATA"
    ENCRYPTED=$(ls "$SHOP_DATA"/*.encrypted 2>/dev/null | wc -l)
    if [ "$ENCRYPTED" -gt 0 ]; then
        echo -e "\n  ${RED}⚠  $ENCRYPTED file(s) da bi ma hoa!${NC}"
    fi

fi

# ─────────────────────────────────────────────────
#  PHAN PHONG THU
# ─────────────────────────────────────────────────
if [ "$MODE" = "full" ] || [ "$MODE" = "defend" ]; then

    sep
    step "5" "Phan tich tinh (Static Analysis)"
    info "Quet file tan cong: manager-agent/fake_manager.py"
    python3 "$DEFENDER/static_analyzer.py" "$ATTACKER/fake_manager.py" || true

    sep
    step "6" "Quet phat hien ransomware trong shop_data/"
    python3 "$DEFENDER/scanner.py" "$SHOP_DATA" || true

    sep
    step "7" "Phuc hoi du lieu (Decryptor)"
    KEYFILE="$SHOP_DATA/.ransom_key"
    if [ -f "$KEYFILE" ]; then
        python3 "$DEFENDER/decryptor.py" "$SHOP_DATA"
    else
        warn "Khong tim thay .ransom_key. Phuc hoi tu backup..."
        restore_shop
    fi

    sep
    step "8" "Backup dinh ky sau khi phuc hoi"
    python3 "$DEFENDER/backup_manager.py" backup
    python3 "$DEFENDER/backup_manager.py" list

    sep
    step "9" "Ket qua sau phuc hoi"
    echo ""
    ls -lh "$SHOP_DATA"
    ok "Du lieu da duoc phuc hoi!"

fi

sep
echo -e "\n${GREEN}${BOLD}  DEMO HOAN TAT${NC}"
echo -e "  ${YELLOW}⚠  MOI TRUONG HOC THUAT — DEMO ONLY${NC}\n"
