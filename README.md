# ATBMHTTT — Demo Phòng Chống Ransomware cho Dữ Liệu TMĐT

Dự án demo học thuật cho môn **An Toàn Bảo Mật Hệ Thống Thông Tin**. Kịch bản mô phỏng toàn bộ vòng đời của một cuộc tấn công social engineering + ransomware và quá trình phòng thủ, phát hiện, ứng phó.

> **DEMO ONLY** — Chỉ chạy trên máy local. Không dùng trên dữ liệu thật hoặc môi trường production.

---

## Tổng quan

| Thành phần | Vai trò |
|---|---|
| `manager-agent/` | Mã độc — GUI ProManager Suite giả mạo + ransomware engine + C2 server |
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
│   ├── fake_installer.py        # Installer giả (tùy chọn)
│   └── c2_server.py             # C&C server (Flask) — nhận key từ nạn nhân
│
├── shop_data/                   # Dữ liệu TMĐT mẫu — xem bảng trạng thái bên dưới
│
├── defender/
│   ├── defender_gui.py          # GUI HIDS — Dashboard, Phát hiện, Cô lập, Backup
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
├── backups/                     # Backup sinh ra khi demo
├── MAINTENANCE.flag             # Tạo tự động khi bật Maintenance Mode
├── NETWORK_ISOLATED.flag        # Tạo khi mô phỏng ngắt mạng
└── RANSOMWARE_DETECTED.flag     # Tạo khi HIDS xác nhận tấn công ransomware
```

---

## Trạng thái `shop_data/` qua các giai đoạn

| Giai đoạn | Nội dung `shop_data/` |
|---|---|
| **Trước tấn công** (sạch) | `file.txt` — chỉ file dữ liệu gốc |
| **Trong/sau khi bị mã hóa** | `file.txt.encrypted` + `file.txt.demo_original` |
| **Sau reset** (`mv`) | `file.txt` — chỉ file dữ liệu gốc |

> `.demo_original` **không** phải file có sẵn — chúng được TẠO RA bởi quá trình mã hóa (file gốc bị đổi tên sang `.demo_original` để lưu tạm). Sau khi reset bằng `mv`, chỉ còn file gốc, không trùng lặp.

---

## Yêu cầu

- Python 3.10+ với `tkinter`
- `cryptography` (bắt buộc)
- `flask` (bắt buộc — cho C2 server)
- `yara-python` (tùy chọn — dùng trong `static_analyzer.py`)
- Node.js 18+ (chỉ cho landing page)

```bash
# Arch Linux
sudo pacman -S tk
pip install cryptography flask yara-python --break-system-packages
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
          → Ngầm: với mỗi file trong sandbox:
              file.txt  →  đổi tên  →  file.txt.demo_original  (bản gốc được giữ lại)
                        →  tạo mới  →  file.txt.encrypted       (bản mã hóa)
          → Ngầm: key được gửi đến C2 server (localhost:8888)
          → Key cục bộ bị XÓA sau khi C2 xác nhận nhận
      → Sau ~10s: fake_ransom.py fullscreen
          → Yêu cầu 59.000.000 VND + countdown timer
```

---

## Chạy demo — Hướng dẫn từng bước

### Bước 0 — Đảm bảo dữ liệu sạch

```bash
# Nếu shop_data còn .demo_original từ lần demo trước → khôi phục bằng mv
for f in shop_data/*.demo_original; do mv "$f" "${f%.demo_original}"; done
# Dọn sạch file mã hóa và các flag
rm -f shop_data/*.encrypted shop_data/.ransom_key
rm -f MAINTENANCE.flag NETWORK_ISOLATED.flag RANSOMWARE_DETECTED.flag
```

> `mv` (không phải `cp`) — tiêu thụ file `.demo_original`, chỉ giữ lại file gốc, tránh trùng lặp.

---

### Bước 1 — Khởi động C2 Server (terminal 1)

```bash
python3 manager-agent/c2_server.py
```

```
[C&C] Server started on http://localhost:8888
[C&C] Waiting for victims...
```

---

### Bước 2 — Mở Defender GUI (terminal 2, mở TRƯỚC khi chạy attack)

```bash
python3 defender/defender_gui.py
```

Dashboard hiện:
- **Live Attack Feed** (terminal đen) — sự kiện theo thời gian thực
- **Quá trình phòng thủ** — 7 bước NIST IR tick dần
- Dot xanh = đang giám sát / Dot đỏ = đang bị tấn công

---

### Bước 3 — Backup TRƯỚC khi tấn công

Mở panel **"Backup & Khôi phục"** → nhấn **"💾 Backup ngay"**.

Backup tự động bỏ qua `*.encrypted`, `*.demo_original`, `.ransom_key` — chỉ lưu file dữ liệu sạch.

---

### Bước 4 — Chạy Attack (terminal 3)

**Cách A — Đầy đủ (khuyến nghị):**
```bash
python3 manager-agent/fake_manager.py
# Nhập API key bất kỳ → Activate → Dashboard xuất hiện → mã hóa sau ~10s
```

**Cách B — Chỉ mã hóa:**
```bash
python3 -c "
import sys; sys.path.insert(0, 'manager-agent')
from fake_manager import trigger_encryption
trigger_encryption('shop_data')
"
```

---

### Bước 5 — Quan sát Live Feed

| Thời điểm | Sự kiện |
|---|---|
| ~10s | `⚠ ENCRYPT: customer_data.csv → ...encrypted` |
| ~10s | `🔴 HIDS PHÁT HIỆN TẤN CÔNG RANSOMWARE!` |
| ~13s | `🔍 [Bước 1/4]` Xác nhận + ghi `RANSOMWARE_DETECTED.flag` |
| ~23s | `🔒 [Bước 2/4]` Kill process + bật Maintenance Mode |
| ~33s | `💾 [Bước 3/4]` Backup khẩn cấp (chỉ file sạch) |
| ~43s | `📋 [Bước 4/4]` Đánh giá thiệt hại + popup |
| ~53s | `♻ [Bước 5/5]` Tự động tìm backup sạch và khôi phục |

> Điều chỉnh tốc độ: `STEP_DELAY = 10000` (ms) trong `_auto_respond()` của `defender_gui.py`.

---

### Bước 6 — Khôi phục dữ liệu

**Phương án 1 — Restore từ backup** (trong Defender GUI):
- Panel "Backup & Khôi phục" → chọn backup → **"Khôi phục từ backup"**
- Sau restore: `*.encrypted` bị xóa sạch (kể cả file `.encrypted` trong backup cũ), chỉ còn file gốc
- `RANSOMWARE_DETECTED.flag` và `_under_attack` tự reset

**Phương án 2 — Giải mã bằng key** (mô phỏng trả tiền chuộc):
- Panel "Backup & Khôi phục" → mục "Giải mã bằng key kẻ tấn công" (nền vàng)

**CLI:**
```bash
python3 defender/backup_manager.py restore backups/backup_YYYYMMDD_HHMMSS.tar.gz
python3 defender/decryptor.py shop_data/   # nếu .ransom_key còn local
```

---

### Bước 7 — Reset sau demo

```bash
for f in shop_data/*.demo_original; do mv "$f" "${f%.demo_original}"; done
rm -f shop_data/*.encrypted shop_data/.ransom_key
rm -f MAINTENANCE.flag NETWORK_ISOLATED.flag RANSOMWARE_DETECTED.flag
```

---

## Defender GUI — Tính năng

### Dashboard

- **Stat cards**: file bị mã hóa · tổng file · tiến trình độc hại · trạng thái hệ thống
- Trạng thái hệ thống: `Đang bảo vệ ✓` / `⚠ ĐANG BỊ TẤN CÔNG` / `🔴 RANSOMWARE ĐÃ XÂM NHẬP`
- **Live Attack Feed**: terminal đen realtime
- **7 bước NIST IR**: Chuẩn bị → Phát hiện → Cô lập → Backup → Đánh giá → Khôi phục → Rút kinh nghiệm

### Phát hiện — HIDS

4 chỉ số thời gian thực:

| Indicator | Nội dung |
|---|---|
| File `.encrypted` | Số file đã bị mã hóa |
| Tiến trình độc hại | Tên process đang chạy |
| Ransom key | Có/không `.ransom_key` trong `shop_data/` |
| **Ransomware flag** | `🔴 ĐÃ XÁC NHẬN` khi `RANSOMWARE_DETECTED.flag` tồn tại |

Quét thủ công: signature-based, entropy anomaly (>7.2 bits), extension scan, process monitor.

### Cô lập & Tiêu diệt

- `pkill` tiến trình độc hại
- Bật Maintenance Mode (`MAINTENANCE.flag`)
- Quarantine exe
- Mô phỏng ngắt mạng (`NETWORK_ISOLATED.flag`)

### Backup & Khôi phục

- Backup định kỳ tự động (1h/3h/6h/12h/24h), giữ tối đa N bản
- **Backup bỏ qua**: `*.encrypted`, `*.demo_original`, `.ransom_key`
- **Restore 3-pass**: xóa infected trước extract → xóa infected trong subdir → xóa infected sau extract
- `RANSOMWARE_DETECTED.flag` và `_under_attack` tự reset sau restore thành công

---

## Flag files

| File | Tạo bởi | Ý nghĩa | Xóa khi |
|---|---|---|---|
| `MAINTENANCE.flag` | HIDS auto-respond bước 2 | Ngừng giao dịch, bảo trì | Thủ công |
| `NETWORK_ISOLATED.flag` | Thủ công (Cô lập) | Mô phỏng ngắt mạng | Thủ công |
| `RANSOMWARE_DETECTED.flag` | HIDS auto-respond bước 1 | Xác nhận tấn công (JSON) | Tự động sau restore |

**Nội dung `RANSOMWARE_DETECTED.flag`:**
```json
{
  "detected_at": "2026-05-10T15:18:57",
  "files_encrypted": 8,
  "attack_type": "ransomware",
  "status": "active"
}
```

---

## Cơ chế phát hiện HIDS

| Phương pháp | Mô tả |
|---|---|
| **Signature-based** | Tên file/string khớp pattern (`promanagersuite`, `ransomware`…) → CRITICAL |
| **Extension scan** | Hàng loạt file đổi đuôi → `.encrypted` trong thời gian ngắn |
| **Anomaly (entropy)** | Entropy > 7.2 bits → file bị đóng gói/mã hóa → HIGH |
| **Behavior-based** | File bị đọc rồi xóa liên tục (Disk I/O spike) |
| **Process monitor** | Tiến trình lạ đang chạy (pgrep pattern matching) |
| **YARA rules** | 3 rules trong `rules/ransomware.yar` |

---

## C2 Server

`manager-agent/c2_server.py` — Flask, lắng nghe `http://localhost:8888`:

- Nhận POST `/register`: `{ victim_id, hostname, key, files }`
- Lưu vào `c2_victims.json`
- Khi C2 xác nhận → `fake_manager.py` xóa `.ransom_key` cục bộ → nạn nhân mất khả năng tự giải mã

---

## An toàn sandbox

- `os.path.realpath()` — ransomware engine không thể thoát ra ngoài sandbox
- Khi chạy dưới dạng exe: sandbox = thư mục chứa exe (không ảnh hưởng `shop_data/`)
- Extension bỏ qua: `.exe .py .sh .bat .so .dll` — exe không tự mã hóa chính nó
- Safety marker `RANSOMWARE_SIMULATOR_DEMO_SAFE` nhúng trong source để scanner nhận diện

---

## Landing page

```bash
cd landing-web && npm install
npm run dev      # localhost:5173
npm run build    # → dist/
```

---

## Lưu ý an toàn

- Chỉ dùng cho mục đích học tập và trình diễn.
- Không đưa dữ liệu thật vào `shop_data/`.
- Không sửa simulator để quét ngoài sandbox.
- Sau mỗi demo, chạy script reset ở **Bước 7**.
