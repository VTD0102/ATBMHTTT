# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Academic security demo project (ATTT/BMDL — An Toàn Thông Tin / Bảo Mật Dữ Liệu). Three active folders:

| Folder | Vai trò |
|--------|---------|
| `manager-agent/` | Mã độc — fake ProManager Suite GUI + ransomware engine |
| `shop_data/` | Dữ liệu nạn nhân — file TMĐT bị mã hóa |
| `defender/` | Phần mềm bảo vệ — scanner, backup, GUI defender |

Also contains `landing-web/` (React + Vite marketing page serving the exe download).

## Commands

### Manager-Agent (Attack side)

```bash
# Run the fake ProManager GUI (attacker)
python3 manager-agent/fake_manager.py

# Run the standalone ransom note
python3 manager-agent/fake_ransom.py

# Encrypt shop_data manually
python3 manager-agent/ransomware_simulator.py

# Decrypt shop_data manually
python3 manager-agent/ransomware_simulator.py decrypt

# Build the exe (requires python3.12 + pyinstaller)
python3.12 -m PyInstaller --onefile \
    --name ProManagerSuite.exe \
    --hidden-import fake_ransom \
    --hidden-import ransomware_simulator \
    --hidden-import cryptography.fernet \
    --distpath manager-agent \
    manager-agent/fake_manager.py
# Then copy to landing-web/public/ for the web download
cp manager-agent/ProManagerSuite.exe landing-web/public/
```

### Defender (Defense side)

```bash
# Launch the GUI defender (scanner + backup)
python3 defender/defender_gui.py

# CLI tools
python3 defender/scanner.py shop_data/           # detect encrypted files
python3 defender/decryptor.py shop_data/         # restore files
python3 defender/backup_manager.py               # create backup of shop_data
python3 defender/backup_manager.py list          # list backups
python3 defender/backup_manager.py restore <path>
python3 defender/static_analyzer.py manager-agent/fake_manager.py
python3 defender/behavior_monitor.py             # real-time file watcher
```

### Landing Page (React + Vite)

```bash
cd landing-web
npm install
npm run dev      # dev server at localhost:5173
npm run build    # production build to dist/
```

> The exe download link is `/ProManagerSuite.exe` — served from `landing-web/public/ProManagerSuite.exe`.

## Architecture

### Attack Flow

```
Victim downloads ProManagerSuite.exe from landing-web
  → Runs exe (ELF, 14 MB, built with PyInstaller)
  → fake_manager.py: Activation screen (white/indigo theme)
      → API key entry → "Verifying..." fullscreen
      → Dashboard (fake PM app, sidebar + project cards)
      → After 10s: triggers fake_ransom.py
  → fake_ransom.py: Fullscreen ransom note
      → 59,000,000 VND demand, countdown timer
      → Meanwhile: ransomware_simulator.py encrypts files
        in exe's own directory (→ .encrypted)
```

### Defender Architecture

```
defender/
  defender_gui.py      — Tkinter GUI: Dashboard, Scanner, Backup, Log panels
  scanner.py           — CLI entropy + extension scanner (threshold >7.5)
  decryptor.py         — Fernet decrypt with .ransom_key
  backup_manager.py    — tar.gz backup + restore
  static_analyzer.py   — static analysis before execution
  behavior_monitor.py  — real-time inotify file watcher
  rules/ransomware.yar — YARA rules (3 rules)
```

**defender_gui.py detection logic:**
- `CRITICAL`: filename contains known bad pattern (`promanagersuite`, `fake_manager`, `ransomware`, …)
- `HIGH`: executable with Shannon entropy > 7.2 bits (packed/bundled)
- `MEDIUM`: executable with entropy 6.5–7.2 bits
- String scan for `.py`/`.sh` files: flags `RANSOMWARE_SIMULATOR_DEMO_SAFE`, `fernet.encrypt`, etc.

### Ransomware Simulator Safety

`RansomwareSimulator._is_inside_sandbox()` uses `os.path.realpath()` to ensure files outside the sandbox directory cannot be touched.

**Skip extensions:** `.exe .py .sh .bat .spec .pyz .pkg .so .dll` — the exe never encrypts itself.

**Key file:** `.ransom_key` saved alongside encrypted files; used by `decryptor.py` to restore.

## Key Details

- **Python version:** 3.10+ (uses `tarfile.extractall(filter='data')` for 3.14 compatibility)
- **Exe build:** python3.12 + PyInstaller `--onefile`; output is ELF binary named `ProManagerSuite.exe`
- **Frozen exe path:** When run as exe, `VICTIM_SANDBOX = os.path.dirname(sys.executable)` (encrypts its own folder, not `shop_data/`)
- **YARA rules:** `defender/rules/ransomware.yar` — 3 rules targeting simulator source, Fernet token headers, ransom note HTML
- **Demo unlock code for ransom note:** `DEMO-SAFE-2024-TMDT`
- **Backup dir:** `backups/` at repo root (created automatically)
