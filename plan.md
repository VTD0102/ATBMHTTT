# Ransomware Demo — Phòng Chống Mã Độc TMĐT

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây dựng hệ thống demo 2 chiều — ransomware simulator (an toàn, chỉ trong sandbox) và defender (scanner + decryptor + backup) — phục vụ báo cáo học thuật ATTT/TMĐT.

**Architecture:** Attacker side chạy ransomware_simulator.py mã hóa Fernet chỉ trong thư mục `attacker/sandbox/`, key lưu local (không gửi đi), kèm ransom note HTML. Defender side gồm scanner entropy-based, YARA rules detect simulator signature, decryptor dùng saved key, và backup manager tự động. Toàn bộ chạy Python 3 local, không cần internet, không đụng system file.

**Tech Stack:** Python 3.10+, cryptography (Fernet), yara-python, pytest, HTML/CSS (ransom note UI)

---

## Cấu Trúc File

```
ransomware-demo/
├── attacker/
│   ├── ransomware_simulator.py     # Core: mã hóa Fernet, sandbox-only
│   ├── ransom_note.html            # UI "màn hình bị khóa"
│   └── sandbox/                    # Thư mục bị "tấn công"
│       ├── invoice_2024.txt
│       ├── customer_data.csv
│       ├── contract.txt
│       └── README.md
├── defender/
│   ├── scanner.py                  # Entropy analysis + extension check
│   ├── decryptor.py                # Giải mã với key file
│   ├── backup_manager.py           # Backup định kỳ + restore
│   └── rules/
│       └── ransomware.yar          # YARA rules detect simulator
├── tests/
│   ├── test_simulator.py
│   ├── test_scanner.py
│   └── test_backup.py
├── requirements.txt
├── demo_run.sh                     # Script chạy full demo
└── plan.md
```

---

## Task 1: Project Setup

**Files:**
- Create: `ransomware-demo/requirements.txt`
- Create: `ransomware-demo/attacker/sandbox/invoice_2024.txt`
- Create: `ransomware-demo/attacker/sandbox/customer_data.csv`
- Create: `ransomware-demo/attacker/sandbox/contract.txt`

- [ ] **Step 1: Tạo thư mục project**

```bash
mkdir -p ransomware-demo/attacker/sandbox
mkdir -p ransomware-demo/defender/rules
mkdir -p ransomware-demo/tests
```

- [ ] **Step 2: Tạo requirements.txt**

```
cryptography==42.0.8
yara-python==4.5.1
pytest==8.2.2
```

- [ ] **Step 3: Tạo sample files trong sandbox**

`ransomware-demo/attacker/sandbox/invoice_2024.txt`:
```
HOA DON TMDT - MA HD: TMD-2024-0042
Khach hang: Nguyen Van A
San pham: Laptop Dell XPS 15 x2
Tong tien: 45,000,000 VND
Ngay: 2024-01-15
```

`ransomware-demo/attacker/sandbox/customer_data.csv`:
```csv
id,name,email,phone,order_value
1,Nguyen Van A,nva@email.com,0901234567,45000000
2,Tran Thi B,ttb@email.com,0912345678,12500000
3,Le Van C,lvc@email.com,0923456789,8750000
```

`ransomware-demo/attacker/sandbox/contract.txt`:
```
HOP DONG CUNG CAP DICH VU TMDT
Ben A: Cong ty XYZ
Ben B: Doi tac ABC
Gia tri hop dong: 200,000,000 VND
Thoi han: 12 thang
```

- [ ] **Step 4: Cài dependencies**

```bash
cd ransomware-demo
pip install -r requirements.txt
```

Expected: Successfully installed cryptography, yara-python, pytest

- [ ] **Step 5: Commit**

```bash
cd ransomware-demo
git add requirements.txt attacker/sandbox/
git commit -m "feat: project setup with sandbox sample files"
```

---

## Task 2: Ransomware Simulator (Attacker Side)

**Files:**
- Create: `ransomware-demo/attacker/ransomware_simulator.py`
- Create: `ransomware-demo/tests/test_simulator.py`

- [ ] **Step 1: Viết failing test**

`ransomware-demo/tests/test_simulator.py`:
```python
import os
import sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from attacker.ransomware_simulator import RansomwareSimulator

SANDBOX = os.path.join(os.path.dirname(__file__), '..', 'attacker', 'sandbox')

def test_only_encrypts_sandbox(tmp_path):
    """Simulator KHÔNG được đụng file ngoài sandbox."""
    sim = RansomwareSimulator(sandbox_dir=str(tmp_path / "sandbox"))
    os.makedirs(tmp_path / "sandbox")
    (tmp_path / "sandbox" / "test.txt").write_text("hello")
    (tmp_path / "outside.txt").write_text("do not touch")
    
    sim.encrypt()
    
    assert (tmp_path / "outside.txt").read_text() == "do not touch"

def test_encrypt_then_decrypt(tmp_path):
    """Mã hóa rồi giải mã phải cho lại nội dung gốc."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    original = "noi dung quan trong"
    (sandbox / "data.txt").write_text(original)
    
    sim = RansomwareSimulator(sandbox_dir=str(sandbox))
    sim.encrypt()
    
    encrypted_file = sandbox / "data.txt.encrypted"
    assert encrypted_file.exists()
    assert not (sandbox / "data.txt").exists()
    
    sim.decrypt()
    assert (sandbox / "data.txt").read_text() == original

def test_key_saved_to_file(tmp_path):
    """Key phải được lưu ra file sau khi mã hóa."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    (sandbox / "x.txt").write_text("x")
    
    sim = RansomwareSimulator(sandbox_dir=str(sandbox))
    sim.encrypt()
    
    assert os.path.exists(sim.key_file)
```

- [ ] **Step 2: Chạy test để xác nhận fail**

```bash
cd ransomware-demo
pytest tests/test_simulator.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'attacker.ransomware_simulator'`

- [ ] **Step 3: Viết ransomware_simulator.py**

`ransomware-demo/attacker/__init__.py`: (file rỗng)

`ransomware-demo/attacker/ransomware_simulator.py`:
```python
import os
import sys
from cryptography.fernet import Fernet

# SAFETY MARKER — scanner/YARA sẽ detect chuỗi này
SIMULATOR_SIGNATURE = "RANSOMWARE_SIMULATOR_DEMO_SAFE"

class RansomwareSimulator:
    ENCRYPTED_EXT = ".encrypted"
    
    def __init__(self, sandbox_dir: str = None):
        base = os.path.dirname(os.path.abspath(__file__))
        self.sandbox_dir = sandbox_dir or os.path.join(base, "sandbox")
        self.key_file = os.path.join(self.sandbox_dir, ".ransom_key")
        self._key = None
    
    def _get_or_create_key(self) -> bytes:
        if self._key:
            return self._key
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as f:
                self._key = f.read()
        else:
            self._key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(self._key)
        return self._key
    
    def _is_inside_sandbox(self, path: str) -> bool:
        real_sandbox = os.path.realpath(self.sandbox_dir)
        real_path = os.path.realpath(path)
        return real_path.startswith(real_sandbox + os.sep) or real_path == real_sandbox
    
    def encrypt(self):
        key = self._get_or_create_key()
        fernet = Fernet(key)
        
        for root, _, files in os.walk(self.sandbox_dir):
            for filename in files:
                if filename.endswith(self.ENCRYPTED_EXT) or filename == ".ransom_key":
                    continue
                filepath = os.path.join(root, filename)
                if not self._is_inside_sandbox(filepath):
                    continue
                
                with open(filepath, "rb") as f:
                    data = f.read()
                encrypted = fernet.encrypt(data)
                
                enc_path = filepath + self.ENCRYPTED_EXT
                with open(enc_path, "wb") as f:
                    f.write(encrypted)
                os.remove(filepath)
        
        print(f"[SIMULATOR] {SIMULATOR_SIGNATURE}")
        print(f"[SIMULATOR] Files encrypted in: {self.sandbox_dir}")
        print(f"[SIMULATOR] Key saved to: {self.key_file}")
    
    def decrypt(self):
        if not os.path.exists(self.key_file):
            print("[ERROR] Key file not found. Cannot decrypt.")
            sys.exit(1)
        
        key = self._get_or_create_key()
        fernet = Fernet(key)
        
        for root, _, files in os.walk(self.sandbox_dir):
            for filename in files:
                if not filename.endswith(self.ENCRYPTED_EXT):
                    continue
                enc_path = os.path.join(root, filename)
                if not self._is_inside_sandbox(enc_path):
                    continue
                
                with open(enc_path, "rb") as f:
                    encrypted_data = f.read()
                data = fernet.decrypt(encrypted_data)
                
                original_path = enc_path[:-len(self.ENCRYPTED_EXT)]
                with open(original_path, "wb") as f:
                    f.write(data)
                os.remove(enc_path)
        
        print("[SIMULATOR] Decryption complete.")


if __name__ == "__main__":
    sim = RansomwareSimulator()
    if len(sys.argv) > 1 and sys.argv[1] == "decrypt":
        print("[SIMULATOR] Decrypting files...")
        sim.decrypt()
    else:
        print("[SIMULATOR] Starting encryption (SANDBOX ONLY)...")
        sim.encrypt()
```

- [ ] **Step 4: Chạy test**

```bash
cd ransomware-demo
pytest tests/test_simulator.py -v
```

Expected:
```
PASSED tests/test_simulator.py::test_only_encrypts_sandbox
PASSED tests/test_simulator.py::test_encrypt_then_decrypt
PASSED tests/test_simulator.py::test_key_saved_to_file
```

- [ ] **Step 5: Commit**

```bash
git add attacker/ tests/test_simulator.py
git commit -m "feat: ransomware simulator - sandbox-only Fernet encryption with safety marker"
```

---

## Task 3: Ransom Note UI

**Files:**
- Create: `ransomware-demo/attacker/ransom_note.html`

- [ ] **Step 1: Tạo ransom_note.html**

`ransomware-demo/attacker/ransom_note.html`:
```html
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>⚠️ YOUR FILES HAVE BEEN ENCRYPTED</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #0a0a0a;
    color: #ff3333;
    font-family: 'Courier New', monospace;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
  }
  .container {
    max-width: 700px;
    text-align: center;
    padding: 40px;
    border: 2px solid #ff3333;
    box-shadow: 0 0 40px rgba(255,51,51,0.4);
  }
  h1 { font-size: 2rem; margin-bottom: 20px; animation: blink 1s infinite; }
  @keyframes blink { 50% { opacity: 0.4; } }
  .skull { font-size: 5rem; margin: 20px 0; }
  .timer { font-size: 3rem; color: #ffaa00; margin: 20px 0; }
  .message { color: #ccc; line-height: 1.8; margin: 20px 0; font-size: 0.95rem; }
  .amount { color: #ffaa00; font-size: 1.5rem; font-weight: bold; margin: 20px 0; }
  .input-section { margin-top: 30px; }
  input[type="text"] {
    width: 100%;
    padding: 12px;
    background: #1a1a1a;
    border: 1px solid #ff3333;
    color: #ff3333;
    font-family: 'Courier New', monospace;
    font-size: 1rem;
    text-align: center;
  }
  button {
    margin-top: 12px;
    padding: 12px 30px;
    background: #ff3333;
    color: #000;
    border: none;
    font-family: 'Courier New', monospace;
    font-size: 1rem;
    font-weight: bold;
    cursor: pointer;
  }
  button:hover { background: #ff6666; }
  .edu-badge {
    position: fixed;
    bottom: 10px;
    right: 10px;
    background: #1a3a1a;
    color: #44ff44;
    border: 1px solid #44ff44;
    padding: 6px 12px;
    font-size: 0.75rem;
    font-family: monospace;
  }
  .result { margin-top: 15px; font-size: 1rem; }
  .success { color: #44ff44; }
  .fail { color: #ff6666; }
</style>
</head>
<body>
<div class="container">
  <div class="skull">💀</div>
  <h1>YOUR FILES HAVE BEEN ENCRYPTED</h1>
  <p class="message">
    Tất cả dữ liệu trong hệ thống của bạn đã bị mã hóa.<br>
    Các file: <code>invoice_2024.txt</code>, <code>customer_data.csv</code>, <code>contract.txt</code><br>
    đã bị chuyển thành định dạng <code>.encrypted</code>.
  </p>
  <div class="amount">Tiền chuộc: 0.5 BTC (~$30,000 USD)</div>
  <p class="message">
    Bạn có <strong>72 giờ</strong> để thanh toán.<br>
    Sau thời hạn, key sẽ bị xóa vĩnh viễn.
  </p>
  <div class="timer" id="timer">71:59:59</div>
  <div class="input-section">
    <p style="color:#999; margin-bottom:8px;">Nhập mã giải mã:</p>
    <input type="text" id="decryptCode" placeholder="XXXX-XXXX-XXXX-XXXX" />
    <br>
    <button onclick="checkCode()">UNLOCK FILES</button>
    <div class="result" id="result"></div>
  </div>
</div>
<div class="edu-badge">⚠️ MÔI TRƯỜNG HỌC THUẬT — DEMO ONLY</div>

<script>
  // Demo unlock code
  const DEMO_CODE = "DEMO-SAFE-2024-TMDT";
  
  function checkCode() {
    const input = document.getElementById('decryptCode').value.trim().toUpperCase();
    const result = document.getElementById('result');
    if (input === DEMO_CODE) {
      result.className = 'result success';
      result.textContent = '✓ Mã đúng! Files đang được giải mã... Chạy: python attacker/ransomware_simulator.py decrypt';
    } else {
      result.className = 'result fail';
      result.textContent = '✗ Mã sai. Còn ' + Math.floor(Math.random() * 5 + 1) + ' lần thử.';
    }
  }
  
  // Countdown timer
  let seconds = 72 * 3600 - 1;
  function updateTimer() {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    document.getElementById('timer').textContent =
      String(h).padStart(2,'0') + ':' + String(m).padStart(2,'0') + ':' + String(s).padStart(2,'0');
    if (seconds > 0) seconds--;
  }
  setInterval(updateTimer, 1000);
</script>
</body>
</html>
```

- [ ] **Step 2: Kiểm tra UI trong browser**

```bash
# Mở file trong browser
xdg-open ransomware-demo/attacker/ransom_note.html
# Hoặc: firefox ransomware-demo/attacker/ransom_note.html
```

Kiểm tra: timer đếm ngược, nhập `DEMO-SAFE-2024-TMDT` → thông báo thành công, badge "MÔI TRƯỜNG HỌC THUẬT" hiển thị.

- [ ] **Step 3: Commit**

```bash
git add attacker/ransom_note.html
git commit -m "feat: ransom note HTML UI with countdown timer and demo unlock code"
```

---

## Task 4: Scanner (Defender Side)

**Files:**
- Create: `ransomware-demo/defender/scanner.py`
- Create: `ransomware-demo/tests/test_scanner.py`
- Create: `ransomware-demo/defender/__init__.py`

Scanner phát hiện ransomware qua 3 dấu hiệu: (1) entropy cao bất thường, (2) extension `.encrypted`, (3) SIMULATOR_SIGNATURE trong file Python.

- [ ] **Step 1: Viết failing test**

`ransomware-demo/tests/test_scanner.py`:
```python
import os
import sys
import math
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from defender.scanner import RansomwareScanner

def make_high_entropy_file(path):
    """Tạo file với entropy cao (giống file bị mã hóa)."""
    import os as _os
    data = _os.urandom(1024)
    with open(path, 'wb') as f:
        f.write(data)

def make_low_entropy_file(path, content="hello world this is plain text " * 20):
    with open(path, 'w') as f:
        f.write(content)

def test_detect_encrypted_extension(tmp_path):
    """File .encrypted phải bị đánh dấu suspicious."""
    f = tmp_path / "data.txt.encrypted"
    f.write_bytes(b"some data")
    scanner = RansomwareScanner(scan_dir=str(tmp_path))
    results = scanner.scan()
    assert any(r["file"].endswith(".encrypted") for r in results)
    assert any(r["reason"] == "encrypted_extension" for r in results)

def test_detect_high_entropy(tmp_path):
    """File có entropy cao (>7.5) phải bị flag."""
    f = tmp_path / "normal.txt"
    make_high_entropy_file(str(f))
    scanner = RansomwareScanner(scan_dir=str(tmp_path))
    results = scanner.scan()
    assert any(r["reason"] == "high_entropy" for r in results)

def test_no_false_positive_plain_text(tmp_path):
    """File text bình thường không bị flag entropy."""
    f = tmp_path / "readme.txt"
    make_low_entropy_file(str(f))
    scanner = RansomwareScanner(scan_dir=str(tmp_path))
    results = scanner.scan()
    entropy_flags = [r for r in results if r["reason"] == "high_entropy"]
    assert len(entropy_flags) == 0

def test_detect_simulator_signature(tmp_path):
    """File chứa RANSOMWARE_SIMULATOR_DEMO_SAFE bị detect."""
    f = tmp_path / "suspect.py"
    f.write_text('SIMULATOR_SIGNATURE = "RANSOMWARE_SIMULATOR_DEMO_SAFE"')
    scanner = RansomwareScanner(scan_dir=str(tmp_path))
    results = scanner.scan()
    assert any(r["reason"] == "simulator_signature" for r in results)
```

- [ ] **Step 2: Chạy test để xác nhận fail**

```bash
cd ransomware-demo
pytest tests/test_scanner.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'defender.scanner'`

- [ ] **Step 3: Viết scanner.py**

`ransomware-demo/defender/__init__.py`: (file rỗng)

`ransomware-demo/defender/scanner.py`:
```python
import os
import math
from typing import List, Dict

SUSPICIOUS_EXTENSIONS = {".encrypted", ".locked", ".crypto", ".crypt", ".enc"}
ENTROPY_THRESHOLD = 7.5
SIMULATOR_SIGNATURE = "RANSOMWARE_SIMULATOR_DEMO_SAFE"


def calculate_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    freq = {}
    for byte in data:
        freq[byte] = freq.get(byte, 0) + 1
    length = len(data)
    entropy = 0.0
    for count in freq.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy


class RansomwareScanner:
    def __init__(self, scan_dir: str):
        self.scan_dir = scan_dir
        self.findings: List[Dict] = []

    def scan(self) -> List[Dict]:
        self.findings = []
        for root, _, files in os.walk(self.scan_dir):
            for filename in files:
                filepath = os.path.join(root, filename)
                self._check_file(filepath)
        return self.findings

    def _check_file(self, filepath: str):
        _, ext = os.path.splitext(filepath)
        if ext.lower() in SUSPICIOUS_EXTENSIONS:
            self.findings.append({
                "file": filepath,
                "reason": "encrypted_extension",
                "severity": "HIGH",
                "detail": f"Extension '{ext}' thường dùng bởi ransomware"
            })

        try:
            with open(filepath, "rb") as f:
                data = f.read(4096)
            entropy = calculate_entropy(data)
            if entropy > ENTROPY_THRESHOLD:
                self.findings.append({
                    "file": filepath,
                    "reason": "high_entropy",
                    "severity": "MEDIUM",
                    "detail": f"Entropy = {entropy:.2f} (ngưỡng: {ENTROPY_THRESHOLD})"
                })
        except (IOError, PermissionError):
            pass

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(8192)
            if SIMULATOR_SIGNATURE in content:
                self.findings.append({
                    "file": filepath,
                    "reason": "simulator_signature",
                    "severity": "CRITICAL",
                    "detail": "Phát hiện signature của ransomware simulator"
                })
        except (IOError, PermissionError):
            pass

    def report(self):
        if not self.findings:
            print("[SCANNER] ✓ Không phát hiện mối đe dọa.")
            return
        print(f"\n[SCANNER] ⚠️  Phát hiện {len(self.findings)} mối đe dọa:\n")
        for i, f in enumerate(self.findings, 1):
            print(f"  [{i}] {f['severity']} | {f['reason']}")
            print(f"       File: {f['file']}")
            print(f"       Chi tiết: {f['detail']}\n")


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    print(f"[SCANNER] Quét thư mục: {target}")
    scanner = RansomwareScanner(scan_dir=target)
    scanner.scan()
    scanner.report()
```

- [ ] **Step 4: Chạy test**

```bash
cd ransomware-demo
pytest tests/test_scanner.py -v
```

Expected:
```
PASSED tests/test_scanner.py::test_detect_encrypted_extension
PASSED tests/test_scanner.py::test_detect_high_entropy
PASSED tests/test_scanner.py::test_no_false_positive_plain_text
PASSED tests/test_scanner.py::test_detect_simulator_signature
```

- [ ] **Step 5: Commit**

```bash
git add defender/ tests/test_scanner.py
git commit -m "feat: ransomware scanner - entropy analysis and signature detection"
```

---

## Task 5: YARA Rules

**Files:**
- Create: `ransomware-demo/defender/rules/ransomware.yar`

YARA rules detect simulator theo signature string và pattern extension `.encrypted`.

- [ ] **Step 1: Tạo ransomware.yar**

`ransomware-demo/defender/rules/ransomware.yar`:
```yara
rule RansomwareSimulator_Demo {
    meta:
        description = "Phat hien ransomware simulator dung cho demo hoc thuat"
        author = "ATBMHTTT Demo Project"
        severity = "CRITICAL"
        type = "simulator"
    
    strings:
        $sig1 = "RANSOMWARE_SIMULATOR_DEMO_SAFE" ascii
        $sig2 = "RansomwareSimulator" ascii
        $sig3 = "ENCRYPTED_EXT = \".encrypted\"" ascii
    
    condition:
        any of them
}

rule EncryptedFilePattern {
    meta:
        description = "File co dau hieu bi ransomware ma hoa (entropy cao)"
        severity = "HIGH"
        type = "encrypted_data"
    
    strings:
        $fernet_header = { 67 41 41 41 41 }  // Fernet token bắt đầu bằng "gAAAA" (base64)
    
    condition:
        $fernet_header at 0
}

rule RansomNoteHTML {
    meta:
        description = "Phat hien ransom note HTML"
        severity = "HIGH"
        type = "ransom_note"
    
    strings:
        $note1 = "YOUR FILES HAVE BEEN ENCRYPTED" ascii wide
        $note2 = "Bitcoin" nocase ascii
        $note3 = "decrypt" nocase ascii
        $timer = "countdown" nocase ascii
    
    condition:
        ($note1 or $note2) and $note3
}
```

- [ ] **Step 2: Kiểm tra YARA detect được simulator**

```bash
cd ransomware-demo
python3 -c "
import yara
rules = yara.compile('defender/rules/ransomware.yar')
matches = rules.match('attacker/ransomware_simulator.py')
print('YARA matches:', [m.rule for m in matches])
"
```

Expected: `YARA matches: ['RansomwareSimulator_Demo']`

- [ ] **Step 3: Kiểm tra YARA detect ransom note**

```bash
cd ransomware-demo
python3 -c "
import yara
rules = yara.compile('defender/rules/ransomware.yar')
matches = rules.match('attacker/ransom_note.html')
print('YARA matches:', [m.rule for m in matches])
"
```

Expected: `YARA matches: ['RansomNoteHTML']`

- [ ] **Step 4: Commit**

```bash
git add defender/rules/ransomware.yar
git commit -m "feat: YARA rules for ransomware simulator and ransom note detection"
```

---

## Task 6: Decryptor

**Files:**
- Create: `ransomware-demo/defender/decryptor.py`

- [ ] **Step 1: Tạo decryptor.py**

`ransomware-demo/defender/decryptor.py`:
```python
import os
import sys
from cryptography.fernet import Fernet, InvalidToken


def decrypt_sandbox(sandbox_dir: str, key_file: str = None):
    if key_file is None:
        key_file = os.path.join(sandbox_dir, ".ransom_key")
    
    if not os.path.exists(key_file):
        print(f"[DECRYPTOR] Không tìm thấy key file: {key_file}")
        sys.exit(1)
    
    with open(key_file, "rb") as f:
        key = f.read()
    
    fernet = Fernet(key)
    count = 0
    errors = 0
    
    for root, _, files in os.walk(sandbox_dir):
        for filename in files:
            if not filename.endswith(".encrypted"):
                continue
            enc_path = os.path.join(root, filename)
            original_path = enc_path[:-len(".encrypted")]
            
            try:
                with open(enc_path, "rb") as f:
                    encrypted_data = f.read()
                data = fernet.decrypt(encrypted_data)
                with open(original_path, "wb") as f:
                    f.write(data)
                os.remove(enc_path)
                print(f"[DECRYPTOR] ✓ Khôi phục: {os.path.basename(original_path)}")
                count += 1
            except InvalidToken:
                print(f"[DECRYPTOR] ✗ Key sai hoặc file bị hỏng: {filename}")
                errors += 1
    
    print(f"\n[DECRYPTOR] Kết quả: {count} file khôi phục, {errors} lỗi.")


if __name__ == "__main__":
    sandbox = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), '..', 'attacker', 'sandbox'
    )
    decrypt_sandbox(sandbox_dir=sandbox)
```

- [ ] **Step 2: Test thủ công (end-to-end)**

```bash
cd ransomware-demo
# Bước 1: Chạy simulator để mã hóa
python attacker/ransomware_simulator.py
ls attacker/sandbox/  # Phải thấy file .encrypted

# Bước 2: Chạy scanner phát hiện
python defender/scanner.py attacker/sandbox/

# Bước 3: Giải mã
python defender/decryptor.py attacker/sandbox/
ls attacker/sandbox/  # Phải thấy lại file gốc
```

- [ ] **Step 3: Commit**

```bash
git add defender/decryptor.py
git commit -m "feat: decryptor to restore sandbox files using saved Fernet key"
```

---

## Task 7: Backup Manager

**Files:**
- Create: `ransomware-demo/defender/backup_manager.py`
- Create: `ransomware-demo/tests/test_backup.py`

- [ ] **Step 1: Viết failing test**

`ransomware-demo/tests/test_backup.py`:
```python
import os
import sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from defender.backup_manager import BackupManager

def test_backup_creates_archive(tmp_path):
    """Backup phải tạo file .tar.gz trong backup_dir."""
    source = tmp_path / "data"
    source.mkdir()
    (source / "file.txt").write_text("important data")
    backup_dir = tmp_path / "backups"
    
    mgr = BackupManager(source_dir=str(source), backup_dir=str(backup_dir))
    backup_path = mgr.backup()
    
    assert os.path.exists(backup_path)
    assert backup_path.endswith(".tar.gz")

def test_restore_recovers_files(tmp_path):
    """Restore từ backup phải khôi phục nội dung gốc."""
    source = tmp_path / "data"
    source.mkdir()
    (source / "important.txt").write_text("critical content")
    backup_dir = tmp_path / "backups"
    restore_dir = tmp_path / "restored"
    
    mgr = BackupManager(source_dir=str(source), backup_dir=str(backup_dir))
    backup_path = mgr.backup()
    
    mgr.restore(backup_path=backup_path, restore_dir=str(restore_dir))
    
    restored_file = restore_dir / "important.txt"
    assert restored_file.exists()
    assert restored_file.read_text() == "critical content"

def test_list_backups(tmp_path):
    """list_backups phải trả về danh sách backup đã tạo."""
    source = tmp_path / "data"
    source.mkdir()
    (source / "x.txt").write_text("x")
    backup_dir = tmp_path / "backups"
    
    mgr = BackupManager(source_dir=str(source), backup_dir=str(backup_dir))
    mgr.backup()
    mgr.backup()
    
    backups = mgr.list_backups()
    assert len(backups) == 2
```

- [ ] **Step 2: Chạy test để xác nhận fail**

```bash
cd ransomware-demo
pytest tests/test_backup.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'defender.backup_manager'`

- [ ] **Step 3: Viết backup_manager.py**

`ransomware-demo/defender/backup_manager.py`:
```python
import os
import sys
import tarfile
from datetime import datetime
from typing import List


class BackupManager:
    def __init__(self, source_dir: str, backup_dir: str):
        self.source_dir = source_dir
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
    
    def backup(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"backup_{timestamp}.tar.gz"
        archive_path = os.path.join(self.backup_dir, archive_name)
        
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(self.source_dir, arcname=os.path.basename(self.source_dir))
        
        size_kb = os.path.getsize(archive_path) / 1024
        print(f"[BACKUP] ✓ Đã backup: {archive_name} ({size_kb:.1f} KB)")
        return archive_path
    
    def restore(self, backup_path: str, restore_dir: str):
        os.makedirs(restore_dir, exist_ok=True)
        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(path=restore_dir)
        
        # Di chuyển file ra ngoài thư mục con
        extracted_subdir = os.path.join(restore_dir, os.path.basename(self.source_dir))
        if os.path.isdir(extracted_subdir):
            for item in os.listdir(extracted_subdir):
                src = os.path.join(extracted_subdir, item)
                dst = os.path.join(restore_dir, item)
                os.rename(src, dst)
            os.rmdir(extracted_subdir)
        
        print(f"[BACKUP] ✓ Đã restore từ: {os.path.basename(backup_path)}")
    
    def list_backups(self) -> List[str]:
        backups = sorted([
            os.path.join(self.backup_dir, f)
            for f in os.listdir(self.backup_dir)
            if f.startswith("backup_") and f.endswith(".tar.gz")
        ])
        return backups


if __name__ == "__main__":
    import sys
    action = sys.argv[1] if len(sys.argv) > 1 else "backup"
    sandbox = os.path.join(os.path.dirname(__file__), '..', 'attacker', 'sandbox')
    backup_dir = os.path.join(os.path.dirname(__file__), '..', 'backups')
    
    mgr = BackupManager(source_dir=sandbox, backup_dir=backup_dir)
    
    if action == "list":
        backups = mgr.list_backups()
        print(f"[BACKUP] {len(backups)} backup(s):")
        for b in backups:
            print(f"  - {os.path.basename(b)}")
    elif action == "restore" and len(sys.argv) > 2:
        mgr.restore(backup_path=sys.argv[2], restore_dir=sandbox)
    else:
        mgr.backup()
```

- [ ] **Step 4: Chạy test**

```bash
cd ransomware-demo
pytest tests/test_backup.py -v
```

Expected:
```
PASSED tests/test_backup.py::test_backup_creates_archive
PASSED tests/test_backup.py::test_restore_recovers_files
PASSED tests/test_backup.py::test_list_backups
```

- [ ] **Step 5: Commit**

```bash
git add defender/backup_manager.py tests/test_backup.py
git commit -m "feat: backup manager with tar.gz archive and restore capability"
```

---

## Task 8: Demo Script + Chạy Toàn Bộ

**Files:**
- Create: `ransomware-demo/demo_run.sh`

- [ ] **Step 1: Tạo demo_run.sh**

`ransomware-demo/demo_run.sh`:
```bash
#!/bin/bash
set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}========================================"
echo "   RANSOMWARE DEMO - MÔI TRƯỜNG HỌC THUẬT"
echo -e "========================================${NC}"
echo ""

echo -e "${GREEN}[BƯỚC 1] Backup dữ liệu trước khi tấn công...${NC}"
python defender/backup_manager.py backup
echo ""

echo -e "${GREEN}[BƯỚC 2] Trạng thái sandbox TRƯỚC tấn công:${NC}"
ls -la attacker/sandbox/
echo ""

echo -e "${RED}[BƯỚC 3] ATTACKER: Chạy ransomware simulator...${NC}"
python attacker/ransomware_simulator.py
echo ""

echo -e "${RED}[BƯỚC 4] Trạng thái sandbox SAU tấn công:${NC}"
ls -la attacker/sandbox/
echo ""

echo -e "${GREEN}[BƯỚC 5] DEFENDER: Chạy scanner...${NC}"
python defender/scanner.py attacker/sandbox/
echo ""

echo -e "${GREEN}[BƯỚC 6] DEFENDER: Quét YARA rules...${NC}"
python3 -c "
import yara, os
rules = yara.compile('defender/rules/ransomware.yar')
target = 'attacker/ransomware_simulator.py'
matches = rules.match(target)
if matches:
    print('[YARA] PHÁT HIỆN:', [m.rule for m in matches])
else:
    print('[YARA] Không có match')
"
echo ""

echo -e "${YELLOW}[BƯỚC 7] Mở ransom note (xem màn hình bị khóa)...${NC}"
echo "Mở file: attacker/ransom_note.html trong browser"
echo "Nhập mã demo: DEMO-SAFE-2024-TMDT"
echo ""

echo -e "${GREEN}[BƯỚC 8] DEFENDER: Giải mã với key...${NC}"
python defender/decryptor.py attacker/sandbox/
echo ""

echo -e "${GREEN}[BƯỚC 9] Trạng thái sandbox SAU giải mã:${NC}"
ls -la attacker/sandbox/
echo ""

echo -e "${GREEN}========================================"
echo "   DEMO HOÀN TẤT"
echo -e "========================================${NC}"
```

- [ ] **Step 2: Chạy toàn bộ test suite**

```bash
cd ransomware-demo
pytest tests/ -v
```

Expected:
```
PASSED tests/test_simulator.py::test_only_encrypts_sandbox
PASSED tests/test_simulator.py::test_encrypt_then_decrypt
PASSED tests/test_simulator.py::test_key_saved_to_file
PASSED tests/test_scanner.py::test_detect_encrypted_extension
PASSED tests/test_scanner.py::test_detect_high_entropy
PASSED tests/test_scanner.py::test_no_false_positive_plain_text
PASSED tests/test_scanner.py::test_detect_simulator_signature
PASSED tests/test_backup.py::test_backup_creates_archive
PASSED tests/test_backup.py::test_restore_recovers_files
PASSED tests/test_backup.py::test_list_backups
10 passed
```

- [ ] **Step 3: Chạy demo script**

```bash
cd ransomware-demo
chmod +x demo_run.sh
./demo_run.sh
```

- [ ] **Step 4: Commit cuối**

```bash
git add demo_run.sh
git commit -m "feat: demo_run.sh integration script for full ransomware demo"
```

---

## Tóm Tắt Kiến Trúc Demo

```
ATTACKER SIDE                    DEFENDER SIDE
─────────────────                ──────────────────────────────
ransomware_simulator.py          scanner.py
  → Fernet encrypt                 → entropy analysis
  → chỉ trong sandbox/             → extension check  
  → lưu key local                  → signature detection
  → in SIMULATOR_SIGNATURE       
                                 rules/ransomware.yar
ransom_note.html                   → YARA pattern matching
  → UI đếm ngược 72h             
  → nhập mã giải mã              decryptor.py
  → badge "DEMO ONLY"              → Fernet decrypt với key
                                   → khôi phục file gốc

                                 backup_manager.py
                                   → tar.gz backup
                                   → restore từ backup
```

**Nguyên tắc an toàn đã áp dụng:**
- Sandbox isolation: `_is_inside_sandbox()` kiểm tra path tuyệt đối
- Key không gửi đi đâu (local only)
- SIMULATOR_SIGNATURE để scanner dễ detect
- Badge "MÔI TRƯỜNG HỌC THUẬT" trên UI
- Không có tính năng self-spread
