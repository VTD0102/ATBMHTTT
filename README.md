# ATBMHTTT - Demo Phòng Chống Ransomware cho Dữ Liệu TMĐT

Demo học thuật cho môn **An Toàn Bảo Mật Hệ Thống Thông Tin**. Dự án mô phỏng một kịch bản social engineering + ransomware trên dữ liệu thương mại điện tử, kèm bộ công cụ phát hiện, ứng phó và khôi phục dữ liệu.

> **Chỉ dùng để học tập và trình diễn.** Không chạy trên dữ liệu thật, không sửa simulator để quét ngoài sandbox.

## Tổng Quan

| Thành phần | Vai trò |
|---|---|
| `manager-agent/` | Bên tấn công: ứng dụng ProManager giả, ransom note, C2 server |
| `shop_data/` | Sandbox dữ liệu nạn nhân, gồm CSV/TXT/JSON mẫu của hệ thống TMĐT |
| `defender/` | Bên phòng thủ: GUI HIDS, scanner, static analyzer, backup, decryptor |
| `backups/` | Nơi lưu backup `.tar.gz` do demo tạo ra |
| `quarantine/` | Nơi cô lập file nghi ngờ |
| `md-file/` | Tài liệu mô tả luồng tấn công, báo cáo và ghi chú vận hành |

## Cấu Trúc Chính

```text
.
├── manager-agent/
│   ├── fake_manager.py       # GUI ProManager giả + kích hoạt mã hóa demo
│   ├── fake_ransom.py        # Màn hình ransom note fullscreen
│   ├── fake_installer.py     # Installer giả cho behavior monitor
│   └── c2_server.py          # Flask C2 server, nhận key và số file bị mã hóa
├── defender/
│   ├── defender_gui.py       # Dashboard phòng thủ bằng Tkinter
│   ├── scanner.py            # Quét extension/entropy/signature
│   ├── static_analyzer.py    # Phân tích tĩnh, hỗ trợ YARA nếu có
│   ├── behavior_monitor.py   # Theo dõi hành vi khi chạy installer
│   ├── backup_manager.py     # Tạo/list/restore backup
│   ├── decryptor.py          # Khôi phục file .encrypted
│   └── rules/ransomware.yar  # YARA rules cho demo
├── shop_data/                # Dữ liệu TMĐT mẫu
├── backups/                  # Backup sinh ra trong quá trình demo
├── c2_victims.json           # Dữ liệu nạn nhân do C2 ghi lại
└── *.flag                    # Flag trạng thái ứng phó sự cố
```

## Yêu Cầu

- Python 3.10+
- `tkinter`
- `flask` cho C2 server
- `cryptography` cho decryptor/defender GUI
- `yara-python` tùy chọn cho static analyzer

Ví dụ cài trên Arch Linux:

```bash
sudo pacman -S tk
pip install flask cryptography yara-python --break-system-packages
```

Nếu dùng virtualenv:

```bash
python3 -m venv venv
source venv/bin/activate
pip install flask cryptography yara-python
```

## Luồng Demo

1. C2 server chạy tại `http://localhost:8888`.
2. Defender GUI được mở trước để giám sát `shop_data/`.
3. Người dùng chạy `manager-agent/fake_manager.py` và nhập API key bất kỳ.
4. ProManager giả hiện màn hình activation, verifying và dashboard.
5. Bên trong, demo tạo `.ransom_key`, tạo file `*.encrypted`, đổi file gốc thành `*.demo_original`, rồi gửi key về C2.
6. Nếu C2 nhận thành công, `.ransom_key` cục bộ bị xóa.
7. Defender phát hiện file `.encrypted`, tạo `RANSOMWARE_DETECTED.flag`, cô lập/backup/khôi phục theo workflow trong GUI.

## Chạy Demo

### 1. Đưa sandbox về trạng thái sạch

```bash
for f in shop_data/*.demo_original; do [ -e "$f" ] && mv "$f" "${f%.demo_original}"; done
rm -f shop_data/*.encrypted shop_data/.ransom_key
rm -f MAINTENANCE.flag NETWORK_ISOLATED.flag RANSOMWARE_DETECTED.flag
```

### 2. Chạy C2 server

```bash
python3 manager-agent/c2_server.py
```

C2 sẽ ghi thông tin nạn nhân vào `c2_victims.json`.

### 3. Mở Defender GUI

```bash
python3 defender/defender_gui.py
```

Trong GUI, nên tạo backup sạch trước khi tấn công bằng panel **Backup & Khôi phục**.

### 4. Chạy ứng dụng giả mạo

```bash
python3 manager-agent/fake_manager.py
```

Nhập API key bất kỳ, bấm activate và quan sát Defender GUI.

Có thể kích hoạt riêng bước mã hóa bằng Python:

```bash
python3 -c "import sys; sys.path.insert(0, 'manager-agent'); from fake_manager import trigger_encryption; trigger_encryption('shop_data')"
```

### 5. Khôi phục dữ liệu

Dùng GUI:

- **Backup & Khôi phục** -> chọn backup -> **Khôi phục từ backup**
- Hoặc dùng mục giải mã nếu key vẫn còn trong sandbox

Dùng CLI:

```bash
python3 defender/backup_manager.py list
python3 defender/backup_manager.py restore backups/backup_YYYYMMDD_HHMMSS.tar.gz
python3 defender/decryptor.py shop_data
```

## Lệnh Hữu Ích

### Bên tấn công

```bash
python3 manager-agent/c2_server.py
python3 manager-agent/fake_manager.py
python3 manager-agent/fake_ransom.py
python3 manager-agent/fake_installer.py
```

### Bên phòng thủ

```bash
python3 defender/defender_gui.py
python3 defender/scanner.py shop_data
python3 defender/static_analyzer.py manager-agent/fake_manager.py
python3 defender/behavior_monitor.py manager-agent/fake_installer.py shop_data
python3 defender/backup_manager.py
python3 defender/backup_manager.py list
python3 defender/backup_manager.py restore backups/<ten-backup>.tar.gz
python3 defender/decryptor.py shop_data
```

## Trạng Thái File Trong `shop_data/`

| Trạng thái | File |
|---|---|
| Trước tấn công | File gốc như `customer_data.csv`, `invoice_2024.txt`, `api_config.json` |
| Sau mã hóa | `*.encrypted` + `*.demo_original`; có thể có hoặc không có `.ransom_key` tùy C2 có nhận được key không |
| Sau restore/decrypt | File gốc được khôi phục, file `.encrypted` bị xóa |

## Cơ Chế Phát Hiện

| Công cụ | Nội dung |
|---|---|
| `scanner.py` | Phát hiện extension đáng ngờ, entropy cao, signature demo |
| `static_analyzer.py` | Quét chuỗi nguy hiểm và YARA rules nếu cài `yara-python` |
| `behavior_monitor.py` | Chụp snapshot trước/sau khi chạy installer, kill process nếu xuất hiện `.encrypted` hoặc file gốc bị xóa |
| `defender_gui.py` | Dashboard HIDS, live feed, backup tự động, quarantine, workflow ứng phó sự cố |

## Flag Files

| File | Ý nghĩa |
|---|---|
| `RANSOMWARE_DETECTED.flag` | Defender xác nhận có tấn công ransomware |
| `MAINTENANCE.flag` | Mô phỏng đưa hệ thống vào maintenance mode |
| `NETWORK_ISOLATED.flag` | Mô phỏng cô lập mạng |

## Lưu Ý An Toàn

- `fake_manager.py` chỉ thao tác trong sandbox `shop_data/` khi chạy từ source.
- Khi chạy dạng executable đóng gói, sandbox là thư mục chứa executable.
- Simulator bỏ qua các extension như `.exe`, `.py`, `.ps1`, `.sh`, `.bat`, `.so`, `.dll`.
- Backup bỏ qua `*.encrypted`, `*.demo_original`, `.ransom_key` để tránh lưu dữ liệu đã bị mã hóa.
- Sau mỗi lần demo, chạy lại bước reset sandbox trước khi demo tiếp.
