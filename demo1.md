# Demo1: Tổng quan dự án ATBMHTTT & Khác biệt so với demo.md

> **Môn học:** An Toàn Bảo Mật Hệ Thống Thông Tin (ATBMHTTT)
> **Mục đích:** Tài liệu bổ sung cho `demo.md` — mô tả trạng thái thực tế của project và các điểm khác biệt so với `demo.md`

---

## Mục lục

1. [Tổng quan dự án](#1-tổng-quan-dự-án)
2. [Cấu trúc thư mục](#2-cấu-trúc-thư-mục)
3. [Công nghệ & công cụ](#3-công-nghệ--công-cụ)
4. [Luồng tấn công thực tế](#4-luồng-tấn-công-thực-tế)
5. [Luồng phòng thủ & phục hồi](#5-luồng-phòng-thủ--phục-hồi)
6. [Hướng dẫn chạy trên Windows](#6-hướng-dẫn-chạy-trên-windows)
7. [KHÁC BIỆT so với demo.md](#7-khác-biệt-so-với-demomd)

---

## 1. Tổng quan dự án

Dự án mô phỏng học thuật toàn bộ vòng đời tấn công ransomware qua Social Engineering vào hệ thống TMĐT, đồng thời triển khai giải pháp phòng thủ, phát hiện và phục hồi dữ liệu.

Hệ thống gồm **3 cụm chức năng**:

| Cụm | Thư mục | Vai trò |
|-----|---------|---------|
| Tấn công | `manager-agent/` + `landing-web/` | GUI ProManager giả mạo, CLI installer, landing page lừa đảo |
| Dữ liệu nạn nhân | `shop_data/` | Sandbox chứa 8 file mô phỏng dữ liệu TMĐT |
| Phòng thủ | `defender/` | HIDS, scanner, static analyzer, behavior monitor, backup, decryptor, GUI defender |

---

## 2. Cấu trúc thư mục

```
ATBMHTTT/
├── manager-agent/
│   ├── ProManagerSuite.exe       # File PyInstaller (~14 MB)
│   ├── fake_manager.py           # GUI gia mạo + engine mã hóa tích hợp
│   ├── fake_installer.py         # CLI installer giả mạo
│   └── fake_ransom.py            # Ransom note fullscreen
├── shop_data/                    # Sandbox dữ liệu nạn nhân
├── defender/
│   ├── defender_gui.py           # GUI DefenderPro (1577 dòng, 84KB)
│   ├── scanner.py                # Quét entropy + extension
│   ├── decryptor.py              # Giải mã hỗ trợ cả demo mới và Fernet cũ
│   ├── backup_manager.py         # Tạo/list/restore backup tar.gz
│   ├── static_analyzer.py        # Phân tích tĩnh + YARA
│   ├── behavior_monitor.py       # Giám sát filesystem realtime
│   └── rules/ransomware.yar      # 4 YARA rules
├── landing-web/                  # React + Vite marketing page
├── backups/                      # Backup tar.gz
├── md-file/                      # Tài liệu kỹ thuật bổ sung
├── demo.ps1                      # Script demo PowerShell (Windows)
├── demo.sh                       # Script demo Bash (Linux)
└── demo.md                       # Tài liệu demo gốc
```

---

## 3. Công nghệ & công cụ

| Thành phần | Công nghệ |
|------------|-----------|
| Ngôn ngữ chính | Python 3.10+ |
| GUI | Tkinter (cả attacker lẫn defender) |
| Biến đổi dữ liệu | `DEMO_HEADER` + Base64 (bản Windows-safe hiện tại) |
| Tương thích cũ | `cryptography.fernet.Fernet` (nhánh fallback trong decryptor) |
| Phân tích mã độc | `yara-python` + Shannon Entropy |
| Landing page | React + Vite (Node.js 18+) |
| Đóng gói exe | PyInstaller |
| Script tự động | PowerShell (`demo.ps1`) + Bash (`demo.sh`) |

---

## 4. Luồng tấn công thực tế

### 4.1 Hai đường tấn công

| Đường | File | Mô tả |
|-------|------|-------|
| GUI (chính) | `fake_manager.py` | Activation → Verifying → Dashboard → Ransom note |
| CLI | `fake_installer.py` | Giả lập cài đặt OpenAI SDK → mã hóa → ransom note |

### 4.2 Engine mã hóa — Windows-safe transform

Engine mã hóa **tích hợp trực tiếp** trong `fake_manager.py` qua hàm `trigger_encryption()`.

**Hằng số quan trọng:**

```python
DEMO_HEADER = b"ATBMHTTT_DEMO_ENCRYPTED_V1\n"
DEMO_KEY = b"ATBMHTTT_WINDOWS_DEMO_KEY"
DEMO_ORIGINAL_EXT = ".demo_original"
DEMO_ENCRYPTED_EXT = ".encrypted"
DEMO_SKIP_EXTENSIONS = {'.exe', '.py', '.ps1', '.sh', '.bat', '.so', '.dll'}
```

**Công thức biến đổi:**

```
Với mỗi file F hợp lệ:
  F.encrypted = DEMO_HEADER || Base64(bytes(F))
  F           → F.demo_original  (đổi tên, giữ nguyên nội dung gốc)
```

**Kết quả trong sandbox:**

```
Trước:                    Sau:
  invoice_2024.txt          invoice_2024.txt.encrypted
                            invoice_2024.txt.demo_original
                            .ransom_key
```

### 4.3 Timeline thực tế

```
T+0.0s  Nhấn "Activate License" (nhập API key bất kỳ)
        ├── [NGẦM] trigger_encryption() chạy trên thread riêng
        │          → Base64 transform, KHÔNG phải Fernet
T+0.0s  [HIỂN THỊ] "Verifying license key..." (fullscreen tối)
        → 4 bước giả: Connecting → Validating → Syncing → Configuring (~2.4s)
T+2.4s  [HIỂN THỊ] Dashboard ProManager Suite (light theme)
T+5.4s  self.root.after(3000) → _trigger_ransom()
        → Đóng dashboard, mở fake_ransom.py
        → Ransom note fullscreen, countdown 72h
```

### 4.4 Ransom note

- Tổng tiền chuộc: **29,000,000 VND** (trong `fake_ransom.py`)
- Mã demo bypass: `DEMO-SAFE-2024-TMDT`
- Nhập đúng mã → chỉ hiện hướng dẫn chạy `decryptor.py`, không tự giải mã

---

## 5. Luồng phòng thủ & phục hồi

### 5.1 Defender GUI — 6 panels

| Panel | Chức năng |
|-------|-----------|
| Dashboard — Live Monitor | Live Attack Feed + Quá trình phòng thủ + Stat cards |
| Phát hiện (HIDS) | Chỉ số realtime + quét thủ công (entropy + signature) |
| Cô lập & Tiêu diệt | Maintenance mode + kill process + quarantine + network isolate |
| Backup & Khôi phục | Backup định kỳ + restore + giải mã bằng key |
| Báo cáo sự cố | Xuất incident report (.txt) |
| Log | Toàn bộ log hoạt động |

### 5.2 IR Phases (NIST Framework) — 6 giai đoạn

```python
IR_PHASES = [
    ('preparation',    '1. Chuẩn bị'),
    ('identification', '2. Phát hiện'),
    ('containment',    '3. Cô lập'),
    ('emergency_bak',  '4. Backup khẩn cấp'),
    ('assessment',     '5. Đánh giá thiệt hại'),
    ('lessons',        '6. Rút kinh nghiệm'),
]
```

### 5.3 YARA Rules — 4 rules (không phải 3)

| Rule | Mô tả | Severity |
|------|--------|----------|
| `RansomwareSimulator_Demo` | Phát hiện chuỗi `RANSOMWARE_SIMULATOR_DEMO_SAFE` | CRITICAL |
| `EncryptedFilePattern` | Header Fernet token `{ 67 41 41 41 41 }` | HIGH |
| `WindowsSafeDemoTransform` | Header `ATBMHTTT_DEMO_ENCRYPTED_V1` + `.demo_original` | CRITICAL |
| `RansomNoteHTML` | Chuỗi `YOUR FILES HAVE BEEN ENCRYPTED` + `decrypt` | HIGH |

### 5.4 Decryptor — hai nhánh xử lý

```
File .encrypted
     │
     ├── Có DEMO_HEADER? ──► Nhánh Windows-safe:
     │       ├── Có .demo_original? → os.replace() về tên gốc, xóa .encrypted
     │       └── Không có? → Base64-decode, ghi file gốc, xóa .encrypted
     │
     └── Không có DEMO_HEADER ──► Nhánh Fernet (tương thích cũ):
             └── Đọc .ransom_key → Fernet(key).decrypt() → ghi file gốc
```

### 5.5 Auto-respond timeline (Defender)

```
T=0      DefenderPro khởi động → HIDS watcher thread (polling 2s)
T=2s     Phát hiện .encrypted → _auto_respond():
         ├── Bước 1/4: Xác nhận tấn công (10s delay)
         ├── Bước 2/4: Kill process + Maintenance Mode (10s delay)
         ├── Bước 3/4: Backup khẩn cấp (10s delay)
         └── Bước 4/4: Đánh giá thiệt hại + popup (10s delay)
         Tổng: ~55 giây (~1 phút)
```

---

## 6. Hướng dẫn chạy trên Windows

### Chuẩn bị

```powershell
cd "D:\GIT REPO\btl-atbm\ATBMHTTT"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv310\Scripts\activate
```

### Chạy bằng demo.ps1

```powershell
.\demo.ps1              # Full demo: attack + defense + recovery
.\demo.ps1 -AttackOnly  # Chỉ phần tấn công
.\demo.ps1 -DefendOnly  # Chỉ phần phòng thủ + phục hồi
.\demo.ps1 -Help        # Xem hướng dẫn
```

### Chạy từng phần

```powershell
# Tấn công GUI
.\.venv310\Scripts\python.exe .\manager-agent\fake_manager.py

# Tấn công CLI
.\.venv310\Scripts\python.exe .\manager-agent\fake_installer.py

# Defender GUI
.\.venv310\Scripts\python.exe .\defender\defender_gui.py

# Giải mã
.\.venv310\Scripts\python.exe .\defender\decryptor.py .\shop_data

# Quét
.\.venv310\Scripts\python.exe .\defender\scanner.py .\shop_data

# Phân tích tĩnh
$env:PYTHONIOENCODING = "utf-8"
.\.venv310\Scripts\python.exe .\defender\static_analyzer.py .\manager-agent\fake_manager.py

# Backup
.\.venv310\Scripts\python.exe .\defender\backup_manager.py backup
.\.venv310\Scripts\python.exe .\defender\backup_manager.py list
```

---

## 7. KHÁC BIỆT so với demo.md

Dưới đây là **tổng hợp tất cả điểm khác biệt** giữa `demo.md` (tài liệu gốc) và trạng thái thực tế hiện tại của project.

### 7.1 Engine mã hóa — Khác biệt LỚN NHẤT

| Nội dung | demo.md mô tả | Thực tế hiện tại |
|----------|---------------|-------------------|
| **Thuật toán** | Fernet (AES-128-CBC + HMAC-SHA256) | Base64 transform với `DEMO_HEADER` |
| **Công thức** | `Fernet(key).encrypt(data)` | `DEMO_HEADER + Base64(data)` |
| **Key** | `Fernet.generate_key()` (32 bytes random) | Chuỗi cố định `ATBMHTTT_WINDOWS_DEMO_KEY` |
| **File gốc** | `os.remove()` — xóa vĩnh viễn | `os.replace()` → `.demo_original` — giữ lại |
| **Mức độ an toàn** | Khó phục hồi nếu mất key | Luôn phục hồi được (file gốc còn nguyên) |
| **Module** | `ransomware_simulator.py` riêng biệt | `trigger_encryption()` tích hợp trong `fake_manager.py` |

**demo.md viết:**
```python
# ransomware_simulator.py
self._key = Fernet.generate_key()
Fernet(key).encrypt(data)
```

**Code thực tế:**
```python
# fake_manager.py
DEMO_HEADER = b"ATBMHTTT_DEMO_ENCRYPTED_V1\n"
with open(filepath + DEMO_ENCRYPTED_EXT, "wb") as fh:
    fh.write(DEMO_HEADER + base64.b64encode(data))
os.replace(filepath, filepath + DEMO_ORIGINAL_EXT)
```

### 7.2 Số tiền chuộc

| | demo.md | Thực tế |
|-|---------|---------|
| Số tiền | **59,000,000 VND** | **29,000,000 VND** (trong `fake_ransom.py`) |

### 7.3 Đường tấn công CLI — Không có trong demo.md

`demo.md` chỉ mô tả GUI attack qua `fake_manager.py`. Thực tế project còn có:

- **`fake_installer.py`** — CLI installer giả mạo OpenAI SDK, cũng gọi `trigger_encryption()` và mở `fake_ransom.py`

### 7.4 File `.demo_original` — Không có trong demo.md

`demo.md` mô tả file gốc bị **xóa hoàn toàn** (`os.remove`). Thực tế:

- File gốc được **đổi tên** sang `.demo_original`
- Decryptor ưu tiên restore từ `.demo_original` trước khi thử Base64/Fernet

### 7.5 YARA Rules — 4 rules thay vì 3

| | demo.md | Thực tế |
|-|---------|---------|
| Số rules | 3 rules | **4 rules** |
| Rule mới | — | `WindowsSafeDemoTransform` (phát hiện `ATBMHTTT_DEMO_ENCRYPTED_V1`) |
| `EncryptedFilePattern` | Header `{ 80 ?? ... }` (Fernet 0x80) | Header `{ 67 41 41 41 41 }` (Base64 "gAAAA") |

### 7.6 IR Phases — 6 giai đoạn, không phải 5

demo.md mô tả NIST IR Framework 6 giai đoạn ở mục lý thuyết nhưng Defender GUI thực tế hiện thị:

| Phase | demo.md (lý thuyết) | Defender GUI (thực tế) |
|-------|---------------------|----------------------|
| 1 | Chuẩn bị | ✅ Chuẩn bị |
| 2 | Phát hiện | ✅ Phát hiện |
| 3 | Cô lập | ✅ Cô lập |
| 4 | Tiêu diệt | ❌ Thay bằng **Backup khẩn cấp** |
| 5 | Phục hồi | ❌ Thay bằng **Đánh giá thiệt hại** |
| 6 | Rút kinh nghiệm | ✅ Rút kinh nghiệm |

### 7.7 Script `demo.ps1` — Không có trong demo.md

`demo.md` không đề cập script PowerShell tự động. Project thực tế có `demo.ps1` với 3 mode:

```powershell
.\demo.ps1              # Full: 9 bước tự động
.\demo.ps1 -AttackOnly  # Bước 1–4: backup → show data → attack → show result
.\demo.ps1 -DefendOnly  # Bước 5–9: static analysis → scan → decrypt → backup → show
```

### 7.8 Tốc độ mã hóa

| | demo.md | Thực tế |
|-|---------|---------|
| Delay giữa file | 5s/file hoặc 10s/file | **Không có delay** — `trigger_encryption()` chạy liên tục |
| Tổng thời gian | ~80 giây (8 file × 10s) | Gần như tức thì (Base64 rất nhanh) |

### 7.9 Decryptor — Hai nhánh thay vì một

demo.md chỉ mô tả giải mã Fernet. Code thực tế có **hai nhánh**:

1. **Nhánh Windows-safe** (ưu tiên): kiểm tra `DEMO_HEADER`, restore từ `.demo_original` hoặc Base64-decode
2. **Nhánh Fernet** (fallback): dùng `Fernet(key).decrypt()` cho bản demo cũ

### 7.10 Defender GUI — Live Attack Feed

demo.md mô tả Dashboard đơn giản. GUI thực tế có:

- **Live Attack Feed**: terminal đen real-time, hiển thị từng sự kiện với mã màu (đỏ = attack, xanh = defense, vàng = warning)
- **Quá trình phòng thủ**: 5 bước tick dần với icon
- **Tóm tắt thiệt hại**: hiển thị số file mã hóa + trạng thái backup khẩn cấp
- **Hành động nhanh**: 3 nút (Quét ngay / Cô lập ngay / Backup ngay)
- **Báo cáo sự cố**: xuất file `.txt` với format chuẩn (có mẫu thực tế)

### 7.11 Incident Report — Có mẫu thực tế

Project có mẫu incident report thực (`incident_report_20260507_012741.txt`) với format:

```
BÁO CÁO SỰ CỐ AN TOÀN THÔNG TIN — RANSOMWARE
Thời gian tạo : 2026-05-07 01:27:46
Loại mã độc   : Ransomware (ProManager Suite giả mạo)
File bị mã hóa: 1
Số backup sẵn có: 8

TIẾN ĐỘ ỨNG PHÓ:
  [DONE] 🛡 1. Chuẩn bị
  [DONE] 🔍 2. Phát hiện
  ...

HÀNH ĐỘNG ĐÃ THỰC HIỆN:
  1. HIDS phát hiện ransomware
  2. Auto-kill: fake_manager
  3. Auto Maintenance Mode
  4. Backup khẩn cấp
  5. Đánh giá thiệt hại

EVENT LOG:
  [timestamp] Từng sự kiện chi tiết
```

### 7.12 Bảng tổng hợp so sánh demo.md vs thực tế

| Hạng mục | demo.md | Thực tế (code hiện tại) |
|----------|---------|------------------------|
| Engine mã hóa | Fernet (AES-128-CBC) | Base64 transform (Windows-safe) |
| Module mã hóa | `ransomware_simulator.py` | `trigger_encryption()` trong `fake_manager.py` |
| Quản lý key | `Fernet.generate_key()` random | Chuỗi cố định `ATBMHTTT_WINDOWS_DEMO_KEY` |
| File gốc sau mã hóa | Bị xóa (`os.remove`) | Giữ lại (`*.demo_original`) |
| Số tiền chuộc | 59,000,000 VND | 29,000,000 VND |
| Đường tấn công | Chỉ GUI | GUI + CLI (`fake_installer.py`) |
| YARA rules | 3 rules | 4 rules (+`WindowsSafeDemoTransform`) |
| Delay mã hóa | 5–10s/file | Không delay (tức thì) |
| Decryptor | Chỉ Fernet | Hai nhánh: demo-first + Fernet fallback |
| Script Windows | Không đề cập | `demo.ps1` với 3 mode |
| Incident report | Không đề cập | Có mẫu thực tế + tự động xuất từ GUI |

---

> **DEMO ONLY** — Toàn bộ mã nguồn và dữ liệu chỉ phục vụ mục đích học thuật trong môi trường kiểm soát.
