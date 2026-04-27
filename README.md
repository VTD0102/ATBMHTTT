# Phòng Chống Mã Độc trong Hệ Thống Thương Mại Điện Tử

Demo học thuật cho chủ đề **An Toàn Thông Tin (ATTT)** và **Bảo Mật Dữ Liệu (BMDL)** — minh họa ransomware simulator, tấn công social engineering, phát hiện, giải mã và backup trong môi trường TMĐT.

---

## Tổng Quan

Dự án gồm ba phần độc lập:

| Phần | Mô tả |
|------|-------|
| `ransomware-demo/` | Demo 2 chiều: ransomware simulator + hệ thống phòng thủ (10 tests) |
| `social-engineering/` | Demo social engineering: giả mạo "API key miễn phí" + defender chặn (6 tests) |
| `secure_ecommerce.sh` | Demo quét ClamAV, mã hóa AES-256, backup tự động |

---

## Phần 1 — Ransomware Demo (Attacker vs Defender)

> ⚠️ **MÔI TRƯỜNG HỌC THUẬT — DEMO ONLY**
> Simulator chỉ mã hóa file trong thư mục `sandbox/`, không đụng đến system file.

### Cấu Trúc

```
ransomware-demo/
├── attacker/
│   ├── ransomware_simulator.py   # Mã hóa Fernet, sandbox-only
│   ├── ransom_note.html          # UI màn hình "bị khóa" (đếm ngược 72h)
│   └── sandbox/                  # Thư mục bị "tấn công"
│       ├── invoice_2024.txt
│       ├── customer_data.csv
│       └── contract.txt
├── defender/
│   ├── scanner.py                # Phát hiện: entropy + extension + signature
│   ├── decryptor.py              # Giải mã với saved key
│   ├── backup_manager.py         # Backup tar.gz + restore
│   └── rules/ransomware.yar     # YARA rules (3 rules)
├── tests/                        # 10 tests, tất cả pass
├── demo_run.sh                   # Script chạy full demo 9 bước
└── requirements.txt
```

### Cài Đặt

```bash
cd ransomware-demo
pip install -r requirements.txt
```

### Chạy Demo (9 Bước Tự Động)

```bash
cd ransomware-demo
bash demo_run.sh
```

Demo sẽ thực hiện tuần tự:

| Bước | Hành động | Công cụ |
|------|-----------|---------|
| 1 | Backup dữ liệu sandbox | `backup_manager.py` |
| 2 | Hiển thị trạng thái TRƯỚC tấn công | `ls` |
| 3 | **Mã hóa** (attacker) | `ransomware_simulator.py` |
| 4 | Hiển thị trạng thái SAU tấn công | `ls` |
| 5 | Quét phát hiện ransomware | `scanner.py` |
| 6 | Quét YARA rules | `yara-python` |
| 7 | Mở màn hình "bị khóa" trong browser | `ransom_note.html` |
| 8 | **Giải mã** (defender) | `decryptor.py` |
| 9 | Hiển thị trạng thái SAU giải mã | `ls` |

### Chạy Từng Thành Phần

```bash
cd ransomware-demo

# Attacker: mã hóa sandbox
python3 attacker/ransomware_simulator.py

# Defender: quét phát hiện
python3 defender/scanner.py attacker/sandbox/

# Defender: giải mã
python3 defender/decryptor.py attacker/sandbox/

# Defender: backup
python3 defender/backup_manager.py backup

# Xem màn hình ransom note
firefox attacker/ransom_note.html
```

### Chạy Tests

```bash
cd ransomware-demo
python3 -m pytest tests/ -v
# 10 passed
```

### Cơ Chế Phát Hiện (Scanner)

| Phương pháp | Mô tả | Độ chính xác |
|-------------|-------|-------------|
| Extension check | Phát hiện `.encrypted`, `.locked`, `.crypto` | HIGH |
| Entropy analysis | File mã hóa có entropy > 5.5 bits | MEDIUM |
| Signature detection | Tìm `RANSOMWARE_SIMULATOR_DEMO_SAFE` | CRITICAL |

### YARA Rules

| Rule | Phát hiện | Severity |
|------|-----------|---------|
| `RansomwareSimulator_Demo` | Simulator source code | CRITICAL |
| `EncryptedFilePattern` | Fernet token header | HIGH |
| `RansomNoteHTML` | Ransom note HTML | HIGH |

### Tech Stack

| Thư viện | Mục đích |
|----------|---------|
| `cryptography` (Fernet) | Mã hóa symmetric AES-128-CBC |
| `yara-python` | Pattern matching rules |
| `pytest` | Test suite |

---

## Phần 2 — Social Engineering Demo

> ⚠️ **MÔI TRƯỜNG HỌC THUẬT — DEMO ONLY**
> Kịch bản: nạn nhân bị lừa tải "phần mềm kích hoạt GPT API key miễn phí" — thực chất là ransomware.

### Cấu Trúc

```
social-engineering/
├── attacker/
│   ├── fake_landing.html        # Landing page giả "Get Free GPT-4 API Key"
│   ├── fake_key_generator.html  # UI sinh key giả + progress bar
│   ├── fake_installer.py        # Installer giả — chạy ransomware ngầm
│   └── victim_sandbox/          # Files "của nạn nhân" bị mã hóa
├── defender/
│   ├── static_analyzer.py       # Phân tích tĩnh: YARA + string scan
│   └── behavior_monitor.py      # Theo dõi filesystem khi chạy
├── prevention_success.html      # UI "Defender đã chặn thành công"
├── demo_social.sh               # Script demo chính
└── tests/                       # 6 tests, tất cả pass
```

### Cài Đặt

```bash
cd ransomware-demo
pip install -r requirements.txt   # Tái dụng cùng dependencies
```

### Chạy Demo

**Kịch bản 1 — Tấn công không có phòng thủ:**

```bash
cd social-engineering
bash demo_social.sh --attack-only
```

| Bước | Hành động |
|------|-----------|
| 1 | Backup victim_sandbox |
| 2 | Mở fake landing page trong browser |
| 3 | Mở fake key generator |
| 4 | Chạy fake_installer.py (ransomware mã hóa ngầm) |
| 5 | Hiển thị victim_sandbox sau tấn công (toàn `.encrypted`) |
| 6 | Mở ransom note trong browser |
| 7 | Restore victim_sandbox từ backup |

**Kịch bản 2 — Có hệ thống phòng thủ:**

```bash
cd social-engineering
bash demo_social.sh --with-defender
```

| Bước | Hành động |
|------|-----------|
| 1–3 | Giống kịch bản 1 |
| 4 | **Static analyzer quét fake_installer.py** → phát hiện CRITICAL |
| 5 | Hỏi có bỏ qua cảnh báo không (để demo behavioral tiếp theo) |
| 6 | Bật behavior monitor |
| 7 | Chạy fake_installer.py (monitored) |
| 8 | **Behavior monitor kill process** khi phát hiện `.encrypted` |
| 9 | Mở prevention_success.html |
| 10 | Restore victim_sandbox |

### Cơ Chế Phát Hiện (Defender)

| Thành phần | Phương pháp | Severity |
|-----------|-------------|---------|
| `static_analyzer.py` | YARA scan (`ransomware.yar`) | CRITICAL |
| `static_analyzer.py` | Dangerous string scan (`Fernet`, `.encrypt(`) | CRITICAL |
| `static_analyzer.py` | Suspicious import combo (`cryptography` + `os.walk` + `os.remove`) | MEDIUM |
| `behavior_monitor.py` | Filesystem snapshot: file `.encrypted` mới xuất hiện | CRITICAL |
| `behavior_monitor.py` | Filesystem snapshot: file gốc bị xóa | HIGH |

### Chạy Tests

```bash
cd social-engineering
python3 -m pytest tests/ -v
# 6 passed (4 static_analyzer + 2 behavior_monitor)
```

---

## Phần 3 — ShopSecure (ClamAV + GPG)

Demo quét antivirus và mã hóa dữ liệu TMĐT.

### Yêu Cầu

- Ubuntu 20.04 / 22.04 / 24.04
- `sudo` access

### Chạy Nhanh

```bash
# Cài đặt dependencies
sudo bash setup.sh

# Tạo dữ liệu mô phỏng
bash generate_data.sh

# Chạy demo
bash secure_ecommerce.sh
```

**Tùy chọn:**

```bash
bash secure_ecommerce.sh --fast     # Bỏ delay (nhanh hơn)
bash secure_ecommerce.sh --verbose  # Hiện output chi tiết
```

### Quy Trình (5 Bước)

| Bước | Hành động | Công cụ |
|------|-----------|---------|
| 1 | Quét malware | ClamAV |
| 2 | Cách ly mối đe dọa | bash + mv |
| 3 | Mã hóa dữ liệu nhạy cảm | GPG AES-256 |
| 4 | Backup mã hóa | rsync + tar + GPG |
| 5 | Báo cáo HTML | Python |

---

## Nguyên Tắc An Toàn

Dự án tuân theo nguyên tắc demo học thuật an toàn:

| Thành phần | Cách triển khai an toàn |
|-----------|------------------------|
| Ransomware simulator | Chỉ chạy trong `sandbox/`, hardcoded path check |
| Key mã hóa | Lưu local, không gửi đi đâu |
| Safety marker | `SIMULATOR_SIGNATURE` để scanner tự detect |
| Mẫu malware | EICAR test string (tiêu chuẩn ISO, vô hại) |
| Phạm vi chạy | Local machine, không network propagation |
