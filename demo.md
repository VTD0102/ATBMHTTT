# Báo cáo Demo: Ransomware & Phòng thủ trên hệ thống TMĐT

> **Môn học:** An Toàn Bảo Mật Hệ Thống Thông Tin (ATBMHTTT)  
> **Loại demo:** Mô phỏng học thuật — Academic/Educational Environment  
> **Công cụ:** Python 3.12 · Tkinter · Fernet · React + Vite · PyInstaller

---

## Mục lục

1. [Phần I — Ransomware](#phần-i--ransomware)
   - [1.1 Phương thức tấn công](#11-phương-thức-tấn-công-social-engineering--ransomware)
   - [1.2 Kịch bản tấn công chi tiết](#12-kịch-bản-tấn-công-chi-tiết)
   - [1.3 Giải thuật mã hóa](#13-giải-thuật-mã-hóa)
2. [Phần II — Phòng thủ](#phần-ii--phòng-thủ)
   - [2.1 Kiến trúc hệ thống phòng thủ](#21-kiến-trúc-hệ-thống-phòng-thủ)
   - [2.2 Các biện pháp demo đã triển khai](#22-các-biện-pháp-demo-đã-triển-khai)
   - [2.3 Quy trình ứng phó sự cố (IR Framework)](#23-quy-trình-ứng-phó-sự-cố-ir-framework)

---

# Phần I — Ransomware

## 1.1 Phương thức tấn công: Social Engineering + Ransomware

Kịch bản này kết hợp hai kỹ thuật tấn công:

| Giai đoạn | Kỹ thuật | Công cụ demo |
|-----------|----------|--------------|
| Phát tán  | Trang web giả mạo SaaS (Phishing Site) | `landing-web/` — React + Vite |
| Dụ dỗ    | Social Engineering: gửi API key qua email để nạn nhân tin tưởng | Email giả lập |
| Thực thi  | Nạn nhân tự tải và chạy file exe | `ProManagerSuite.exe` — PyInstaller ELF |
| Che giấu  | GUI hợp lệ (fake PM dashboard) trong khi mã hóa ngầm | `fake_manager.py` |
| Tống tiền | Ransom note fullscreen, yêu cầu 59,000,000 VND | `fake_ransom.py` |

### Sơ đồ vector tấn công

```
┌─────────────────────────────────────────────────────────────────────┐
│                    VECTOR TẤN CÔNG SOCIAL ENGINEERING               │
└─────────────────────────────────────────────────────────────────────┘

  [Kẻ tấn công]
       │
       ├─① Dựng trang web quảng cáo giả (ProManager Suite SaaS)
       │        landing-web/ ──► "AI-powered PM platform"
       │
       ├─② Gửi email chứa API key (tạo sự tin tưởng)
       │        "Your API key: sk-PM3-xxxx-xxxx"
       │
       ▼
  [Nạn nhân]
       │
       ├─③ Truy cập web, đọc testimonials/features → tin tưởng
       │
       ├─④ Tải ProManagerSuite.exe (14 MB, ELF/PyInstaller)
       │
       ├─⑤ Chạy exe → Màn hình Activation (nhập API key)
       │
       └─⑥ Nhấn "Activate" ──────────────────────────────────────────►
                                                                       │
                              ┌────────────────────────────────────────┘
                              │  MALWARE KÍCH HOẠT
                              │
                              ├─ Thread A: Mã hóa file (ngay lập tức)
                              │       ransomware_simulator.encrypt()
                              │       file.txt → file.txt.encrypted
                              │
                              ├─ Thread B: Hiện GUI giả ("Verifying...")
                              │       → Dashboard fake ProManager
                              │       (che giấu hành vi mã hóa)
                              │
                              └─ Sau ~5s: Ransom note fullscreen
                                      59,000,000 VND · Countdown 72h
```

---

## 1.2 Kịch bản tấn công chi tiết

### Dòng thời gian (Timeline)

```
T+0.0s  Nạn nhân nhấn "Activate License" (nhập API key bất kỳ)
         │
         ├── [NGẦM] ransomware_simulator.encrypt() khởi động
         │          → quét thư mục, bỏ qua .exe/.py/.dll
         │          → mã hóa từng file bằng Fernet
         │
T+0.0s  [HIỂN THỊ] Màn hình "Verifying license key..." (dark, fullscreen)
         → 4 bước giả: Connecting → Validating → Syncing → Configuring
         (tổng ~2.4 giây)
         │
T+2.4s  [HIỂN THỊ] Dashboard ProManager Suite (light theme, fullscreen)
         → Sidebar, project cards, task list, progress bars
         → "Syncing workspace data..." (progress bar chạy mãi)
         │
         ├── [NGẦM] Mã hóa đang hoàn tất các file còn lại
         │
T+5.4s  [KÍCH HOẠT] Ransom note fullscreen
         → Skull + tiêu đề nhấp nháy đỏ
         → "59,000,000 VND" — font 48pt, màu amber
         → Countdown 72 giờ
         → Ô nhập unlock code (demo: DEMO-SAFE-2024-TMDT)
```

### Sơ đồ luồng tấn công (Flowchart)

```
                    ╔══════════════════╗
                    ║  Nạn nhân mở    ║
                    ║ ProManagerSuite  ║
                    ║      .exe        ║
                    ╚════════╤═════════╝
                             │
                    ╔════════▼═════════╗
                    ║  Màn hình nhập  ║
                    ║    API Key       ║
                    ║  (½ màn hình)   ║
                    ╚════════╤═════════╝
                             │ Nhập key bất kỳ + Enter
                ┌────────────┴────────────┐
                │                         │
       [Thread A — Ẩn]           [Thread B — Hiện]
                │                         │
    ╔═══════════▼═══════════╗   ╔═════════▼═════════╗
    ║  RansomwareSimulator  ║   ║  "Verifying..."   ║
    ║  .encrypt()           ║   ║  Màn hình tối    ║
    ║                       ║   ║  fullscreen       ║
    ║  ┌─────────────────┐  ║   ╚═════════╤═════════╝
    ║  │ os.walk(sandbox)│  ║             │ ~2.4s
    ║  │ skip .exe/.py   │  ║   ╔═════════▼═════════╗
    ║  │ Fernet.encrypt()│  ║   ║  Dashboard giả    ║
    ║  │ file → .encrypt.│  ║   ║  ProManager Suite ║
    ║  │ save .ransom_key│  ║   ║  fullscreen       ║
    ║  └─────────────────┘  ║   ╚═════════╤═════════╝
    ╚═══════════════════════╝             │ ~3s
                │                         │
                └────────────┬────────────┘
                             │
                    ╔════════▼═════════╗
                    ║   RANSOM NOTE   ║
                    ║  Fullscreen     ║
                    ║  59,000,000 VND ║
                    ║  Countdown 72h  ║
                    ╚═════════════════╝
```

### Danh sách file bị mã hóa (Shop Data)

| File gốc | File sau tấn công | Nội dung |
|----------|-------------------|----------|
| `invoice_2024.txt` | `invoice_2024.txt.encrypted` | Hóa đơn khách hàng |
| `customer_data.csv` | `customer_data.csv.encrypted` | CSDL khách hàng, email, SĐT |
| `contract.txt` | `contract.txt.encrypted` | Hợp đồng dịch vụ $50,000/năm |
| `api_config.json` | `api_config.json.encrypted` | API key, DB credentials |
| `business_report.csv` | `business_report.csv.encrypted` | Báo cáo doanh thu |
| `orders_2024.csv` | `orders_2024.csv.encrypted` | Dữ liệu đơn hàng |
| `db_credentials.txt` | `db_credentials.txt.encrypted` | Mật khẩu database production |
| `project_data.txt` | `project_data.txt.encrypted` | Thông tin dự án nội bộ |

---

## 1.3 Giải thuật mã hóa

Demo sử dụng **Fernet** — symmetric encryption chuẩn từ thư viện `cryptography` của Python.

### Cấu trúc Fernet

```
Fernet = AES-128-CBC  +  HMAC-SHA256  +  Base64url

┌──────────────────────────────────────────────────────┐
│                  FERNET KEY (32 bytes)               │
│                                                      │
│  [ 16 bytes signing key ] [ 16 bytes encryption key ]│
│       (HMAC-SHA256)            (AES-128-CBC)         │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│                FERNET TOKEN (output)                 │
│                                                      │
│  Version(1B) │ Timestamp(8B) │ IV(16B) │ Ciphertext  │
│              │               │         │ + HMAC(32B) │
│    0x80      │  Unix epoch   │ random  │             │
└──────────────────────────────────────────────────────┘
```

### Quy trình mã hóa từng file

```
plaintext_file
      │
      ▼
  đọc bytes
      │
      ▼
 Fernet(key).encrypt(data)
      │  ┌─────────────────────────────┐
      │  │ 1. Sinh IV ngẫu nhiên 16B  │
      │  │ 2. AES-128-CBC encrypt      │
      │  │ 3. HMAC-SHA256 ký token     │
      │  │ 4. Base64url encode         │
      │  └─────────────────────────────┘
      │
      ▼
 ghi ra file.txt.encrypted
      │
      ▼
 xóa file gốc (os.remove)
```

### Quản lý khóa

```python
# ransomware_simulator.py
def _get_or_create_key(self) -> bytes:
    if os.path.exists(self.key_file):      # .ransom_key đã tồn tại
        with open(self.key_file, "rb") as f:
            self._key = f.read()           # tái sử dụng khóa cũ
    else:
        self._key = Fernet.generate_key()  # sinh khóa mới (32B random)
        with open(self.key_file, "wb") as f:
            f.write(self._key)             # lưu tại shop_data/.ransom_key
```

> **Ghi chú thực tế:** Ransomware thực (LockBit, REvil) dùng **RSA-2048** để mã hóa khóa Fernet/AES, khóa giải mã chỉ có ở máy chủ kẻ tấn công. Demo này lưu khóa cục bộ để có thể phục hồi trong môi trường học thuật.

### So sánh: Demo vs Ransomware thực

| Đặc điểm | Demo (Fernet) | Ransomware thực (LockBit/REvil) |
|-----------|--------------|----------------------------------|
| Mã hóa đối xứng | AES-128-CBC | AES-256-CBC / ChaCha20 |
| Bảo vệ khóa | Lưu local (`.ransom_key`) | RSA-2048/4096 encrypt, gửi C2 |
| Phạm vi | Sandbox giới hạn | Toàn bộ ổ đĩa + network share |
| Exfiltration | Không | Có (double extortion) |
| Anti-analysis | Không | Obfuscation, anti-VM, anti-debug |
| Phục hồi | Có thể (key local) | Gần như bất khả thi |

---

# Phần II — Phòng thủ

## 2.1 Kiến trúc hệ thống phòng thủ

```
┌─────────────────────────────────────────────────────────────────────┐
│                    HỆ THỐNG PHÒNG THỦ (DefenderPro)                │
└─────────────────────────────────────────────────────────────────────┘

  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
  │   PHÁT HIỆN      │    │   CÔ LẬP         │    │   PHỤC HỒI       │
  │   (Detection)    │    │   (Containment)  │    │   (Recovery)     │
  │                  │    │                  │    │                  │
  │ • HIDS watcher   │───►│ • pkill procs    │───►│ • Fernet decrypt │
  │ • Entropy scan   │    │ • Maintenance    │    │ • Backup restore │
  │ • String match   │    │   Mode flag      │    │ • tar.gz archive │
  │ • Process check  │    │ • Quarantine exe │    │                  │
  │ • File ext check │    │ • Network isolate│    │                  │
  └──────────────────┘    └──────────────────┘    └──────────────────┘
           │                       │                       │
           └───────────────────────┴───────────────────────┘
                                   │
                         ┌─────────▼─────────┐
                         │   DEFENDER GUI    │
                         │   (Tkinter)       │
                         │                  │
                         │ Dashboard        │
                         │ Phát hiện (HIDS) │
                         │ Cô lập & Tiêu diệt│
                         │ Phục hồi         │
                         │ Báo cáo sự cố    │
                         │ Log              │
                         └──────────────────┘
```

---

## 2.2 Các biện pháp demo đã triển khai

### Biện pháp 1 — HIDS: Giám sát file realtime

**Nguyên lý:** Host-based IDS theo dõi số lượng file `.encrypted` trong sandbox mỗi 2 giây. Khi phát hiện gia tăng đột biến → kích hoạt ứng phó tự động.

```python
# defender/defender_gui.py — _watch_loop()
def _watch_loop(self):
    prev_enc = _count_encrypted(_VICTIM_DIR)
    while True:
        time.sleep(2)                          # polling mỗi 2 giây
        enc = _count_encrypted(_VICTIM_DIR)
        if enc > prev_enc and not self._under_attack:
            self._under_attack = True
            self._auto_respond()               # kích hoạt tự động
        prev_enc = enc
```

```
Trước tấn công:    shop_data/  →  8 file plaintext
Trong tấn công:    shop_data/  →  file.txt + file.txt.encrypted  (đang xử lý)
Sau tấn công:      shop_data/  →  8 file .encrypted  ← HIDS phát hiện
```

**Ngưỡng phát hiện:**
| Chỉ số | Bình thường | Cảnh báo |
|--------|-------------|----------|
| File `.encrypted` | 0 | ≥ 1 (mới xuất hiện) |
| Entropy file exe | < 6.5 bits | > 7.2 bits → HIGH |
| Tên file | — | Chứa "ransomware", "promanager" → CRITICAL |

---

### Biện pháp 2 — Static Analysis: Entropy + Chữ ký

**Nguyên lý:** Kết hợp phát hiện dựa trên chữ ký (Signature-based) và dị thường (Anomaly-based) để phân tích file trước khi thực thi.

```
                    PHÂN TÍCH FILE (analyze_file)
                           │
              ┌────────────┼────────────┐
              │            │            │
      [Tên file]    [Entropy]    [String scan]
              │            │            │
              ▼            ▼            ▼
    Khớp pattern?   Is executable?  Chứa chuỗi nguy hiểm?
    promanager,     ELF/PE magic    RANSOMWARE_SIMULATOR
    fake_manager,   bytes?          fernet.encrypt
    ransomware...        │          Fernet.generate_key
              │          │            │
              ▼          ▼            ▼
           CRITICAL    entropy      CRITICAL
                      > 7.2 → HIGH
                      > 6.5 → MED
```

**Công thức tính Shannon Entropy:**

```
H(X) = -∑ p(x) × log₂(p(x))

Trong đó:
  p(x) = tần suất byte x / tổng số byte đọc (max 64KB đầu file)

File bình thường (text):  H ≈ 4.5 – 6.0 bits
File nén/đóng gói:        H ≈ 7.2 – 7.9 bits  → nghi ngờ
File mã hóa (Fernet):     H ≈ 7.9 – 8.0 bits  → cao nhất
```

---

### Biện pháp 3 — Auto-Containment: Dừng tiến trình tự động

**Nguyên lý:** Khi HIDS phát hiện tấn công, defender tự động `pkill` các tiến trình nguy hiểm mà không cần thao tác thủ công.

```
HIDS phát hiện .encrypted mới
           │
           ▼
    _auto_respond() [chạy trong main thread]
           │
    ┌──────┴──────────────────────────────────────────┐
    │                                                  │
    ▼                                                  ▼
pkill -f ProManagerSuite              Tạo MAINTENANCE.flag
pkill -f fake_manager                 (ngừng giao dịch mới)
pkill -f fake_ransom
           │
           ▼
    Tạo NETWORK_ISOLATED.flag     (mô phỏng ngắt mạng)
           │
           ▼
    Backup khẩn cấp shop_data/    (tar.gz → backups/)
           │
           ▼
    Popup cảnh báo + banner đỏ Dashboard
```

> **Lưu ý thực tế:** Trong kịch bản thực, bước này tương đương rút cáp mạng / ngắt vSwitch. **Tuyệt đối không tắt nguồn** — khóa giải mã có thể đang lưu trong RAM.

---

### Biện pháp 4 — Backup định kỳ (Preparation)

**Nguyên lý:** Backup proactive trước khi bị tấn công là biện pháp phòng thủ quan trọng nhất. Khi bị ransomware, backup sạch là giải pháp duy nhất nếu không có khóa giải mã.

```
CẤU TRÚC BACKUP:
  backups/
  ├── backup_20241015_090000.tar.gz   ← backup tự động (6h/lần)
  ├── backup_20241015_150000.tar.gz
  └── shop_data_20241028_180000.tar.gz ← backup trước demo

BACKUP PROCEDURE (backup_manager.py):
  shop_data/          →    tar -czf backup_TIMESTAMP.tar.gz
  [plaintext files]         [compressed archive]
                                   │
                                   ▼
                             backups/backup_*.tar.gz

RESTORE PROCEDURE:
  backups/backup_X.tar.gz  →  tarfile.extractall()  →  shop_data/
```

**Lịch backup được cấu hình:**
- Tự động: có thể chọn 1h / 3h / 6h / 12h / 24h
- Khẩn cấp: tự động trigger khi HIDS phát hiện tấn công

---

### Biện pháp 5 — Recovery: Giải mã Fernet

**Nguyên lý:** Nếu tìm thấy `.ransom_key` (trong demo, khóa lưu cục bộ), có thể giải mã toàn bộ file bị ảnh hưởng.

```
GIẢI MÃ (decryptor.py / defender_gui.py):

shop_data/.ransom_key  (32 bytes Fernet key)
         │
         ▼
    Fernet(key).decrypt(encrypted_data)
         │  ┌──────────────────────────────┐
         │  │ 1. Xác thực HMAC-SHA256     │
         │  │ 2. AES-128-CBC decrypt       │
         │  │ 3. Xác nhận timestamp        │
         │  └──────────────────────────────┘
         │
         ▼
file.txt.encrypted  →  file.txt  (plaintext phục hồi)
         │
         ▼
    os.remove(enc_path)   (xóa file mã hóa)
```

---

### Biện pháp 6 — YARA Rules (Static Analyzer)

**Nguyên lý:** Quét file nguồn bằng YARA rules để nhận diện mã độc đã biết trước khi thực thi.

```yara
// defender/rules/ransomware.yar

rule RansomwareSimulator_Demo {
    strings:
        $sig = "RANSOMWARE_SIMULATOR_DEMO_SAFE"
    condition:
        $sig
}

rule EncryptedFilePattern {
    strings:
        $fernet_header = { 80 ?? ?? ?? ?? ?? ?? ?? ?? }
    condition:
        $fernet_header at 0
}

rule RansomNoteHTML {
    strings:
        $ransom = "DEMO-SAFE-2024-TMDT"
    condition:
        $ransom
}
```

---

## 2.3 Quy trình ứng phó sự cố (IR Framework)

Hệ thống phòng thủ demo tuân theo **NIST Incident Response Framework** gồm 6 giai đoạn, áp dụng riêng cho ransomware:

```
┌─────────────────────────────────────────────────────────────────────────┐
│              NIST IR FRAMEWORK — Ransomware Playbook                    │
└─────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐
  │ 1. CHUẨN BỊ │  Backup định kỳ · YARA rules · HIDS watcher khởi động
  │ Preparation  │  defender_gui.py khởi động → giai đoạn này = DONE
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ 2. PHÁT HIỆN │  HIDS polling 2s · entropy scan · process check
  │Identification│  → File .encrypted xuất hiện → ALERT
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │  3. CÔ LẬP  │  pkill bad procs · Maintenance Mode · Network isolate
  │ Containment  │  ⚠ KHÔNG TẮT NGUỒN — bảo toàn RAM keys cho Forensics
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ 4. TIÊU DIỆT│  Quarantine exe · Remove malware files
  │  Eradication │  Quarantine folder · MAINTENANCE.flag
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ 5. PHỤC HỒI │  Fernet decrypt (nếu có .ransom_key)
  │   Recovery   │  Restore từ backup (nếu không có key)
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │6. RÚT KINH  │  Báo cáo sự cố · Cập nhật YARA rules
  │  NGHIỆM     │  Update Playbook · Đào tạo nhân viên
  └──────────────┘
```

### Bảng tổng hợp: Dấu hiệu → Biện pháp → Công cụ demo

| Dấu hiệu phát hiện | Biện pháp ứng phó | Công cụ demo |
|---------------------|-------------------|--------------|
| File `.encrypted` xuất hiện | Auto-containment + alert | `defender_gui.py → _auto_respond()` |
| Tiến trình lạ (ProManagerSuite) | `pkill -f` kill ngay | `subprocess.run(['pkill', ...])` |
| Entropy exe > 7.2 bits | Cảnh báo CRITICAL | `analyze_file() → _entropy()` |
| Tên file khớp pattern | Cảnh báo CRITICAL | `_BAD_NAMES` set matching |
| Chuỗi nguy hiểm trong source | CRITICAL flag | `_BAD_STRINGS` byte scan |
| `.ransom_key` xuất hiện | Ghi log, đề xuất giải mã | HIDS + Recovery panel |
| Không có key | Restore từ backup | `BackupManager.restore()` |

### Sơ đồ luồng phòng thủ — thời gian thực

```
T=0      Defender GUI khởi động
          └── HIDS watcher thread chạy nền (polling 2s)
          └── Giai đoạn Chuẩn bị = DONE ✓
          └── Backup định kỳ lên lịch (6h default)

T=0      [Song song] Nạn nhân mở ProManagerSuite.exe, nhập API key
          └── Encryption bắt đầu ngay lập tức (background thread)

T=2s     HIDS phát hiện file .encrypted đầu tiên xuất hiện
          └── _under_attack = True
          └── _auto_respond() kích hoạt:
               ├── [0.0s] pkill ProManagerSuite, fake_manager, fake_ransom
               ├── [0.1s] Tạo MAINTENANCE.flag
               ├── [0.2s] Tạo NETWORK_ISOLATED.flag
               ├── [0.3s] Backup khẩn cấp shop_data/ → backups/
               └── [0.8s] Popup cảnh báo + Banner đỏ Dashboard

T=4s     Giao diện defender cập nhật:
          └── Phase tracker: Phát hiện ✓ · Cô lập ✓ · Tiêu diệt ✓
          └── Dashboard: "8 file bị mã hóa | Tiến trình: Đã dừng"

T=5s     Admin thực hiện Recovery:
          └── Phương án 1: Decrypt bằng .ransom_key (Fernet)
          └── Phương án 2: Restore từ backup tar.gz

T=6s     Hệ thống phục hồi hoàn tất
          └── shop_data/ → file plaintext gốc ✓
          └── Giai đoạn Phục hồi ✓
          └── Xuất Báo cáo sự cố (.txt)
```

---

## Kết luận

### Điểm mạnh của hệ thống phòng thủ demo

1. **Phát hiện realtime** — HIDS polling 2s, không cần scan thủ công
2. **Ứng phó tự động** — không phụ thuộc vào thao tác quản trị viên trong thời điểm đầu
3. **Hai con đường phục hồi** — decrypt (nếu có key) hoặc restore backup (fallback)
4. **Backup proactive** — dữ liệu được lưu trữ độc lập trước khi bị tấn công
5. **Tuân theo IR Framework** — 6 giai đoạn có thể theo dõi trực quan trên dashboard

### Hạn chế (so với môi trường thực)

| Hạn chế demo | Thực tế cần bổ sung |
|--------------|---------------------|
| Key lưu local (`.ransom_key`) | RSA-2048 + key escrow server |
| Sandbox giới hạn | Giám sát toàn bộ filesystem |
| pkill đơn giản | EDR (Endpoint Detection & Response) |
| Backup local | Offline/air-gapped backup |
| Không có network monitor | NIDS + firewall rules |
| YARA rules thủ công | Threat intelligence feed tự động |

---

> **Demo ONLY** — Toàn bộ mã nguồn, file thực thi và dữ liệu trong dự án này chỉ phục vụ mục đích học thuật và trình diễn trong môi trường kiểm soát. Không sử dụng ngoài môi trường demo.
