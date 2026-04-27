# Fake Manager — Design Spec

**Date:** 2026-04-27
**Project:** ATBMHTTT — Academic Security Demo
**Scope:** Thêm kịch bản social engineering mới vào `social-engineering/`: fake Project Manager GUI (Tkinter) yêu cầu nhập API key để "kích hoạt", sau đó mã hóa dữ liệu ngầm.

---

## Mục Tiêu

Minh họa kịch bản tấn công social engineering qua phần mềm giả mạo: nạn nhân tải "ProManager Suite" về, mở lên thấy giao diện desktop chuyên nghiệp, nhập API key để kích hoạt → sau khi "kích hoạt thành công" và dashboard hiển thị, ransomware chạy ngầm rồi ransom note xuất hiện.

Demo chạy trên **1 máy** với 2 flag:
- `--attack-only`: không có phòng thủ → bị mã hóa
- `--with-defender`: static + behavioral defense chặn lại

---

## Cấu Trúc File

```
social-engineering/
├── attacker/
│   ├── fake_manager.py          # MỚI — Tkinter GUI
│   └── victim_sandbox/          # Giữ nguyên
├── demo_manager.sh              # MỚI — script demo riêng
└── tests/
    └── test_fake_manager.py     # MỚI — 2 tests
```

**Tái sử dụng:**
- `ransomware-demo/attacker/ransomware_simulator.py` — `RansomwareSimulator`
- `ransomware-demo/attacker/ransom_note.html` — màn hình ransom
- `social-engineering/defender/static_analyzer.py` — phân tích tĩnh
- `social-engineering/defender/behavior_monitor.py` — giám sát filesystem
- `social-engineering/prevention_success.html` — UI chặn thành công

---

## `fake_manager.py` — Tkinter GUI

### Ba màn hình theo thứ tự

**Screen 1 — Activation** (hiện khi mở app):
- Title bar: `ProManager Suite — License Activation`
- Logo icon 📋 + tên app
- Status badge đỏ: `⊗ Unlicensed — Activation Required`
- Label `API License Key` + Entry field (placeholder `sk-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
- Nút `Activate License` (màu tím `#cba6f7`) + nút `Cancel`
- Badge dưới: `⚠ DEMO ONLY — Academic Environment`

**Screen 2 — Verifying** (sau khi bấm Activate, hiển thị ~2 giây):
- Title bar: `ProManager Suite — Activating...`
- Text `Verifying license key...`
- Subtitle `Connecting to license server`
- `ttk.Progressbar` chạy indeterminate mode
- Các bước fake: "Connecting...", "Validating entitlements...", "Configuring workspace..."
- Background thread `_do_activate()`: `time.sleep(2)` → gọi `root.after(0, _show_dashboard)`

**Screen 3 — Dashboard** (hiện sau verify, kéo dài ~4 giây trước ransom):
- Status badge xanh: `✓ License activated — Welcome!`
- Section `Your Projects` với 3 fake project rows:
  - 📁 Q4 Marketing Campaign — Active
  - 📁 Product Launch 2025 — In Progress
  - 📁 Client Onboarding Flow — Active
- Progress bar `Loading your data... [████░░] 80%` (chạy chậm, fake)
- **Ngầm:** `threading.Thread(target=_silent_encrypt, daemon=True).start()`
- `root.after(4000, _trigger_ransom)` — sau 4 giây đóng cửa sổ, mở ransom note

### Hàm riêng (có thể test độc lập)

```python
def trigger_encryption(sandbox_dir: str) -> None:
    """Gọi RansomwareSimulator để mã hóa sandbox."""
    sim = RansomwareSimulator(sandbox_dir=sandbox_dir)
    sim.encrypt()
```

### Safety

- Tái dụng `RansomwareSimulator._is_inside_sandbox()` — chỉ mã hóa `victim_sandbox/`
- Badge `DEMO ONLY` trên tất cả màn hình
- Không có network request thật

### Import path

```python
_base = os.path.dirname(os.path.abspath(__file__))
_ransomware_demo = os.path.abspath(os.path.join(_base, '..', '..', 'ransomware-demo'))
sys.path.insert(0, _ransomware_demo)
from attacker.ransomware_simulator import RansomwareSimulator
```

---

## `demo_manager.sh`

### `--attack-only` (6 bước)

| Bước | Hành động |
|------|-----------|
| 1 | Backup `victim_sandbox/` |
| 2 | In hướng dẫn: "Victim tải ProManager.exe về, double-click chạy" |
| 3 | Chạy `python3 attacker/fake_manager.py` |
| 4 | (Tự động) Dashboard hiển thị → ransom note mở sau 4 giây |
| 5 | Hiển thị `victim_sandbox/` sau tấn công (toàn `.encrypted`) |
| 6 | Restore từ backup |

### `--with-defender` (9 bước)

| Bước | Hành động |
|------|-----------|
| 1 | Backup `victim_sandbox/` |
| 2 | In hướng dẫn: "Victim tải ProManager.exe về" |
| 3 | **Static analyzer quét `fake_manager.py`** → CRITICAL |
| 4 | Cảnh báo — hỏi bypass để demo behavioral |
| 5 | *(Nếu bypass)* Bật behavior monitor |
| 6 | Chạy `fake_manager.py` (monitored) |
| 7 | **Behavior monitor kill process** khi phát hiện `.encrypted` |
| 8 | Mở `prevention_success.html` |
| 9 | Restore từ backup |

---

## Tests (`test_fake_manager.py`)

### `test_static_analyzer_detects_fake_manager`
Static analyzer phải trả về ít nhất 1 finding CRITICAL khi quét `fake_manager.py`.
`fake_manager.py` sẽ chứa `from attacker.ransomware_simulator import RansomwareSimulator` (match YARA rule `RansomwareSimulator_Demo`) và `.encrypt(` (match dangerous string).

### `test_fake_manager_encrypts_sandbox`
Gọi `trigger_encryption(victim_sandbox_dir)` trực tiếp (không qua Tkinter), kiểm tra file `.encrypted` xuất hiện, restore.

---

## Dependencies

Không thêm dependency mới:
- `tkinter` — stdlib Python
- `threading`, `subprocess`, `time`, `os`, `sys` — stdlib
- `cryptography` (Fernet) — đã có trong `requirements.txt`

---

## Nguyên Tắc An Toàn

| Thành phần | Cách triển khai |
|-----------|----------------|
| `fake_manager.py` | Tái dụng `_is_inside_sandbox()` qua `RansomwareSimulator` |
| `victim_sandbox` | Backup trước mỗi demo, auto-restore sau |
| Màn hình GUI | Badge `⚠ DEMO ONLY` trên tất cả 3 screen |
| Không network | Không HTTP request thật, không gửi key đi đâu |
