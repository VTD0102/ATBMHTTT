# Social Engineering Ransomware Demo — Design Spec

**Date:** 2026-04-27  
**Project:** ATBMHTTT — Academic Security Demo  
**Scope:** Mở rộng `ransomware-demo/` với module `social-engineering/` mô phỏng tấn công giả mạo API key miễn phí

---

## Mục Tiêu

Minh họa kịch bản tấn công ransomware qua social engineering: nạn nhân bị lừa tải "phần mềm kích hoạt GPT API key miễn phí", thực chất là ransomware. Demo chạy trên **1 máy duy nhất** với 2 kịch bản chuyển đổi bằng flag:

- `--attack-only`: nạn nhân không có phòng thủ → bị mã hóa toàn bộ
- `--with-defender`: hệ thống phòng thủ phát hiện và chặn trước khi thiệt hại xảy ra

---

## Cấu Trúc Thư Mục

```
social-engineering/
├── attacker/
│   ├── fake_landing.html        # Landing page "Nhận GPT API key miễn phí"
│   ├── fake_key_generator.html  # UI sinh key giả + progress bar cài đặt
│   ├── fake_installer.py        # Installer giả — payload ransomware ngầm
│   └── victim_sandbox/          # Files "của nạn nhân"
│       ├── project_data.txt
│       ├── api_config.json
│       └── business_report.csv
├── defender/
│   ├── static_analyzer.py       # Phân tích tĩnh trước khi chạy
│   └── behavior_monitor.py      # Theo dõi filesystem trong khi chạy
├── prevention_success.html      # UI "Defender đã chặn thành công"
├── demo_social.sh               # Demo script chính
└── tests/
    ├── test_static_analyzer.py
    └── test_behavior_monitor.py
```

**Tái sử dụng từ `ransomware-demo/defender/`:**
- `scanner.py` — entropy + extension + signature detection
- `rules/ransomware.yar` — YARA rules (RansomwareSimulator_Demo, EncryptedFilePattern)
- `backup_manager.py` — backup/restore victim_sandbox

---

## Luồng Attacker

### fake_landing.html
Mô phỏng landing page hợp lệ:
- Logo "OpenAI API", headline "Get Your Free GPT-4 API Key"
- Form nhập email → submit redirect sang `fake_key_generator.html`
- Badge góc dưới: `⚠️ DEMO ONLY — Academic Environment`

### fake_key_generator.html
UI theatrical:
- Progress bar "Generating your key..." (3 giây CSS animation)
- Hiển thị API key giả: `sk-demo-XXXX-XXXX-XXXX-XXXXXXXXXXXX`
- Nút "Download SDK to activate key" + hướng dẫn: `python fake_installer.py`
- Badge: `⚠️ DEMO ONLY — Academic Environment`

### fake_installer.py
Khi chạy thực hiện song song:
1. In terminal: `Installing OpenAI Python SDK... [████████] 100%` (fake progress, time.sleep)
2. In terminal: `Activating API key sk-demo-XXXX... Done!`
3. **Ngầm:** import và gọi `RansomwareSimulator(sandbox_dir="victim_sandbox/")` → mã hóa toàn bộ files  
   Import path: `sys.path.insert` trỏ tới `../ransomware-demo/` để dùng `attacker.ransomware_simulator`

Key lưu vào `victim_sandbox/.ransom_key`. Sau đó mở `../ransomware-demo/attacker/ransom_note.html` (tái dụng file hiện có, không copy).

**Safety invariant:** Tái dụng `_is_inside_sandbox()` — chỉ mã hóa trong `victim_sandbox/`.

---

## Luồng Defender

### static_analyzer.py
Nhận path tới file installer, thực hiện 3 kiểm tra theo thứ tự:

| Kiểm tra | Phương pháp | Severity |
|----------|-------------|---------|
| YARA scan | Tái dụng `rules/ransomware.yar` | CRITICAL |
| Dangerous string scan | Tìm `RANSOMWARE_SIMULATOR_DEMO_SAFE`, `Fernet`, `.encrypt(` | CRITICAL |
| Suspicious import combo | `cryptography` + `os.walk` + `os.remove` cùng nhau | MEDIUM |

Nếu phát hiện CRITICAL → in cảnh báo đỏ, trả về `False` (không cho chạy).  
Output: structured list giống `scanner.py` hiện có (`file`, `reason`, `severity`, `detail`).

### behavior_monitor.py
Dùng **filesystem snapshot polling** (không cần dependency ngoài):

1. `snapshot_before = take_snapshot(victim_sandbox/)` — ghi lại tên + size tất cả files
2. Chạy `fake_installer.py` trong `subprocess.Popen`
3. Poll mỗi 0.5s: so sánh snapshot hiện tại với `snapshot_before`
4. Nếu phát hiện file `.encrypted` mới hoặc file gốc bị xóa → kill subprocess, báo cáo, mở `prevention_success.html`

### prevention_success.html
UI màu xanh lá:
- Headline: "Threat Blocked Successfully"
- Liệt kê các dấu hiệu bị phát hiện (dynamic từ behavior_monitor output)
- Nút "Restore Files" → hướng dẫn chạy backup restore
- Badge: `⚠️ DEMO ONLY — Academic Environment`

---

## Demo Script (`demo_social.sh`)

### `--attack-only` (7 bước)

| Bước | Hành động |
|------|-----------|
| 1 | Backup `victim_sandbox/` |
| 2 | Mở `fake_landing.html` trong browser |
| 3 | Mở `fake_key_generator.html` |
| 4 | Chạy `fake_installer.py` |
| 5 | Hiển thị `victim_sandbox/` sau tấn công (toàn .encrypted) |
| 6 | Mở `../ransomware-demo/attacker/ransom_note.html` |
| 7 | Reset `victim_sandbox/` từ backup |

### `--with-defender` (10 bước)

| Bước | Hành động |
|------|-----------|
| 1 | Backup `victim_sandbox/` |
| 2 | Mở `fake_landing.html` |
| 3 | Mở `fake_key_generator.html` |
| 4 | **Static analyzer quét `fake_installer.py`** |
| 5 | **Cảnh báo CRITICAL — hỏi có bỏ qua không** |
| 6 | *(Nếu bỏ qua để demo behavioral)* Bật behavior monitor |
| 7 | Chạy `fake_installer.py` (monitored) |
| 8 | **Behavior monitor phát hiện .encrypted → kill process** |
| 9 | Mở `prevention_success.html` |
| 10 | Reset `victim_sandbox/` từ backup |

---

## Testing

### test_static_analyzer.py (3 tests)
- `test_detect_fernet_import` — file chứa `from cryptography.fernet import Fernet` bị flag
- `test_detect_yara_match` — file chứa `RANSOMWARE_SIMULATOR_DEMO_SAFE` bị flag CRITICAL
- `test_clean_file_no_false_positive` — file Python bình thường không bị flag

### test_behavior_monitor.py (2 tests)
- `test_detect_new_encrypted_file` — tạo file `.encrypted` trong snapshot → phát hiện
- `test_detect_original_file_deleted` — xóa file gốc khỏi snapshot → phát hiện

**Tổng: 5 tests mới + 10 tests hiện có = 15 tests, tất cả phải pass.**

---

## Nguyên Tắc An Toàn

| Thành phần | Cách triển khai |
|-----------|----------------|
| fake_installer.py | Tái dụng `_is_inside_sandbox()` — chỉ mã hóa `victim_sandbox/` |
| victim_sandbox | Backup trước mỗi demo run, auto-restore sau |
| HTML badges | Tất cả 3 trang HTML đều có "⚠️ DEMO ONLY — Academic Environment" |
| Không network | Không có HTTP request thật, không gửi key đi đâu |

---

## Dependencies

Không thêm dependency mới — tái dụng hoàn toàn:
- `cryptography` (Fernet) — đã có trong `requirements.txt`
- `yara-python` — đã có
- `pytest` — đã có
- `subprocess`, `os`, `time` — stdlib Python
