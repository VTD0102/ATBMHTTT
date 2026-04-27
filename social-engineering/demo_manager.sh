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
    print('  No backup found.')
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

MODE=""
for arg in "$@"; do
  case $arg in
    --attack-only)   MODE="attack" ;;
    --with-defender) MODE="defend" ;;
    --help)
      echo "Usage: bash demo_manager.sh [--attack-only | --with-defender]"
      echo "  --attack-only    Victim runs ProManager, files get encrypted"
      echo "  --with-defender  Static + behavioral defense stops the attack"
      exit 0 ;;
  esac
done

if [ -z "$MODE" ]; then
  echo -e "${YELLOW}Select demo mode:${NC}"
  echo "  1) --attack-only    (no defense)"
  echo "  2) --with-defender  (static + behavioral defense)"
  read -rp "Enter 1 or 2: " choice || true
  [ "$choice" = "1" ] && MODE="attack" || MODE="defend"
fi

cd "$SCRIPT_DIR"

if [ "$MODE" = "attack" ]; then
  echo -e "\n${RED}========================================
   FAKE MANAGER — ATTACK ONLY
========================================${NC}\n"

  echo -e "${GREEN}[STEP 1/6] Backing up victim_sandbox...${NC}"
  backup_sandbox; echo ""

  echo -e "${RED}[STEP 2/6] Social Engineering: Victim downloads ProManager.exe${NC}"
  echo "  Victim finds 'ProManager Suite' on a software site,"
  echo "  downloads it, and double-clicks to run."
  read -rp "  [Press Enter to launch ProManager]" || true; echo ""

  echo -e "${RED}[STEP 3/6] Victim runs ProManager.exe${NC}"
  echo "  (Enter any API key in the form and click Activate)"
  python3 attacker/fake_manager.py; echo ""

  echo -e "${RED}[STEP 4/6] victim_sandbox AFTER attack:${NC}"
  ls -la "$VICTIM_SANDBOX/"; echo ""

  echo -e "${RED}[STEP 5/6] Ransom note opened by app — check your browser${NC}"
  read -rp "  [Press Enter to restore files]" || true; echo ""

  echo -e "${GREEN}[STEP 6/6] Restoring victim_sandbox...${NC}"
  restore_sandbox; echo ""

  echo -e "${GREEN}========================================
   ATTACK DEMO COMPLETE
========================================${NC}"

elif [ "$MODE" = "defend" ]; then
  echo -e "\n${GREEN}========================================
   FAKE MANAGER — WITH DEFENDER
========================================${NC}\n"

  echo -e "${GREEN}[STEP 1/9] Backing up victim_sandbox...${NC}"
  backup_sandbox; echo ""

  echo -e "${BLUE}[STEP 2/9] Social Engineering: Victim downloads ProManager.exe${NC}"
  echo "  Before running, security team scans the file."
  read -rp "  [Press Enter to run static analysis]" || true; echo ""

  echo -e "${GREEN}[STEP 3/9] DEFENDER: Static analyzer scanning fake_manager.py...${NC}"
  python3 defender/static_analyzer.py attacker/fake_manager.py || true; echo ""

  echo -e "${RED}[STEP 4/9] ⚠ CRITICAL threats found — ProManager.exe is DANGEROUS${NC}"
  read -rp "  Bypass to demo behavioral defense? (y/N): " bypass || bypass="n"
  if [ "$bypass" != "y" ] && [ "$bypass" != "Y" ]; then
    echo -e "\n  ${GREEN}✓ Attack prevented at static analysis stage.${NC}"
    restore_sandbox
    exit 0
  fi; echo ""

  echo -e "${GREEN}[STEP 5/9] DEFENDER: Behavior monitor activated — watching victim_sandbox/${NC}"; echo ""

  echo -e "${BLUE}[STEP 6/9] Running fake_manager.py under monitoring...${NC}"
  echo "  (Enter any API key and click Activate)"
  python3 defender/behavior_monitor.py attacker/fake_manager.py "$VICTIM_SANDBOX" || true; echo ""

  echo -e "${GREEN}[STEP 7/9] Process killed by behavior monitor${NC}"; echo ""

  echo -e "${GREEN}[STEP 8/9] Prevention success page${NC}"
  open_browser "$SCRIPT_DIR/prevention_success.html"
  read -rp "  [Press Enter to restore files]" || true; echo ""

  echo -e "${GREEN}[STEP 9/9] Restoring victim_sandbox...${NC}"
  restore_sandbox; echo ""

  echo -e "${GREEN}========================================
   DEFENDER DEMO COMPLETE
========================================${NC}"
fi
