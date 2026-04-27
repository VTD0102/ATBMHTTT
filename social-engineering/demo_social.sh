#!/bin/bash
set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ATTACKER_DIR="$SCRIPT_DIR/attacker"
VICTIM_SANDBOX="$ATTACKER_DIR/victim_sandbox"
BACKUP_DIR="$SCRIPT_DIR/.backups"

open_browser() {
  xdg-open "$1" 2>/dev/null || open "$1" 2>/dev/null || echo "  Open manually: $1"
}

backup_sandbox() {
  mkdir -p "$BACKUP_DIR"
  python3 - <<PYEOF
import tarfile, datetime, os
ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
archive = os.path.join('$BACKUP_DIR', f'victim_sandbox_{ts}.tar.gz')
with tarfile.open(archive, 'w:gz') as tar:
    tar.add('$VICTIM_SANDBOX', arcname='victim_sandbox')
print(f'  Backup saved: {os.path.basename(archive)}')
PYEOF
}

restore_sandbox() {
  python3 - <<PYEOF
import tarfile, glob, os, shutil
backups = sorted(glob.glob(os.path.join('$BACKUP_DIR', 'victim_sandbox_*.tar.gz')))
if not backups:
    print('  No backup found — recreating files manually.')
    exit(0)
latest = backups[-1]
shutil.rmtree('$VICTIM_SANDBOX', ignore_errors=True)
os.makedirs('$VICTIM_SANDBOX', exist_ok=True)
parent = os.path.dirname('$VICTIM_SANDBOX')
with tarfile.open(latest, 'r:gz') as tar:
    tar.extractall(path=parent, filter='data')
print(f'  Restored from: {os.path.basename(latest)}')
PYEOF
}

# ─── Parse mode ───────────────────────────────────────────
MODE=""
for arg in "$@"; do
  case $arg in
    --attack-only)   MODE="attack" ;;
    --with-defender) MODE="defend" ;;
    --help)
      echo "Usage: bash demo_social.sh [--attack-only | --with-defender]"
      echo "  --attack-only    Full attack, no defense (files get encrypted)"
      echo "  --with-defender  Static + behavioral defense stops the attack"
      exit 0 ;;
  esac
done

if [ -z "$MODE" ]; then
  echo -e "${YELLOW}Select demo mode:${NC}"
  echo "  1) --attack-only    (no defense)"
  echo "  2) --with-defender  (static + behavioral defense)"
  read -rp "Enter 1 or 2: " choice
  [ "$choice" = "1" ] && MODE="attack" || MODE="defend"
fi

cd "$SCRIPT_DIR"

# ─────────────────────────────────────────────────────────
# ATTACK-ONLY
# ─────────────────────────────────────────────────────────
if [ "$MODE" = "attack" ]; then
  echo -e "\n${RED}========================================"
  echo "   SOCIAL ENGINEERING — ATTACK ONLY"
  echo -e "========================================${NC}\n"

  echo -e "${GREEN}[STEP 1/7] Backing up victim_sandbox...${NC}"
  backup_sandbox; echo ""

  echo -e "${RED}[STEP 2/7] Victim visits fake landing page${NC}"
  open_browser "$ATTACKER_DIR/fake_landing.html"
  read -rp "  [Press Enter after viewing landing page]"; echo ""

  echo -e "${RED}[STEP 3/7] Victim enters email → fake API key generator${NC}"
  open_browser "$ATTACKER_DIR/fake_key_generator.html"
  read -rp "  [Press Enter after viewing key generator]"; echo ""

  echo -e "${RED}[STEP 4/7] Victim runs fake_installer.py${NC}"
  python3 attacker/fake_installer.py; echo ""

  echo -e "${RED}[STEP 5/7] victim_sandbox AFTER attack:${NC}"
  ls -la "$VICTIM_SANDBOX/"; echo ""

  echo -e "${RED}[STEP 6/7] Ransom note (opened by installer — check browser)${NC}"
  read -rp "  [Press Enter to continue]"; echo ""

  echo -e "${GREEN}[STEP 7/7] Restoring victim_sandbox...${NC}"
  restore_sandbox; echo ""

  echo -e "${GREEN}========================================\n   ATTACK DEMO COMPLETE\n========================================${NC}"

# ─────────────────────────────────────────────────────────
# WITH-DEFENDER
# ─────────────────────────────────────────────────────────
elif [ "$MODE" = "defend" ]; then
  echo -e "\n${GREEN}========================================"
  echo "   SOCIAL ENGINEERING — WITH DEFENDER"
  echo -e "========================================${NC}\n"

  echo -e "${GREEN}[STEP 1/10] Backing up victim_sandbox...${NC}"
  backup_sandbox; echo ""

  echo -e "${BLUE}[STEP 2/10] Victim visits fake landing page${NC}"
  open_browser "$ATTACKER_DIR/fake_landing.html"
  read -rp "  [Press Enter after viewing landing page]"; echo ""

  echo -e "${BLUE}[STEP 3/10] Victim sees fake API key generator${NC}"
  open_browser "$ATTACKER_DIR/fake_key_generator.html"
  read -rp "  [Press Enter after viewing key generator]"; echo ""

  echo -e "${GREEN}[STEP 4/10] DEFENDER: Static analyzer scanning fake_installer.py...${NC}"
  python3 defender/static_analyzer.py attacker/fake_installer.py || true; echo ""

  echo -e "${RED}[STEP 5/10] ⚠ CRITICAL threats found — installer is DANGEROUS${NC}"
  read -rp "  Bypass to demo behavioral defense? (y/N): " bypass
  if [ "$bypass" != "y" ] && [ "$bypass" != "Y" ]; then
    echo -e "\n  ${GREEN}✓ Attack prevented at static analysis stage.${NC}"
    restore_sandbox
    exit 0
  fi; echo ""

  echo -e "${GREEN}[STEP 6/10] DEFENDER: Behavior monitor activated — watching victim_sandbox/${NC}"
  echo ""

  echo -e "${BLUE}[STEP 7/10] Running fake_installer.py under monitoring...${NC}"
  python3 defender/behavior_monitor.py attacker/fake_installer.py "$VICTIM_SANDBOX" || true; echo ""

  echo -e "${GREEN}[STEP 8/10] Process killed by behavior monitor${NC}"; echo ""

  echo -e "${GREEN}[STEP 9/10] Prevention success page${NC}"
  open_browser "$SCRIPT_DIR/prevention_success.html"
  read -rp "  [Press Enter to continue]"; echo ""

  echo -e "${GREEN}[STEP 10/10] Restoring victim_sandbox...${NC}"
  restore_sandbox; echo ""

  echo -e "${GREEN}========================================\n   DEFENDER DEMO COMPLETE\n========================================${NC}"
fi
