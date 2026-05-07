# ATBMHTTT — Demo Phòng Chống Ransomware cho Dữ Liệu TMĐT

Dự án demo học thuật cho môn **An Toàn Bảo Mật Hệ Thống Thông Tin**. Kịch bản mô phỏng toàn bộ vòng đời của một cuộc tấn công social engineering + ransomware và quá trình phòng thủ, phát hiện, ứng phó.

> **DEMO ONLY** — Chỉ chạy trên máy local. Không dùng trên dữ liệu thật hoặc môi trường production.

---

## Tổng quan

| Thành phần | Vai trò |
|---|---|
| `manager-agent/` | Mã độc — GUI ProManager Suite giả mạo + ransomware engine |
| `shop_data/` | Dữ liệu nạn nhân — file TMĐT mẫu dùng làm sandbox |
| `defender/` | Phần mềm bảo vệ — HIDS scanner, backup định kỳ, GUI defender |
| `landing-web/` | Trang web quảng cáo giả (React + Vite) phát tán file exe |
| `backups/` | Các bản backup `.tar.gz` tạo ra trong demo |

---

## Cấu trúc dự án

```text
.
├── manager-agent/
│   ├── ProManagerSuite.exe      # File ELF PyInstaller (~14 MB) — nạn nhân tải về
│   ├── fake_manager.py          # GUI ProManager giả (activation → dashboard → ransom)
│   ├── fake_ransom.py           # Màn hình ransom note fullscreen + countdown
│   └── ransomware_simulator.py  # Engine mã hóa Fernet — 5s/file (sandbox-only)
│
├── shop_data/                   # Dữ liệu TMĐT mẫu (invoice, customer, contract…)
│
├── defender/
│   ├── defender_gui.py          # GUI HIDS — Live Feed, Phát hiện, Cô lập, Backup
│   ├── scanner.py               # CLI — quét entropy + đuôi .encrypted
│   ├── decryptor.py             # CLI — giải mã .encrypted bằng .ransom_key
│   ├── backup_manager.py        # CLI — tạo/list/restore backup tar.gz
│   ├── static_analyzer.py       # Phân tích tĩnh file nghi ngờ (YARA)
│   ├── behavior_monitor.py      # Giám sát filesystem realtime
│   └── rules/ransomware.yar     # YARA rules (3 rules)
│
├── landing-web/                 # React + Vite marketing page
│   ├── public/ProManagerSuite.exe
│   └── src/components/
│
└── backups/                     # Backup sinh ra khi demo
```

---

## Yêu cầu

- Python 3.10+ với `tkinter`
- `cryptography` (bắt buộc)
- `yara-python` (tùy chọn — dùng trong `static_analyzer.py`)
- Node.js 18+ (chỉ cho landing page)

```bash
# Arch Linux
sudo pacman -S tk
python3 -m pip install cryptography yara-python
```

---

## Luồng tấn công mô phỏng

```
Nạn nhân truy cập landing-web (React site)
  → Tải ProManagerSuite.exe
  → Chạy exe → fake_manager.py khởi động
      → Màn hình Activation (nhập API key bất kỳ)
      → Màn hình "Verifying..." fullscreen (~2.4s)
      → Dashboard ProManager giả (sidebar, project cards, task list)
          → Ngầm: ransomware_simulator.py bắt đầu mã hóa (5s/file)
      → Sau ~10s: fake_ransom.py fullscreen
          → Yêu cầu 59.000.000 VND + countdown
          → File gốc → file.encrypted (tiếp tục cho đến hết)
          → Khóa mã hóa lưu tại shop_data/.ransom_key
```

---

## Chạy demo — Hướng dẫn từng bước

### Bước 0 — Đảm bảo dữ liệu sạch

```bash
# Kiểm tra shop_data không có file .encrypted
ls shop_data/

# Nếu có file .encrypted từ lần demo trước, restore lại:
python3 manager-agent/ransomware_simulator.py decrypt
```

---

### Bước 1 — Mở Defender GUI (mở TRƯỚC khi chạy attack)

```bash
python3 defender/defender_gui.py
```

GUI sẽ hiện **Dashboard — Live Monitor** với:
- **Live Attack Feed** (terminal đen bên trái) — hiển thị sự kiện theo thời gian thực
- **Quá trình Phòng thủ** (bên phải) — 5 bước tick dần khi hoàn thành
- Dot nhấp nháy xanh = đang giám sát, đỏ = đang bị tấn công

> Khuyến nghị demo: để màn hình Defender và màn hình Attack chạy song song (split screen hoặc 2 màn hình).

---

### Bước 2 — Chạy Attack (trên màn hình/terminal khác)

**Cách A — Đầy đủ (khuyến nghị cho demo):**
```bash
python3 manager-agent/fake_manager.py
# Nhập API key bất kỳ → Activate License
# Dashboard xuất hiện → tự động trigger mã hóa sau ~10s
```

**Cách B — Chỉ mã hóa (không có GUI giả):**
```bash
python3 manager-agent/ransomware_simulator.py
```

**Tốc độ:** mỗi file bị mã hóa cách nhau **10 giây** → 8 file × 10s = ~80 giây nếu không bị chặn.

---

### Bước 3 — Quan sát Live Feed trên Defender GUI

Khi file đầu tiên bị mã hóa, HIDS tự động phát hiện và thực hiện 4 bước ứng phó:

| Thời điểm | Sự kiện hiển thị trên Live Feed |
|---|---|
| ~10s | File đầu tiên bị mã hóa: `⚠ ENCRYPT: customer_data.csv → ...encrypted` |
| ~10s | `🔴 HIDS PHÁT HIỆN TẤN CÔNG RANSOMWARE!` — banner đỏ xuất hiện |
| ~13s | `🔍 [Bước 1/4]` Xác nhận tấn công, mô tả phương pháp phát hiện (10s) |
| ~20s | File thứ hai bị mã hóa trong lúc bước 1 đang chạy |
| ~23s | `🔒 [Bước 2/4]` Kill process + bật Maintenance Mode (10s) |
| ~33s | `💾 [Bước 3/4]` Backup khẩn cấp dữ liệu còn lại (10s) |
| ~43s | `📋 [Bước 4/4]` Đánh giá thiệt hại + popup tổng kết (10s) |
| ~53s | Popup hiện — demo kết thúc, chuyển sang giải thích khôi phục |

> **Tổng thời gian demo tự động: ~55 giây (~1 phút)**

> **Điều chỉnh tốc độ:** Sửa `STEP_DELAY = 10000` (ms) và `encrypt_delay = 10.0` (giây) nếu muốn nhanh/chậm hơn.

---

### Bước 4 — Khôi phục dữ liệu

Mở panel **"Backup & Khôi phục"** trên Defender GUI:

**Phương án 1 — Restore từ backup (thực tế):**
- Chọn backup trong danh sách → nhấn **"Khôi phục từ backup"**
- Backup khẩn cấp (`backup_emergency_*.tar.gz`) được tạo tự động khi HIDS phát hiện

**Phương án 2 — Giải mã bằng key (mô phỏng trả tiền chuộc):**
- Mục "Giải mã bằng key kẻ tấn công" ở cuối panel (nền vàng)
- Nhấn **"Demo Key?"** để xem key hiện tại
- Nhập key → nhấn **"Giải mã với key này"**

**CLI (ngoài GUI):**
```bash
# Restore từ backup
python3 defender/backup_manager.py restore backups/backup_emergency_YYYYMMDD_HHMMSS.tar.gz

# Giải mã trực tiếp bằng .ransom_key (CLI)
python3 defender/decryptor.py shop_data/

# Hoặc dùng simulator (nhanh nhất để reset sau demo)
python3 manager-agent/ransomware_simulator.py decrypt
```

---

### Bước 5 — Reset sau demo

```bash
# Giải mã toàn bộ file .encrypted
python3 manager-agent/ransomware_simulator.py decrypt

# Dọn flag maintenance / network isolation
rm -f MAINTENANCE.flag NETWORK_ISOLATED.flag

# Kiểm tra lại
ls shop_data/
```

---

## Các tính năng của Defender GUI

### Dashboard — Live Monitor

- **Live Attack Feed**: terminal đen hiển thị từng file bị mã hóa, từng bước ứng phó theo thời gian thực
- **Quá trình phòng thủ**: 5 bước tick dần (Chuẩn bị → Phát hiện → Cô lập → Backup → Đánh giá)
- **Tóm tắt thiệt hại**: số file bị mã hóa, trạng thái backup khẩn cấp

### Phát hiện — HIDS

- Chỉ số thời gian thực: file `.encrypted`, tiến trình độc hại, ransom key
- Quét thủ công: signature-based + entropy anomaly (>7.2 bits = HIGH)
- Extension scan, process monitoring

### Cô lập & Tiêu diệt

- Dừng tiến trình (`pkill`)
- Bật Maintenance Mode
- Quarantine exe
- Mô phỏng ngắt mạng (tạo `NETWORK_ISOLATED.flag`)

### Backup & Khôi phục

- Backup định kỳ tự động (1h/3h/6h/12h/24h)
- Lịch sử backup + restore
- Mục "Giải mã bằng key" (demo — mô phỏng sau khi trả tiền chuộc)

> **Triết lý phòng thủ:** Defender chỉ giảm thiểu thiệt hại, không tự giải mã được. Backup định kỳ là biện pháp phòng thủ hiệu quả nhất.

---

## Cơ chế phát hiện HIDS

| Phương pháp | Mô tả |
|---|---|
| **Signature-based** | Tên file/string khớp pattern ransomware đã biết (`promanagersuite`, `ransomware`…) → CRITICAL |
| **Extension scan** | Hàng loạt file đổi đuôi → `.encrypted` trong thời gian ngắn |
| **Anomaly (entropy)** | Entropy > 7.2 bits → file bị đóng gói/mã hóa → HIGH |
| **Behavior-based** | File bị đọc rồi xóa liên tục (Disk I/O spike) |
| **Process monitor** | Tiến trình lạ đang chạy (pgrep pattern matching) |
| **YARA rules** | 3 rules trong `rules/ransomware.yar` — phân tích tĩnh |

---

## Tốc độ mô phỏng

| Thành phần | Giá trị mặc định | Cách thay đổi |
|---|---|---|
| Delay giữa mỗi file mã hóa | **10 giây** | `encrypt_delay=` trong `RansomwareSimulator.__init__()` |
| Pause trước khi bước 1 bắt đầu | **3 giây** | `self.root.after(3000, step1)` trong `_auto_respond()` |
| Delay giữa các bước phòng thủ | **10 giây** | `STEP_DELAY = 10000` trong `_auto_respond()` của `defender_gui.py` |

---

## An toàn sandbox

- `RansomwareSimulator._is_inside_sandbox()` dùng `os.path.realpath()` — không thể thoát ra ngoài thư mục sandbox.
- Khi chạy dưới dạng exe: sandbox = thư mục chứa exe (không ảnh hưởng `shop_data/` hay dữ liệu hệ thống).
- Extension bỏ qua khi mã hóa: `.exe .py .sh .bat .so .dll` — exe không tự mã hóa chính nó.
- Safety marker `RANSOMWARE_SIMULATOR_DEMO_SAFE` nhúng trong source để scanner tự nhận diện.

---

## Landing page

```bash
cd landing-web
npm install
npm run dev      # dev server tại localhost:5173
npm run build    # build production → dist/
```

File exe download: `/ProManagerSuite.exe` — phục vụ từ `landing-web/public/ProManagerSuite.exe`.

---

## Lưu ý an toàn

- Chỉ dùng cho mục đích học tập và trình diễn phòng thủ.
- Không đưa dữ liệu thật vào `shop_data/`.
- Không sửa simulator để quét ngoài sandbox.
- Sau mỗi demo, chạy `python3 manager-agent/ransomware_simulator.py decrypt` để reset.
