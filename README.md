# Phong Chong Ma Doc trong He Thong Thuong Mai Dien Tu

Demo hoc thuat cho chu de **An Toan Thong Tin (ATTT)** va **Bao Mat Du Lieu (BMDL)** — minh hoa tan cong ransomware qua social engineering, he thong phat hien / chan dung, va backup du lieu dinh ky.

---

## Tong Quan

| Phan | Mo ta |
|------|-------|
| **Phan 1** — `ransomware-demo/` + `social-engineering/` | Kich ban tan cong social engineering → ransomware → phat hien → phong thu (16 tests) |
| **Phan 2** — `secure_ecommerce.sh` | Backup du lieu dinh ky: quet ClamAV, ma hoa AES-256, backup tu dong |

---

## Phan 1 — Demo Ransomware qua Social Engineering

> **MOI TRUONG HOC THUAT — DEMO ONLY**
> Tat ca ma hoa chi xay ra trong thu muc sandbox — khong dong cham file he thong.

### Kich Ban Tong The

```
[Attacker]                         [Defender]
   |                                    |
   |-- fake_landing.html           static_analyzer.py
   |-- fake_key_generator.html     behavior_monitor.py
   |-- fake_installer.py      -->  scanner.py + YARA rules
   |       |                       decryptor.py
   |       v                            |
   |  victim_sandbox/ (ma hoa)     prevention_success.html
   |  ransom_note.html             ransom restored
```

**Hai kich ban demo tren 1 may:**

| Flag | Mo ta |
|------|-------|
| `--attack-only` | Khong co phong thu → bi ma hoa toan bo |
| `--with-defender` | He thong phat hien va chan truoc khi thiet hai |

### Cau Truc

```
ransomware-demo/
├── attacker/
│   ├── ransomware_simulator.py   # Ma hoa Fernet, sandbox-only
│   ├── ransom_note.html          # UI man hinh "bi khoa" (dem nguoc 72h)
│   └── sandbox/                  # Files bi "tan cong"
├── defender/
│   ├── scanner.py                # Phat hien: entropy + extension + signature
│   ├── decryptor.py              # Giai ma voi saved key
│   ├── backup_manager.py         # Backup tar.gz + restore
│   └── rules/ransomware.yar      # YARA rules (3 rules)
├── tests/                        # 10 tests
├── demo_run.sh                   # Demo 9 buoc (ransomware thuan tuy)
└── requirements.txt

social-engineering/
├── attacker/
│   ├── fake_landing.html         # Landing page gia "Get Free GPT-4 API Key"
│   ├── fake_key_generator.html   # UI sinh key gia + progress bar
│   ├── fake_installer.py         # Installer gia — chay ransomware ngam
│   └── victim_sandbox/           # Files "cua nan nhan"
├── defender/
│   ├── static_analyzer.py        # Phan tich tinh: YARA + string scan
│   └── behavior_monitor.py       # Theo doi filesystem khi chay
├── prevention_success.html       # UI "Defender da chan thanh cong"
├── demo_social.sh                # Script demo chinh (2 flag)
└── tests/                        # 6 tests
```

### Cai Dat

```bash
cd ransomware-demo
pip install -r requirements.txt
```

### Chay Demo — Kich Ban Tan Cong (Khong Co Phong Thu)

```bash
cd social-engineering
bash demo_social.sh --attack-only
```

| Buoc | Hanh dong |
|------|-----------|
| 1 | Backup victim_sandbox |
| 2 | Mo fake landing page trong browser |
| 3 | Mo fake key generator (progress bar + fake API key) |
| 4 | Chay fake_installer.py — ransomware ma hoa ngam |
| 5 | Hien thi victim_sandbox sau tan cong (toan `.encrypted`) |
| 6 | Mo ransom_note.html trong browser |
| 7 | Restore victim_sandbox tu backup |

### Chay Demo — Kich Ban Co Phong Thu

```bash
cd social-engineering
bash demo_social.sh --with-defender
```

| Buoc | Hanh dong |
|------|-----------|
| 1–3 | Giong kich ban tan cong |
| 4 | **Static analyzer quet fake_installer.py** → phat hien CRITICAL |
| 5 | Hoi co bo qua canh bao khong (de demo behavioral tiep theo) |
| 6 | Bat behavior monitor |
| 7 | Chay fake_installer.py (monitored) |
| 8 | **Behavior monitor kill process** khi phat hien `.encrypted` |
| 9 | Mo prevention_success.html |
| 10 | Restore victim_sandbox |

### Chay Demo — Ransomware Thuan Tuy (Khong Qua Social Engineering)

```bash
cd ransomware-demo
bash demo_run.sh
```

| Buoc | Hanh dong | Cong cu |
|------|-----------|---------|
| 1 | Backup sandbox | `backup_manager.py` |
| 2 | Hien thi TRUOC tan cong | `ls` |
| 3 | **Ma hoa** (attacker) | `ransomware_simulator.py` |
| 4 | Hien thi SAU tan cong | `ls` |
| 5 | Quet phat hien ransomware | `scanner.py` |
| 6 | Quet YARA rules | `yara-python` |
| 7 | Mo man hinh "bi khoa" trong browser | `ransom_note.html` |
| 8 | **Giai ma** (defender) | `decryptor.py` |
| 9 | Hien thi SAU giai ma | `ls` |

### Co Che Phat Hien

**Static Analyzer (`static_analyzer.py`):**

| Kiem tra | Phuong phap | Severity |
|----------|-------------|---------|
| YARA scan | Doi chieu `ransomware.yar` | CRITICAL |
| Dangerous string | Tim `Fernet`, `.encrypt(`, `RANSOMWARE_SIMULATOR_DEMO_SAFE` | CRITICAL |
| Suspicious combo | `cryptography` + `os.walk` + `os.remove` cung nhau | MEDIUM |

**Behavior Monitor (`behavior_monitor.py`):**

| Su kien | Phuong phap | Severity |
|---------|-------------|---------|
| File `.encrypted` moi | Filesystem snapshot polling (0.5s) | CRITICAL |
| File goc bi xoa | So sanh snapshot truoc/sau | HIGH |

**Scanner (`scanner.py`):**

| Phuong phap | Mo ta | Do chinh xac |
|-------------|-------|-------------|
| Extension check | Phat hien `.encrypted`, `.locked`, `.crypto` | HIGH |
| Entropy analysis | File ma hoa co entropy > 7.5 bits | MEDIUM |
| Signature detection | Tim `RANSOMWARE_SIMULATOR_DEMO_SAFE` | CRITICAL |

**YARA Rules (`ransomware.yar`):**

| Rule | Phat hien | Severity |
|------|-----------|---------|
| `RansomwareSimulator_Demo` | Simulator source code | CRITICAL |
| `EncryptedFilePattern` | Fernet token header | HIGH |
| `RansomNoteHTML` | Ransom note HTML | HIGH |

### Chay Tests

```bash
# Ransomware demo: 10 tests
cd ransomware-demo && python3 -m pytest tests/ -v

# Social engineering: 6 tests
cd social-engineering && python3 -m pytest tests/ -v

# Tat ca: 16 tests pass
```

### Tech Stack

| Thu vien | Muc dich |
|----------|---------|
| `cryptography` (Fernet) | Ma hoa symmetric AES-128-CBC |
| `yara-python` | Pattern matching rules |
| `pytest` | Test suite |
| `subprocess`, `os`, `time` | Stdlib — behavior monitor |

---

## Phan 2 — Backup Du Lieu Dinh Ky (ShopSecure)

Demo bao mat du lieu TMDT: quet antivirus, ma hoa, backup tu dong.

### Yeu Cau

- Ubuntu 20.04 / 22.04 / 24.04
- `sudo` access (de cai ClamAV + GPG)

### Chay Nhanh

```bash
# Cai dat dependencies
sudo bash setup.sh

# Tao du lieu mo phong
bash generate_data.sh

# Chay demo
bash secure_ecommerce.sh
bash secure_ecommerce.sh --fast     # Bo delay
bash secure_ecommerce.sh --verbose  # Hien output chi tiet
```

### Quy Trinh (5 Buoc)

| Buoc | Hanh dong | Cong cu |
|------|-----------|---------|
| 1 | Quet malware | ClamAV |
| 2 | Cach ly moi de doa | bash + mv |
| 3 | Ma hoa du lieu nhay cam | GPG AES-256 |
| 4 | Backup ma hoa dinh ky | rsync + tar + GPG |
| 5 | Bao cao HTML | Python |

---

## Nguyen Tac An Toan

| Thanh phan | Cach trien khai an toan |
|-----------|------------------------|
| Ransomware simulator | Chi chay trong `sandbox/`, kiem tra `os.path.realpath()` |
| Key ma hoa | Luu local, khong gui di dau |
| Safety marker | `SIMULATOR_SIGNATURE` de scanner tu detect |
| Mau malware | EICAR test string (tieu chuan ISO, vo hai) |
| Pham vi chay | Local machine, khong network propagation |
| HTML badges | Tat ca trang demo deu co "DEMO ONLY — Academic Environment" |
