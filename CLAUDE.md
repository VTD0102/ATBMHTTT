# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Academic security demo project (ATTT/BMDL — An Toàn Thông Tin / Bảo Mật Dữ Liệu) with two independent parts:

1. **`ransomware-demo/`** — Python-based attacker vs. defender simulation (Fernet encryption, YARA rules, entropy scanner)
2. **Root shell scripts** — ClamAV + GPG AES-256 e-commerce security demo (`secure_ecommerce.sh`)

## Commands

### Ransomware Demo (Python)

```bash
cd ransomware-demo

# Install dependencies
pip install -r requirements.txt

# Run full 9-step demo automatically
bash demo_run.sh

# Run individual components
python3 attacker/ransomware_simulator.py          # encrypt sandbox
python3 attacker/ransomware_simulator.py decrypt  # decrypt sandbox
python3 defender/scanner.py attacker/sandbox/    # detect threats
python3 defender/decryptor.py attacker/sandbox/  # restore files
python3 defender/backup_manager.py backup         # create backup
python3 defender/backup_manager.py list           # list backups

# Run all tests
python3 -m pytest tests/ -v

# Run a single test file
python3 -m pytest tests/test_simulator.py -v
python3 -m pytest tests/test_scanner.py -v
python3 -m pytest tests/test_backup.py -v
```

### ShopSecure Shell Demo

```bash
# Install system dependencies (ClamAV, GPG, rsync) — requires sudo
sudo bash setup.sh

# Generate mock e-commerce data
bash generate_data.sh

# Run the full security demo
bash secure_ecommerce.sh
bash secure_ecommerce.sh --fast     # skip delays
bash secure_ecommerce.sh --verbose  # detailed output
```

## Architecture

### Ransomware Demo (`ransomware-demo/`)

```
ATTACKER SIDE                    DEFENDER SIDE
─────────────────                ─────────────────────────────
attacker/
  ransomware_simulator.py        defender/
    → Fernet (AES-128-CBC)         scanner.py
    → sandbox-only isolation         → entropy threshold (>7.5)
    → key saved to .ransom_key       → extension check (.encrypted)
    → emits SIMULATOR_SIGNATURE      → signature string detection
  ransom_note.html               
    → countdown UI (72h)           rules/ransomware.yar
    → demo unlock code               → RansomwareSimulator_Demo
    → "DEMO ONLY" badge              → EncryptedFilePattern (Fernet header)
                                     → RansomNoteHTML
                                   decryptor.py
                                     → Fernet decrypt with .ransom_key
                                   backup_manager.py
                                     → tar.gz archive + restore
```

**Safety invariant:** `RansomwareSimulator._is_inside_sandbox()` checks `os.path.realpath()` — the simulator cannot touch files outside `attacker/sandbox/`. The string `RANSOMWARE_SIMULATOR_DEMO_SAFE` is embedded as `SIMULATOR_SIGNATURE` so the scanner can always self-detect.

**Module layout:** `attacker/` and `defender/` are Python packages (each has `__init__.py`). Tests use `sys.path.insert(0, parent_dir)` to import them without installation.

### Shell Demo (root level)

`secure_ecommerce.sh` runs a 5-step pipeline: ClamAV scan → quarantine infected files → GPG AES-256 encryption of sensitive data → rsync+tar+GPG backup → HTML report generation. It creates `website/`, `quarantine/`, `backup/`, and `logs/` directories relative to `$BASE_DIR`.

## Key Details

- **Python version:** 3.10+ (uses `tarfile.extractall(filter='data')` for 3.14 compatibility)
- **Test count:** 10 tests across 3 files, all must pass
- **YARA rules file:** `ransomware-demo/defender/rules/ransomware.yar` — 3 rules targeting simulator source, Fernet token headers, and ransom note HTML
- **Entropy threshold:** Scanner flags files with Shannon entropy > 7.5 bits (after reading first 4096 bytes)
- **Demo unlock code for ransom note UI:** `DEMO-SAFE-2024-TMDT`
