# ATBMHTTT - Demo Phòng Chống Ransomware cho Dữ Liệu TMĐT

Demo học thuật cho môn **An Toàn Bảo Mật Hệ Thống Thông Tin**. Dự án mô phỏng một kịch bản **social engineering + ransomware** nhắm vào dữ liệu thương mại điện tử, kèm bộ công cụ phát hiện, ứng phó và khôi phục dữ liệu.

> **Chỉ dùng để học tập và trình diễn.** Không chạy trên dữ liệu thật, không sửa simulator để quét ngoài sandbox.

---

## Mục Lục

1. [Tổng Quan Dự Án](#tổng-quan-dự-án)
2. [Môi Trường Cài Đặt](#môi-trường-cài-đặt)
3. [Cấu Trúc Thư Mục](#cấu-trúc-thư-mục)
4. [Kịch Bản Demo](#kịch-bản-demo)
5. [Chi Tiết Từng Thành Phần](#chi-tiết-từng-thành-phần)
6. [Hướng Dẫn Chạy Demo](#hướng-dẫn-chạy-demo)
7. [Cơ Chế Phát Hiện](#cơ-chế-phát-hiện)
8. [Lệnh Hữu Ích](#lệnh-hữu-ích)
9. [Lưu Ý An Toàn](#lưu-ý-an-toàn)

---

## Tổng Quan Dự Án

Dự án gồm **3 phía** hoạt động phối hợp trong một kịch bản tấn công và phòng thủ hoàn chỉnh:

| Thành phần | Vai trò |
|---|---|
| `manager-agent/` | **Bên tấn công** — Ứng dụng ProManager giả, engine ransomware, ransom note, C2 server |
| `shop_data/` | **Nạn nhân** — Dữ liệu TMĐT mẫu (CSV/TXT/JSON) sẽ bị mã hóa trong demo |
| `defender/` | **Bên phòng thủ** — GUI HIDS, scanner entropy, phân tích tĩnh, backup, decryptor |
| `landing-web/` | **Lừa đảo** — Trang web React giả mạo phục vụ link tải exe |
| `backups/` | Backup `.tar.gz` tự động tạo trong quá trình demo |
| `quarantine/` | Nơi cô lập file nghi ngờ |
| `md-file/` | Tài liệu báo cáo, sơ đồ luồng, ghi chú vận hành |

---

## Môi Trường Cài Đặt

### Yêu Cầu Hệ Thống

| Thành phần | Phiên bản |
|---|---|
| Python (chạy source) | 3.10+ |
| Python (build exe) | 3.12 (bắt buộc cho PyInstaller) |
| Tkinter | Có sẵn theo Python (cần cài riêng trên Linux) |
| Node.js / npm | 18+ (cho landing-web) |

### Thư Viện Python Cần Thiết

| Thư viện | Dùng cho |
|---|---|
| `cryptography` | Mã hóa/giải mã Fernet (AES-128-CBC) |
| `flask` | C2 server nhận key từ máy nạn nhân |
| `yara-python` | Static analyzer (tùy chọn, cần có YARA binary) |

### Cài Đặt Nhanh

**Arch Linux:**
```bash
sudo pacman -S tk
pip install flask cryptography yara-python --break-system-packages
```

**Ubuntu/Debian:**
```bash
sudo apt install python3-tk
pip install flask cryptography yara-python
```

**Dùng virtualenv (khuyến nghị):**
```bash
python3 -m venv venv
source venv/bin/activate
pip install flask cryptography yara-python
```

### Cài Đặt Landing Page

```bash
cd landing-web
npm install
npm run dev      # Dev server tại http://localhost:5173
npm run build    # Build production ra dist/
```

### Build Executable (Tùy Chọn)

```bash
python3.12 -m PyInstaller --onefile \
    --name ProManagerSuite.exe \
    --hidden-import fake_ransom \
    --hidden-import ransomware_simulator \
    --hidden-import cryptography.fernet \
    --distpath manager-agent \
    manager-agent/fake_manager.py

# Copy vào public/ để web phục vụ
cp manager-agent/ProManagerSuite.exe landing-web/public/
```

> Output là ELF binary ~14MB tên `ProManagerSuite.exe` — chủ ý đặt tên `.exe` để gây nhầm lẫn.

---

## Cấu Trúc Thư Mục

```text
ATBMHTTT/
├── manager-agent/
│   ├── fake_manager.py         # GUI ProManager giả + kích hoạt mã hóa
│   ├── fake_ransom.py          # Màn hình đòi tiền chuộc fullscreen
│   ├── fake_installer.py       # Installer giả dùng cho behavior monitor
│   ├── ransomware_simulator.py # Engine mã hóa Fernet (sandboxed)
│   └── c2_server.py            # Flask C2 server (port 8888)
├── defender/
│   ├── defender_gui.py         # Dashboard HIDS Tkinter
│   ├── scanner.py              # Quét entropy / extension / signature
│   ├── static_analyzer.py      # Phân tích tĩnh + YARA
│   ├── behavior_monitor.py     # Giám sát hành vi real-time (inotify)
│   ├── backup_manager.py       # Tạo / list / restore backup tar.gz
│   ├── decryptor.py            # Giải mã file .encrypted bằng .ransom_key
│   └── rules/
│       └── ransomware.yar      # 3 YARA rules phát hiện ransomware
├── shop_data/                  # Dữ liệu TMĐT mẫu (sandbox nạn nhân)
├── landing-web/                # React + Vite, phục vụ link tải exe
├── backups/                    # Backup sinh ra trong demo
├── quarantine/                 # File bị cô lập
├── md-file/                    # Tài liệu báo cáo
├── c2_victims.json             # Log nạn nhân do C2 ghi lại
└── *.flag                      # Flag trạng thái ứng phó sự cố
```

---

## Kịch Bản Demo

### Tổng Quan Kịch Bản

Dự án mô phỏng một cuộc tấn công **APT (Advanced Persistent Threat)** kiểu social engineering nhắm vào doanh nghiệp TMĐT nhỏ, theo mô hình:

```
Tấn công (Attacker)                     Nạn nhân (Victim)
─────────────────────────────────────────────────────────
Dựng trang web giả (landing-web)
    └─→ Nạn nhân lướt web, thấy quảng cáo phần mềm
         "ProManager Suite — Quản lý dự án chuyên nghiệp"
              └─→ Tải ProManagerSuite.exe về máy
                   └─→ Chạy exe, nhập API key
                        └─→ Màn hình "Verifying..."
                             ├─→ Dashboard giả (10 giây)
                             └─→ RANSOMWARE KÍCH HOẠT
                                  ├─→ Mã hóa toàn bộ dữ liệu
                                  ├─→ Gửi key về C2 server
                                  └─→ Hiện ransom note (59 triệu VND)
```

### Giai Đoạn 1: Lừa Đảo (Social Engineering)

- **Landing page** (`landing-web/`) giả mạo trang chủ phần mềm quản lý dự án
- Nạn nhân bị thu hút bởi giao diện chuyên nghiệp và tính năng hấp dẫn
- Tải về file `ProManagerSuite.exe` — thực chất là ELF binary chứa payload

### Giai Đoạn 2: Xâm Nhập (Initial Access)

- Nạn nhân tự chạy exe (không cần leo thang đặc quyền)
- `fake_manager.py` hiển thị:
  1. **Màn hình Activation** — nhập API key bất kỳ cũng qua
  2. **Màn hình Verifying** — fullscreen, trông hợp lệ
  3. **Dashboard** — giao diện PM đầy đủ, có sidebar và project cards

### Giai Đoạn 3: Thực Thi Payload (Execution)

Sau 10 giây kể từ khi Dashboard hiện:
- `ransomware_simulator.py` chạy ngầm, tạo Fernet key, mã hóa toàn bộ file trong sandbox
- File gốc đổi thành `*.demo_original`, bản mã lưu thành `*.encrypted`
- `.ransom_key` lưu tạm cục bộ, sau đó **gửi về C2 server** và xóa khỏi máy nạn nhân
- `fake_ransom.py` chiếm màn hình — hiện đồng hồ đếm ngược, yêu cầu 59,000,000 VND

### Giai Đoạn 4: Ứng Phó Sự Cố (Incident Response) — Phía Defender

Defender phát hiện và phản ứng theo quy trình:

```
Phát hiện → Cách ly → Backup → Điều tra → Khôi phục → Báo cáo
```

| Bước | Hành động |
|---|---|
| Phát hiện | Scanner phát hiện file `.encrypted`, entropy >7.5 |
| Cách ly | Quarantine file nghi ngờ, đặt `NETWORK_ISOLATED.flag` |
| Backup | Tạo snapshot toàn bộ `shop_data/` trước khi tiếp tục |
| Điều tra | Static analyzer + YARA phân tích exe, behavior monitor xem log |
| Khôi phục | Restore từ backup sạch hoặc dùng key từ C2 để decrypt |
| Báo cáo | Ghi log sự kiện ra file, export báo cáo |

---

## Chi Tiết Từng Thành Phần

### Bên Tấn Công (`manager-agent/`)

#### `fake_manager.py` — Trojan GUI

Ứng dụng giả mạo "ProManager Suite" được xây dựng bằng Tkinter với giao diện trắng/indigo chuyên nghiệp.

**Luồng giao diện:**
```
Splash screen
  → Activation screen (nhập API key)
    → Verifying screen (fullscreen, giả lập xác thực 3 giây)
      → Dashboard (sidebar trái + 6 project cards)
        → [10 giây sau] trigger fake_ransom + ransomware_simulator
```

**Điểm quan trọng:**
- Mọi API key đều được chấp nhận — không có xác thực thật
- Sau khi dashboard load, bắt đầu đếm ngầm 10 giây rồi kích hoạt payload
- Khi đóng gói thành exe, `VICTIM_SANDBOX = os.path.dirname(sys.executable)` (mã hóa thư mục chứa exe, không phải `shop_data/`)

#### `ransomware_simulator.py` — Engine Mã Hóa

Dùng `cryptography.fernet` (AES-128-CBC + HMAC-SHA256).

**Cơ chế sandbox an toàn:**
- `_is_inside_sandbox()` dùng `os.path.realpath()` đảm bảo chỉ mã hóa trong thư mục được phép
- **Bỏ qua hoàn toàn:** `.exe .py .sh .bat .spec .pyz .pkg .so .dll` — exe không tự mã hóa chính nó
- **Key file:** `.ransom_key` lưu cạnh file mã hóa; gửi về C2 rồi xóa

**Lệnh thủ công:**
```bash
python3 manager-agent/ransomware_simulator.py           # mã hóa
python3 manager-agent/ransomware_simulator.py decrypt   # giải mã
```

#### `fake_ransom.py` — Ransom Note

Màn hình fullscreen không thể tắt bằng thao thường, hiển thị:
- Cảnh báo đỏ nổi bật
- Yêu cầu 59,000,000 VND
- Đồng hồ đếm ngược
- Hướng dẫn liên hệ thanh toán

> **Unlock code demo:** `DEMO-SAFE-2024-TMDT`

#### `c2_server.py` — Command & Control Server

Flask server lắng nghe tại `http://localhost:8888`.

**Endpoint chính:**
- `POST /register` — nhận key mã hóa và thông tin máy nạn nhân
- `GET /victims` — xem danh sách nạn nhân (lưu trong `c2_victims.json`)
- `POST /send_key` — gửi key giải mã cho nạn nhân (sau khi "nhận tiền")

---

### Sandbox Nạn Nhân (`shop_data/`)

Chứa dữ liệu TMĐT mẫu mô phỏng hệ thống bán hàng thực tế:

| File | Nội dung |
|---|---|
| `customer_data.csv` | Thông tin khách hàng (tên, email, địa chỉ) |
| `invoice_2024.txt` | Hóa đơn giao dịch |
| `api_config.json` | Cấu hình API payment gateway (giả) |
| `product_catalog.csv` | Danh mục sản phẩm |
| `order_history.json` | Lịch sử đơn hàng |

**Trạng thái file:**

| Giai đoạn | Trạng thái |
|---|---|
| Trước tấn công | File gốc bình thường |
| Trong tấn công | `*.encrypted` + `*.demo_original` + (có thể) `.ransom_key` |
| Sau khôi phục | File gốc được restore, `*.encrypted` bị xóa |

---

### Bên Phòng Thủ (`defender/`)

#### `defender_gui.py` — Dashboard HIDS

GUI Tkinter tổng hợp toàn bộ công cụ phòng thủ, gồm 4 panel chính:

**Panel Dashboard:**
- Trạng thái hệ thống real-time (số file, file nghi ngờ, trạng thái backup)
- Nút nhanh: Scan ngay, Tạo backup, Cách ly mạng, Vào maintenance mode
- Live event feed (cập nhật mỗi 2 giây)

**Panel Scanner:**
- Quét toàn bộ `shop_data/` và báo cáo theo mức độ:
  - `CRITICAL`: Tên file chứa pattern nguy hiểm (`promanagersuite`, `fake_manager`, `ransomware`…)
  - `HIGH`: Executable có Shannon entropy > 7.2 bits (packed/bundled)
  - `MEDIUM`: Executable có entropy 6.5–7.2 bits
  - `INFO`: File `.py`/`.sh` chứa string `RANSOMWARE_SIMULATOR_DEMO_SAFE`, `fernet.encrypt`…
- Kết quả màu theo mức độ, có thể export log

**Panel Backup & Khôi Phục:**
- Tạo snapshot `shop_data/` dạng `.tar.gz` vào `backups/`
- Liệt kê backup theo thời gian
- Restore 1-click từ backup đã chọn
- Backup **bỏ qua** `*.encrypted`, `*.demo_original`, `.ransom_key` (tránh backup dữ liệu đã bị hỏng)

**Panel Log:**
- Xem toàn bộ sự kiện theo thời gian
- Lọc theo mức độ (INFO / WARNING / CRITICAL)
- Export báo cáo sự cố

#### `scanner.py` — CLI Scanner

```bash
python3 defender/scanner.py shop_data/
```

Phát hiện dựa trên 3 tiêu chí:
1. **Extension đáng ngờ:** `.encrypted`, `.locked`, `.crypto`…
2. **Shannon entropy cao:** >7.5 bits → nhiều khả năng là dữ liệu mã hóa/nén
3. **Signature demo:** Chuỗi đặc trưng của simulator

#### `static_analyzer.py` — Phân Tích Tĩnh

```bash
python3 defender/static_analyzer.py manager-agent/fake_manager.py
```

Thực hiện:
- Quét chuỗi nguy hiểm trong file (hardcoded key, lệnh shell nguy hiểm…)
- Phát hiện import đáng ngờ (`subprocess`, `os.system`, `cryptography`…)
- Chạy YARA rules nếu cài `yara-python`

**3 YARA rules** trong `defender/rules/ransomware.yar`:
- Rule 1: Phát hiện source code simulator (chuỗi đặc trưng)
- Rule 2: Phát hiện Fernet token header (byte magic `gAAAAA`)
- Rule 3: Phát hiện HTML ransom note (chuỗi trong `fake_ransom.py`)

#### `behavior_monitor.py` — Giám Sát Hành Vi Real-time

```bash
python3 defender/behavior_monitor.py
```

Dùng **inotify** (Linux) theo dõi filesystem:
- Chụp snapshot trước/sau khi chạy installer
- Phát cảnh báo ngay khi có file `.encrypted` xuất hiện
- Kill process ngay lập tức nếu phát hiện file gốc bị xóa đột ngột
- Ghi log chi tiết từng thao tác file (create/modify/delete/rename)

#### `backup_manager.py` — Quản Lý Backup

```bash
python3 defender/backup_manager.py               # tạo backup
python3 defender/backup_manager.py list          # liệt kê
python3 defender/backup_manager.py restore backups/backup_20240101_120000.tar.gz
```

- Backup theo format: `backups/backup_YYYYMMDD_HHMMSS.tar.gz`
- Dùng `tarfile.extractall(filter='data')` tương thích Python 3.14+

#### `decryptor.py` — Khôi Phục File

```bash
python3 defender/decryptor.py shop_data/
```

- Đọc `.ransom_key` trong thư mục đích
- Giải mã từng file `.encrypted` bằng Fernet
- Xóa file `.encrypted` sau khi giải mã thành công
- Báo cáo số file đã khôi phục

---

### Landing Page (`landing-web/`)

Trang web React + Vite mô phỏng trang marketing phần mềm giả:
- Giao diện chuyên nghiệp, có testimonials, pricing, feature list
- Nút "Download Free Trial" trỏ đến `/ProManagerSuite.exe`
- File exe được đặt tại `landing-web/public/ProManagerSuite.exe`

```bash
cd landing-web
npm run dev    # http://localhost:5173
```

---

## Hướng Dẫn Chạy Demo

### Bước 0: Reset Sandbox

Luôn chạy bước này trước mỗi lần demo:

```bash
for f in shop_data/*.demo_original; do [ -e "$f" ] && mv "$f" "${f%.demo_original}"; done
rm -f shop_data/*.encrypted shop_data/.ransom_key
rm -f MAINTENANCE.flag NETWORK_ISOLATED.flag RANSOMWARE_DETECTED.flag
```

### Bước 1: Khởi Động C2 Server (Terminal 1)

```bash
python3 manager-agent/c2_server.py
# C2 lắng nghe tại http://localhost:8888
# Ghi log nạn nhân vào c2_victims.json
```

### Bước 2: Mở Defender GUI (Terminal 2)

```bash
python3 defender/defender_gui.py
```

Trong GUI:
1. Vào panel **Backup & Khôi Phục** → tạo backup sạch trước khi tấn công
2. Giữ GUI mở để quan sát real-time khi tấn công diễn ra

### Bước 3: Chạy Ứng Dụng Giả Mạo (Terminal 3)

```bash
python3 manager-agent/fake_manager.py
```

1. Nhập bất kỳ API key nào (ví dụ: `abc123`)
2. Bấm **Activate**
3. Quan sát màn hình Verifying → Dashboard
4. Sau 10 giây: ransomware kích hoạt, Defender GUI sẽ cảnh báo

### Bước 4: Quan Sát Phản Ứng Defender

Trở lại Defender GUI và quan sát:
- Event feed báo phát hiện file `.encrypted`
- Flag `RANSOMWARE_DETECTED.flag` được tạo tự động
- Scanner tự động quét lại

### Bước 5: Khôi Phục Dữ Liệu

**Cách 1 — Restore từ backup (khuyến nghị):**
```
Defender GUI → Panel Backup & Khôi Phục → Chọn backup → Khôi Phục từ backup
```

**Cách 2 — Decrypt bằng key (nếu key còn trong sandbox):**
```bash
python3 defender/decryptor.py shop_data/
```

**Cách 3 — CLI restore:**
```bash
python3 defender/backup_manager.py list
python3 defender/backup_manager.py restore backups/backup_YYYYMMDD_HHMMSS.tar.gz
```

---

## Cơ Chế Phát Hiện

| Công cụ | Phương pháp | Độ chính xác |
|---|---|---|
| `scanner.py` | Extension đáng ngờ + Shannon entropy >7.5 + signature | Cao với file đã mã hóa |
| `static_analyzer.py` | String scan + YARA rules 3 lớp | Cao với file chưa obfuscate |
| `behavior_monitor.py` | Inotify real-time, so sánh snapshot trước/sau | Phát hiện ngay lập tức |
| `defender_gui.py` | Kết hợp tất cả + CRITICAL/HIGH/MEDIUM/INFO | Tổng hợp, dễ đọc |

**Ngưỡng entropy:**
- `>7.5 bits` → Gần như chắc chắn là dữ liệu mã hóa hoặc nén
- `7.2–7.5 bits` → Nghi ngờ cao (packed executable)
- `6.5–7.2 bits` → Nghi ngờ vừa

---

## Lệnh Hữu Ích

### Bên Tấn Công

```bash
python3 manager-agent/c2_server.py
python3 manager-agent/fake_manager.py
python3 manager-agent/fake_ransom.py
python3 manager-agent/fake_installer.py
python3 manager-agent/ransomware_simulator.py           # mã hóa thủ công
python3 manager-agent/ransomware_simulator.py decrypt   # giải mã thủ công
```

### Bên Phòng Thủ

```bash
python3 defender/defender_gui.py
python3 defender/scanner.py shop_data/
python3 defender/static_analyzer.py manager-agent/fake_manager.py
python3 defender/behavior_monitor.py
python3 defender/backup_manager.py
python3 defender/backup_manager.py list
python3 defender/backup_manager.py restore backups/<ten-backup>.tar.gz
python3 defender/decryptor.py shop_data/
```

---

## Flag Files

| File | Ý nghĩa |
|---|---|
| `RANSOMWARE_DETECTED.flag` | Defender xác nhận có tấn công ransomware |
| `MAINTENANCE.flag` | Mô phỏng đưa hệ thống vào maintenance mode |
| `NETWORK_ISOLATED.flag` | Mô phỏng cô lập mạng khỏi internet |

---

## Lưu Ý An Toàn

- **Sandbox hoàn toàn:** `fake_manager.py` chỉ mã hóa trong `shop_data/` khi chạy từ source; khi là exe thì chỉ mã hóa thư mục chứa exe
- **Skip list:** Simulator bỏ qua `.exe .py .sh .bat .spec .pyz .pkg .so .dll` — không tự phá hoại môi trường Python
- **Backup an toàn:** Backup manager bỏ qua `*.encrypted`, `*.demo_original`, `.ransom_key`
- **Unlock code:** Ransom note có thể tắt bằng code `DEMO-SAFE-2024-TMDT`
- **Reset bắt buộc:** Sau mỗi lần demo, luôn chạy lại bước reset sandbox (Bước 0) trước khi demo tiếp
- **Không deploy công khai:** Landing page và C2 server chỉ chạy localhost trong môi trường demo kiểm soát
