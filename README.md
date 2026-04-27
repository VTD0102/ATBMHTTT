# ATBMHTTT — Demo Phòng Chống Ransomware cho Dữ Liệu TMĐT

Dự án demo học thuật cho môn **An Toàn Bảo Mật Hệ Thống Thông Tin**. Kịch bản mô phỏng toàn bộ vòng đời của một cuộc tấn công social engineering + ransomware và quá trình phòng thủ, phát hiện, phục hồi.

> **DEMO ONLY** — Chỉ chạy trên máy local. Không dùng trên dữ liệu thật hoặc môi trường production.

---

## Tổng quan

| Thành phần | Vai trò |
|---|---|
| `manager-agent/` | Mã độc — GUI ProManager Suite giả mạo + ransomware engine |
| `shop_data/` | Dữ liệu nạn nhân — file TMĐT mẫu dùng làm sandbox |
| `defender/` | Phần mềm bảo vệ — scanner, backup, GUI defender |
| `landing-web/` | Trang web quảng cáo giả (React + Vite) phát tán file exe |
| `backups/` | Các bản backup `.tar.gz` tạo ra trong demo |

---

## Cấu trúc dự án

```text
.
├── manager-agent/
│   ├── ProManagerSuite.exe      # File ELF PyInstaller (~14 MB) — nạn nhân tải về
│   ├── fake_manager.py          # GUI ProManager giả (activation + dashboard)
│   ├── fake_ransom.py           # Màn hình ransom note fullscreen
│   └── ransomware_simulator.py  # Engine mã hóa Fernet (sandbox-only)
│
├── shop_data/                   # Dữ liệu TMĐT mẫu (invoice, customer, contract…)
│
├── defender/
│   ├── defender_gui.py          # GUI bảo vệ — Scanner, Backup, Dashboard, Log
│   ├── scanner.py               # CLI — quét entropy + đuôi .encrypted
│   ├── decryptor.py             # CLI — giải mã .encrypted bằng .ransom_key
│   ├── backup_manager.py        # CLI — tạo/list/restore backup tar.gz
│   ├── static_analyzer.py       # Phân tích tĩnh file nghi ngờ (YARA)
│   ├── behavior_monitor.py      # Giám sát filesystem realtime
│   └── rules/ransomware.yar     # YARA rules (3 rules)
│
├── landing-web/                 # React + Vite marketing page
│   ├── public/ProManagerSuite.exe
│   └── src/components/          # Hero, Features, Pricing, Download…
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
sudo apt install python3-tk
python3 -m pip install cryptography yara-python
```

---

## Luồng tấn công mô phỏng

```
Nạn nhân truy cập landing-web (React site)
  → Tải ProManagerSuite.exe
  → Chạy exe → fake_manager.py khởi động
      → Màn hình Activation (nhập API key)
      → Màn hình "Verifying..." fullscreen
      → Dashboard ProManager giả (sidebar, project cards, task list)
      → Sau ~10s: fake_ransom.py fullscreen
          → Hiển thị yêu cầu 59,000,000 VND + countdown
          → Đồng thời: ransomware_simulator.py mã hóa file trong thư mục exe
              → File gốc → file.encrypted
              → Khóa lưu tại .ransom_key
```

---

## Chạy demo

### Tấn công

```bash
# Chạy GUI tấn công (fake ProManager)
python3 manager-agent/fake_manager.py

# Hoặc chạy thẳng file exe (mô phỏng nạn nhân)
./manager-agent/ProManagerSuite.exe

# Mã hóa shop_data thủ công
python3 manager-agent/ransomware_simulator.py

# Giải mã shop_data thủ công
python3 manager-agent/ransomware_simulator.py decrypt
```

### Phòng thủ

```bash
# Mở GUI defender (khuyến nghị)
python3 defender/defender_gui.py

# CLI — quét phát hiện ransomware
python3 defender/scanner.py shop_data/

# CLI — giải mã file .encrypted
python3 defender/decryptor.py shop_data/

# CLI — backup / restore
python3 defender/backup_manager.py
python3 defender/backup_manager.py list
python3 defender/backup_manager.py restore backups/backup_YYYYMMDD_HHMMSS.tar.gz

# Phân tích tĩnh file nghi ngờ
python3 defender/static_analyzer.py manager-agent/fake_manager.py
```

### Landing page

```bash
cd landing-web
npm install
npm run dev      # localhost:5173
npm run build    # build production
```

---

## Cơ chế phòng thủ

| Công cụ | Cách phát hiện |
|---|---|
| `defender_gui.py` | Tên file khớp pattern biết (`promanagersuite`, `ransomware`…) → CRITICAL; entropy > 7.2 bits → HIGH; string scan `.py`/`.sh` |
| `scanner.py` | Đuôi `.encrypted`, entropy > 7.5 bits, safety signature `RANSOMWARE_SIMULATOR_DEMO_SAFE` |
| `static_analyzer.py` | YARA rules, chuỗi nguy hiểm, combo `cryptography` + `os.walk` + `os.remove` |
| `behavior_monitor.py` | Theo dõi snapshot filesystem, phát hiện file `.encrypted` mới hoặc file gốc bị xóa |
| `decryptor.py` | Đọc `.ransom_key` và khôi phục file `.encrypted` |
| `backup_manager.py` | Tạo, liệt kê và restore backup `.tar.gz` |

---

## An toàn sandbox

- `RansomwareSimulator._is_inside_sandbox()` dùng `os.path.realpath()` — không thể thoát ra ngoài thư mục sandbox.
- Khi chạy dưới dạng exe: sandbox = thư mục chứa exe (không ảnh hưởng `shop_data/` hay dữ liệu hệ thống).
- Extension bỏ qua khi mã hóa: `.exe .py .sh .bat .so .dll` — exe không tự mã hóa chính nó.
- Safety marker `RANSOMWARE_SIMULATOR_DEMO_SAFE` nhúng trong source để scanner tự nhận diện.

---

## Lưu ý an toàn

- Chỉ dùng cho mục đích học tập và trình diễn phòng thủ.
- Không đưa dữ liệu thật vào `shop_data/`.
- Không sửa simulator để quét ngoài sandbox.
- Sau mỗi demo, kiểm tra lại `shop_data/` và chạy decryptor nếu cần.
