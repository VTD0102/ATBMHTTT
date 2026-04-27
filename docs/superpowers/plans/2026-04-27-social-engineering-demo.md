# Social Engineering Ransomware Demo — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `social-engineering/` module demonstrating ransomware delivered via fake "free GPT API key" lure, with static + behavioral defense, runnable on 1 machine via `--attack-only` / `--with-defender` flags.

**Architecture:** Independent `social-engineering/` folder at repo root; `fake_installer.py` imports `RansomwareSimulator` from existing `ransomware-demo/attacker/` via `sys.path.insert`; `static_analyzer.py` reuses YARA rules from `ransomware-demo/defender/rules/`; `demo_social.sh` opens existing `ransom_note.html` without copying it.

**Tech Stack:** Python 3.10+, cryptography (Fernet), yara-python, pytest, HTML/CSS/JS, bash

---

## File Map

| File | Responsibility |
|------|---------------|
| `social-engineering/attacker/fake_landing.html` | Landing page lure — fake OpenAI developer offer |
| `social-engineering/attacker/fake_key_generator.html` | Animated key UI + "Download SDK" CTA |
| `social-engineering/attacker/fake_installer.py` | Theatrical progress bar + silent ransomware payload |
| `social-engineering/attacker/victim_sandbox/` | 3 target files to be encrypted |
| `social-engineering/defender/static_analyzer.py` | Pre-run static analysis: YARA + string scan |
| `social-engineering/defender/behavior_monitor.py` | Filesystem snapshot polling during installer run |
| `social-engineering/prevention_success.html` | "Threat blocked" UI with timeline |
| `social-engineering/demo_social.sh` | Orchestrates both demo scenarios |
| `social-engineering/tests/test_static_analyzer.py` | 3 tests for static_analyzer |
| `social-engineering/tests/test_behavior_monitor.py` | 2 tests for behavior_monitor |

---

## Task 1: Project Setup

**Files:**
- Create: `social-engineering/attacker/__init__.py`
- Create: `social-engineering/defender/__init__.py`
- Create: `social-engineering/tests/__init__.py`
- Create: `social-engineering/attacker/victim_sandbox/project_data.txt`
- Create: `social-engineering/attacker/victim_sandbox/api_config.json`
- Create: `social-engineering/attacker/victim_sandbox/business_report.csv`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p social-engineering/attacker/victim_sandbox
mkdir -p social-engineering/defender
mkdir -p social-engineering/tests
touch social-engineering/attacker/__init__.py
touch social-engineering/defender/__init__.py
touch social-engineering/tests/__init__.py
```

- [ ] **Step 2: Create victim_sandbox files**

`social-engineering/attacker/victim_sandbox/project_data.txt`:
```
PROJECT: AI Integration Platform
Client: TechVentures Co.
Budget: $250,000
API Quota: 1,000,000 tokens/month
Model: GPT-4 Turbo
Status: In Progress
Deadline: 2024-06-30
```

`social-engineering/attacker/victim_sandbox/api_config.json`:
```json
{
  "service": "openai",
  "model": "gpt-4-turbo",
  "max_tokens": 4096,
  "temperature": 0.7,
  "internal_endpoint": "https://api.internal.company.com/v1",
  "fallback_keys": ["sk-internal-backup-001", "sk-internal-backup-002"]
}
```

`social-engineering/attacker/victim_sandbox/business_report.csv`:
```csv
quarter,revenue,ai_costs,profit
Q1-2024,1250000,45000,1205000
Q2-2024,1480000,62000,1418000
Q3-2024,1690000,78000,1612000
Q4-2024,2100000,95000,2005000
```

- [ ] **Step 3: Commit**

```bash
git add social-engineering/
git commit -m "feat: social-engineering module scaffold and victim_sandbox files"
```

---

## Task 2: Attacker HTML Pages

**Files:**
- Create: `social-engineering/attacker/fake_landing.html`
- Create: `social-engineering/attacker/fake_key_generator.html`

- [ ] **Step 1: Create fake_landing.html**

`social-engineering/attacker/fake_landing.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>OpenAI API — Free Developer Access</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f7f7f8; color: #202123; }
    .navbar { background: #fff; border-bottom: 1px solid #e5e5e5; padding: 16px 40px; display: flex; align-items: center; gap: 12px; }
    .logo { font-size: 1.2rem; font-weight: 700; }
    .hero { max-width: 680px; margin: 80px auto; text-align: center; padding: 0 24px; }
    .badge { display: inline-block; background: #d4edda; color: #155724; border-radius: 20px; padding: 4px 14px; font-size: 0.85rem; font-weight: 600; margin-bottom: 20px; }
    h1 { font-size: 2.8rem; font-weight: 700; line-height: 1.2; margin-bottom: 16px; }
    .subtitle { font-size: 1.1rem; color: #6e6e80; margin-bottom: 40px; line-height: 1.6; }
    .card { background: #fff; border: 1px solid #e5e5e5; border-radius: 12px; padding: 32px; margin-bottom: 20px; }
    input[type="email"] { width: 100%; padding: 14px 16px; border: 1.5px solid #d9d9e3; border-radius: 8px; font-size: 1rem; margin-bottom: 14px; outline: none; }
    input[type="email"]:focus { border-color: #10a37f; }
    .btn { width: 100%; padding: 14px; background: #10a37f; color: #fff; border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; }
    .btn:hover { background: #0d8c6d; }
    .features { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 40px; }
    .feature { background: #fff; border: 1px solid #e5e5e5; border-radius: 8px; padding: 20px; text-align: left; }
    .feature h3 { font-size: 0.95rem; font-weight: 600; margin-bottom: 6px; }
    .feature p { font-size: 0.85rem; color: #6e6e80; }
    .edu-badge { position: fixed; bottom: 10px; right: 10px; background: #fff3cd; color: #856404; border: 1px solid #ffc107; padding: 6px 12px; font-size: 0.75rem; border-radius: 4px; }
  </style>
</head>
<body>
  <nav class="navbar">
    <div class="logo">⬡ OpenAI</div>
    <span style="color:#6e6e80;font-size:0.9rem">Developer Program</span>
  </nav>
  <div class="hero">
    <div class="badge">🎉 Limited Time Offer — Free Tier</div>
    <h1>Get Your Free GPT-4 API Key</h1>
    <p class="subtitle">Access the world's most powerful AI model at no cost. Perfect for developers building the next generation of AI-powered applications.</p>
    <div class="card">
      <form onsubmit="handleSubmit(event)">
        <input type="email" id="email" placeholder="Enter your email address" required>
        <button class="btn" type="submit">Claim Your Free API Key →</button>
      </form>
    </div>
    <div class="features">
      <div class="feature"><h3>⚡ Instant Access</h3><p>API key delivered in seconds</p></div>
      <div class="feature"><h3>🔑 GPT-4 Turbo</h3><p>Full model access, no limits</p></div>
      <div class="feature"><h3>🔒 Secure</h3><p>Enterprise-grade security</p></div>
    </div>
  </div>
  <div class="edu-badge">⚠️ DEMO ONLY — Academic Environment</div>
  <script>
    function handleSubmit(e) {
      e.preventDefault();
      window.location.href = 'fake_key_generator.html?email=' + encodeURIComponent(document.getElementById('email').value);
    }
  </script>
</body>
</html>
```

- [ ] **Step 2: Create fake_key_generator.html**

`social-engineering/attacker/fake_key_generator.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Your API Key is Ready</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f7f7f8; color: #202123; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
    .card { background: #fff; border: 1px solid #e5e5e5; border-radius: 12px; padding: 48px 40px; max-width: 560px; width: 100%; text-align: center; }
    h1 { font-size: 1.8rem; font-weight: 700; margin-bottom: 8px; }
    .subtitle { color: #6e6e80; margin-bottom: 32px; }
    .progress-wrap { background: #f0f0f0; border-radius: 8px; height: 8px; margin-bottom: 8px; overflow: hidden; }
    .progress-bar { height: 100%; background: #10a37f; border-radius: 8px; width: 0; }
    .progress-label { font-size: 0.85rem; color: #6e6e80; margin-bottom: 24px; min-height: 20px; }
    .key-box { background: #f7f7f8; border: 1.5px solid #e5e5e5; border-radius: 8px; padding: 16px; font-family: 'Courier New', monospace; font-size: 1rem; letter-spacing: 0.05em; margin-bottom: 24px; word-break: break-all; }
    .btn { padding: 14px 28px; background: #10a37f; color: #fff; border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; }
    .btn:hover { background: #0d8c6d; }
    .instructions { background: #f0f9f6; border: 1px solid #b2dfdb; border-radius: 8px; padding: 16px; text-align: left; margin-top: 20px; }
    .instructions p { font-size: 0.9rem; margin-bottom: 8px; }
    .instructions code { background: #e0f2f1; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.9rem; }
    .edu-badge { position: fixed; bottom: 10px; right: 10px; background: #fff3cd; color: #856404; border: 1px solid #ffc107; padding: 6px 12px; font-size: 0.75rem; border-radius: 4px; }
    .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #10a37f; margin: 0 3px; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
    #phase-done { display: none; }
  </style>
</head>
<body>
  <div class="card">
    <div id="phase-generating">
      <h1>✨ Generating your API key</h1>
      <p class="subtitle">This will only take a moment<span class="dot"></span><span class="dot" style="animation-delay:.3s"></span><span class="dot" style="animation-delay:.6s"></span></p>
      <div class="progress-wrap"><div class="progress-bar" id="bar"></div></div>
      <p class="progress-label" id="plabel">Initializing secure channel...</p>
    </div>
    <div id="phase-done">
      <h1>🎉 Your API Key is Ready!</h1>
      <p class="subtitle" style="margin-bottom:20px">Save this key — it will only be shown once</p>
      <div class="key-box">sk-demo-4x8K-mN2p-9qRt-XXXXXXXXXXXXXXXX</div>
      <button class="btn" onclick="document.getElementById('instructions').style.display='block'">Download SDK to Activate Key →</button>
      <div class="instructions" id="instructions" style="display:none">
        <p><strong>Activate your API key in 2 steps:</strong></p>
        <p>1. Run the activation SDK:</p>
        <p><code>python fake_installer.py</code></p>
        <p>2. Your key will be automatically configured in your environment.</p>
        <p style="color:#6e6e80;font-size:0.8rem;margin-top:8px">⚙️ The SDK configures your local environment and verifies your key with OpenAI servers.</p>
      </div>
    </div>
  </div>
  <div class="edu-badge">⚠️ DEMO ONLY — Academic Environment</div>
  <script>
    const steps = ["Initializing secure channel...","Verifying developer account...","Allocating API quota...","Generating cryptographic key...","Finalizing activation..."];
    let pct = 0, si = 0;
    const bar = document.getElementById('bar');
    const label = document.getElementById('plabel');
    const iv = setInterval(() => {
      pct += 2;
      bar.style.width = pct + '%';
      if (pct % 20 === 0 && si < steps.length) label.textContent = steps[si++];
      if (pct >= 100) {
        clearInterval(iv);
        setTimeout(() => {
          document.getElementById('phase-generating').style.display = 'none';
          document.getElementById('phase-done').style.display = 'block';
        }, 400);
      }
    }, 60);
  </script>
</body>
</html>
```

- [ ] **Step 3: Verify in browser**

```bash
cd social-engineering
xdg-open attacker/fake_landing.html
```

Check: form submit redirects to `fake_key_generator.html`, progress bar animates ~3s, key box appears, "Download SDK" button reveals instructions.

- [ ] **Step 4: Commit**

```bash
git add social-engineering/attacker/fake_landing.html social-engineering/attacker/fake_key_generator.html
git commit -m "feat: fake landing page and API key generator UI"
```

---

## Task 3: fake_installer.py

**Files:**
- Create: `social-engineering/attacker/fake_installer.py`

- [ ] **Step 1: Create fake_installer.py**

`social-engineering/attacker/fake_installer.py`:
```python
import os
import sys
import time
import subprocess

_base = os.path.dirname(os.path.abspath(__file__))
_ransomware_demo = os.path.abspath(os.path.join(_base, '..', '..', 'ransomware-demo'))
sys.path.insert(0, _ransomware_demo)

from attacker.ransomware_simulator import RansomwareSimulator

VICTIM_SANDBOX = os.path.join(_base, 'victim_sandbox')
RANSOM_NOTE = os.path.join(_ransomware_demo, 'attacker', 'ransom_note.html')

_STEPS = [
    ("Connecting to OpenAI servers...", 0.6),
    ("Downloading OpenAI Python SDK v1.35.0...", 0.9),
    ("Verifying package signature...", 0.5),
    ("Installing dependencies...", 0.7),
    ("Configuring local environment...", 0.6),
]


def _fake_progress():
    for msg, delay in _STEPS:
        print(f"  {msg}", flush=True)
        time.sleep(delay)
    for i in range(0, 101, 5):
        bar = "█" * (i // 5) + "░" * (20 - i // 5)
        print(f"\r  Installing... [{bar}] {i}%", end="", flush=True)
        time.sleep(0.08)
    print()
    time.sleep(0.3)
    print("  Activating API key sk-demo-4x8K-mN2p-9qRt-XXXXXXXXXXXXXXXX... Done!", flush=True)
    time.sleep(0.4)
    print("\n  ✓ OpenAI SDK installed successfully. Your API key is now active.\n", flush=True)


def _silent_encrypt():
    sim = RansomwareSimulator(sandbox_dir=VICTIM_SANDBOX)
    sim.encrypt()


if __name__ == "__main__":
    print("\n[OpenAI SDK Installer]\n")
    _fake_progress()
    _silent_encrypt()
    subprocess.Popen(
        ['xdg-open', RANSOM_NOTE],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
```

- [ ] **Step 2: Manual smoke test**

```bash
cd social-engineering
python3 attacker/fake_installer.py
ls attacker/victim_sandbox/
```

Expected: progress bar prints, then `victim_sandbox/` contains `.encrypted` files and `.ransom_key`.

- [ ] **Step 3: Restore victim_sandbox**

```bash
cd social-engineering
python3 -c "
import sys, os
sys.path.insert(0, os.path.join('..', 'ransomware-demo'))
from attacker.ransomware_simulator import RansomwareSimulator
RansomwareSimulator(sandbox_dir='attacker/victim_sandbox').decrypt()
"
ls attacker/victim_sandbox/
```

Expected: original 3 files restored, no `.encrypted` files.

- [ ] **Step 4: Commit**

```bash
git add social-engineering/attacker/fake_installer.py
git commit -m "feat: fake_installer.py - theatrical OpenAI SDK installer with silent ransomware payload"
```

---

## Task 4: static_analyzer.py (TDD)

**Files:**
- Create: `social-engineering/tests/test_static_analyzer.py`
- Create: `social-engineering/defender/static_analyzer.py`

- [ ] **Step 1: Write failing tests**

`social-engineering/tests/test_static_analyzer.py`:
```python
import os
import sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from defender.static_analyzer import analyze_file


def test_detect_yara_match(tmp_path):
    """File containing RANSOMWARE_SIMULATOR_DEMO_SAFE triggers CRITICAL yara_match."""
    f = tmp_path / "malicious.py"
    f.write_text('SIMULATOR_SIGNATURE = "RANSOMWARE_SIMULATOR_DEMO_SAFE"')
    findings = analyze_file(str(f))
    assert any(r["severity"] == "CRITICAL" and r["reason"] == "yara_match" for r in findings)


def test_detect_fernet_dangerous_strings(tmp_path):
    """File using Fernet encryption + os.walk + os.remove triggers CRITICAL dangerous_strings."""
    f = tmp_path / "suspect.py"
    f.write_text(
        "from cryptography.fernet import Fernet\n"
        "import os\n"
        "for root, _, files in os.walk('.'):\n"
        "    for name in files:\n"
        "        data = Fernet(key).encrypt(open(name,'rb').read())\n"
        "        os.remove(name)\n"
    )
    findings = analyze_file(str(f))
    assert any(r["severity"] == "CRITICAL" and r["reason"] == "dangerous_strings" for r in findings)


def test_clean_file_no_false_positive(tmp_path):
    """Plain Python file with no suspicious content returns empty findings list."""
    f = tmp_path / "clean.py"
    f.write_text("import math\nprint(math.pi)\n")
    findings = analyze_file(str(f))
    assert findings == []
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd social-engineering
python3 -m pytest tests/test_static_analyzer.py -v
```

Expected: `ModuleNotFoundError: No module named 'defender.static_analyzer'`

- [ ] **Step 3: Implement static_analyzer.py**

`social-engineering/defender/static_analyzer.py`:
```python
import os
import sys
from typing import List, Dict

try:
    import yara
    _YARA_AVAILABLE = True
except ImportError:
    _YARA_AVAILABLE = False

_YARA_RULES_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', 'ransomware-demo', 'defender', 'rules', 'ransomware.yar'
))

_CRITICAL_STRINGS = [
    "RANSOMWARE_SIMULATOR_DEMO_SAFE",
    ".encrypt(",
    "fernet.encrypt",
    "Fernet.generate_key",
]

_SUSPICIOUS_COMBO = ["cryptography", "os.walk", "os.remove"]


def analyze_file(filepath: str, yara_rules_path: str = _YARA_RULES_PATH) -> List[Dict]:
    findings = []

    if _YARA_AVAILABLE and os.path.exists(yara_rules_path):
        try:
            rules = yara.compile(yara_rules_path)
            for match in rules.match(filepath):
                findings.append({
                    "file": filepath,
                    "reason": "yara_match",
                    "severity": "CRITICAL",
                    "detail": f"YARA rule matched: {match.rule}",
                })
        except Exception:
            pass

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()
    except (IOError, PermissionError):
        return findings

    for s in _CRITICAL_STRINGS:
        if s in content:
            findings.append({
                "file": filepath,
                "reason": "dangerous_strings",
                "severity": "CRITICAL",
                "detail": f"Dangerous string found: '{s}'",
            })
            break

    if all(token in content for token in _SUSPICIOUS_COMBO):
        findings.append({
            "file": filepath,
            "reason": "suspicious_import_combo",
            "severity": "MEDIUM",
            "detail": "Combination of cryptography + os.walk + os.remove detected",
        })

    return findings


def report(findings: List[Dict]):
    if not findings:
        print("[STATIC ANALYZER] \033[32m✓ No threats detected. Safe to run.\033[0m")
        return
    print(f"\n[STATIC ANALYZER] \033[31m⚠ {len(findings)} threat(s) detected:\033[0m\n")
    for i, f in enumerate(findings, 1):
        color = "\033[31m" if f["severity"] == "CRITICAL" else "\033[33m"
        print(f"  [{i}] {color}{f['severity']}\033[0m | {f['reason']}")
        print(f"       File: {f['file']}")
        print(f"       Detail: {f['detail']}\n")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "attacker/fake_installer.py"
    findings = analyze_file(target)
    report(findings)
    sys.exit(1 if any(f["severity"] == "CRITICAL" for f in findings) else 0)
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
cd social-engineering
python3 -m pytest tests/test_static_analyzer.py -v
```

Expected:
```
PASSED tests/test_static_analyzer.py::test_detect_yara_match
PASSED tests/test_static_analyzer.py::test_detect_fernet_dangerous_strings
PASSED tests/test_static_analyzer.py::test_clean_file_no_false_positive
```

- [ ] **Step 5: Commit**

```bash
git add social-engineering/defender/static_analyzer.py social-engineering/tests/test_static_analyzer.py
git commit -m "feat: static_analyzer with YARA + string scan, 3 tests passing"
```

---

## Task 5: behavior_monitor.py (TDD)

**Files:**
- Create: `social-engineering/tests/test_behavior_monitor.py`
- Create: `social-engineering/defender/behavior_monitor.py`

- [ ] **Step 1: Write failing tests**

`social-engineering/tests/test_behavior_monitor.py`:
```python
import os
import sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from defender.behavior_monitor import BehaviorMonitor


def test_detect_new_encrypted_file(tmp_path):
    """BehaviorMonitor.check_threats detects new .encrypted file in snapshot diff."""
    (tmp_path / "data.txt").write_text("important data")
    monitor = BehaviorMonitor(watch_dir=str(tmp_path))
    before = monitor.take_snapshot()

    (tmp_path / "data.txt.encrypted").write_bytes(b"encryptedcontent")

    after = monitor.take_snapshot()
    threats = monitor.check_threats(before, after)
    assert any(t["reason"] == "new_encrypted_file" for t in threats)
    assert any(t["severity"] == "CRITICAL" for t in threats)


def test_detect_original_file_deleted(tmp_path):
    """BehaviorMonitor.check_threats detects original file deletion in snapshot diff."""
    f = tmp_path / "report.csv"
    f.write_text("col1,col2\n1,2")
    monitor = BehaviorMonitor(watch_dir=str(tmp_path))
    before = monitor.take_snapshot()

    f.unlink()

    after = monitor.take_snapshot()
    threats = monitor.check_threats(before, after)
    assert any(t["reason"] == "file_deleted" for t in threats)
    assert any(t["severity"] == "HIGH" for t in threats)
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd social-engineering
python3 -m pytest tests/test_behavior_monitor.py -v
```

Expected: `ModuleNotFoundError: No module named 'defender.behavior_monitor'`

- [ ] **Step 3: Implement behavior_monitor.py**

`social-engineering/defender/behavior_monitor.py`:
```python
import os
import sys
import time
import subprocess
from typing import Dict, List

_base = os.path.dirname(os.path.abspath(__file__))
_PREVENTION_HTML = os.path.abspath(os.path.join(_base, '..', 'prevention_success.html'))
_DEFAULT_INSTALLER = os.path.abspath(os.path.join(_base, '..', 'attacker', 'fake_installer.py'))
_DEFAULT_SANDBOX = os.path.abspath(os.path.join(_base, '..', 'attacker', 'victim_sandbox'))


class BehaviorMonitor:
    def __init__(self, watch_dir: str):
        self.watch_dir = watch_dir

    def take_snapshot(self) -> Dict[str, int]:
        snapshot = {}
        for root, _, files in os.walk(self.watch_dir):
            for name in files:
                if name == ".ransom_key":
                    continue
                path = os.path.join(root, name)
                try:
                    snapshot[path] = os.path.getsize(path)
                except OSError:
                    pass
        return snapshot

    def check_threats(self, before: Dict[str, int], after: Dict[str, int]) -> List[Dict]:
        threats = []
        for path in after:
            if path not in before and path.endswith(".encrypted"):
                threats.append({
                    "file": path,
                    "reason": "new_encrypted_file",
                    "severity": "CRITICAL",
                    "detail": "Encrypted file appeared after process started",
                })
        for path in before:
            if path not in after:
                threats.append({
                    "file": path,
                    "reason": "file_deleted",
                    "severity": "HIGH",
                    "detail": "Original file deleted by running process",
                })
        return threats

    def monitor(self, installer_script: str, poll_interval: float = 0.5) -> List[Dict]:
        before = self.take_snapshot()
        proc = subprocess.Popen(
            [sys.executable, installer_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        threats = []
        while proc.poll() is None:
            time.sleep(poll_interval)
            after = self.take_snapshot()
            threats = self.check_threats(before, after)
            if threats:
                proc.kill()
                proc.wait()
                break
        if not threats:
            after = self.take_snapshot()
            threats = self.check_threats(before, after)
        return threats


def report(threats: List[Dict]):
    if not threats:
        print("[BEHAVIOR MONITOR] \033[32m✓ No suspicious activity detected.\033[0m")
        return
    print(f"\n[BEHAVIOR MONITOR] \033[31m⚠ {len(threats)} threat(s) detected — process killed:\033[0m\n")
    for i, t in enumerate(threats, 1):
        color = "\033[31m" if t["severity"] == "CRITICAL" else "\033[33m"
        print(f"  [{i}] {color}{t['severity']}\033[0m | {t['reason']}")
        print(f"       File: {t['file']}")
        print(f"       Detail: {t['detail']}\n")


if __name__ == "__main__":
    installer = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_INSTALLER
    watch_dir = sys.argv[2] if len(sys.argv) > 2 else _DEFAULT_SANDBOX
    monitor = BehaviorMonitor(watch_dir=watch_dir)
    threats = monitor.monitor(installer_script=installer)
    report(threats)
    if threats:
        subprocess.Popen(
            ['xdg-open', _PREVENTION_HTML],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        sys.exit(1)
    sys.exit(0)
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
cd social-engineering
python3 -m pytest tests/test_behavior_monitor.py -v
```

Expected:
```
PASSED tests/test_behavior_monitor.py::test_detect_new_encrypted_file
PASSED tests/test_behavior_monitor.py::test_detect_original_file_deleted
```

- [ ] **Step 5: Run full test suite**

```bash
cd ransomware-demo && python3 -m pytest tests/ -v
cd ../social-engineering && python3 -m pytest tests/ -v
```

Expected: 10 passed (ransomware-demo) + 5 passed (social-engineering) = **15 total**.

- [ ] **Step 6: Commit**

```bash
git add social-engineering/defender/behavior_monitor.py social-engineering/tests/test_behavior_monitor.py
git commit -m "feat: behavior_monitor with filesystem snapshot polling, 2 tests passing"
```

---

## Task 6: prevention_success.html

**Files:**
- Create: `social-engineering/prevention_success.html`

- [ ] **Step 1: Create prevention_success.html**

`social-engineering/prevention_success.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Threat Blocked — Defender Success</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f0faf4; color: #1a2e1a; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
    .card { background: #fff; border: 2px solid #28a745; border-radius: 16px; padding: 48px 40px; max-width: 600px; width: 100%; text-align: center; box-shadow: 0 0 40px rgba(40,167,69,0.12); }
    .shield { font-size: 5rem; margin-bottom: 16px; }
    h1 { font-size: 2rem; font-weight: 700; color: #155724; margin-bottom: 8px; }
    .subtitle { color: #6e6e80; margin-bottom: 28px; line-height: 1.5; }
    .timeline { display: flex; justify-content: center; margin-bottom: 28px; }
    .tl-step { text-align: center; padding: 0 20px; position: relative; }
    .tl-step:not(:last-child)::after { content: '→'; position: absolute; right: -8px; top: 10px; color: #adb5bd; }
    .tl-dot { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; margin: 0 auto 6px; }
    .tl-label { font-size: 0.72rem; color: #6e6e80; }
    .threats { text-align: left; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; margin-bottom: 24px; }
    .threats h3 { font-size: 0.85rem; font-weight: 600; text-transform: uppercase; color: #6e6e80; margin-bottom: 12px; letter-spacing: 0.06em; }
    .threat-item { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 10px; }
    .sev { font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; white-space: nowrap; margin-top: 2px; }
    .critical { background: #f8d7da; color: #721c24; }
    .high { background: #fff3cd; color: #856404; }
    .threat-detail { font-size: 0.875rem; color: #495057; }
    .actions { display: flex; gap: 12px; justify-content: center; }
    .btn-primary { padding: 12px 24px; background: #28a745; color: #fff; border: none; border-radius: 8px; font-size: 0.95rem; font-weight: 600; cursor: pointer; }
    .btn-secondary { padding: 12px 24px; background: #fff; color: #6e6e80; border: 1.5px solid #dee2e6; border-radius: 8px; font-size: 0.95rem; cursor: pointer; }
    .edu-badge { position: fixed; bottom: 10px; right: 10px; background: #fff3cd; color: #856404; border: 1px solid #ffc107; padding: 6px 12px; font-size: 0.75rem; border-radius: 4px; }
  </style>
</head>
<body>
  <div class="card">
    <div class="shield">🛡️</div>
    <h1>Threat Blocked Successfully</h1>
    <p class="subtitle">The behavior monitor detected malicious filesystem activity<br>and terminated the process before data loss occurred.</p>

    <div class="timeline">
      <div class="tl-step">
        <div class="tl-dot" style="background:#e9ecef">📧</div>
        <div class="tl-label">Lure sent</div>
      </div>
      <div class="tl-step">
        <div class="tl-dot" style="background:#e9ecef">⬇️</div>
        <div class="tl-label">Downloaded</div>
      </div>
      <div class="tl-step">
        <div class="tl-dot" style="background:#f8d7da;color:#721c24">🚫</div>
        <div class="tl-label">Blocked</div>
      </div>
      <div class="tl-step">
        <div class="tl-dot" style="background:#d4edda;color:#155724">✅</div>
        <div class="tl-label">Files safe</div>
      </div>
    </div>

    <div class="threats">
      <h3>Threats Detected</h3>
      <div class="threat-item">
        <span class="sev critical">CRITICAL</span>
        <span class="threat-detail"><strong>new_encrypted_file</strong> — Encrypted file appeared after process started</span>
      </div>
      <div class="threat-item">
        <span class="sev high">HIGH</span>
        <span class="threat-detail"><strong>file_deleted</strong> — Original file deleted by running process</span>
      </div>
    </div>

    <div class="actions">
      <button class="btn-primary" onclick="alert('Run in terminal:\n\ncd social-engineering\nbash demo_social.sh --with-defender\n\n(The demo script auto-restores sandbox at the end)')">
        Restore Files
      </button>
      <button class="btn-secondary" onclick="window.close()">Close</button>
    </div>
  </div>
  <div class="edu-badge">⚠️ DEMO ONLY — Academic Environment</div>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add social-engineering/prevention_success.html
git commit -m "feat: prevention_success.html - threat blocked UI with attack timeline"
```

---

## Task 7: demo_social.sh

**Files:**
- Create: `social-engineering/demo_social.sh`

- [ ] **Step 1: Create demo_social.sh**

`social-engineering/demo_social.sh`:
```bash
#!/bin/bash
set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ATTACKER_DIR="$SCRIPT_DIR/attacker"
VICTIM_SANDBOX="$ATTACKER_DIR/victim_sandbox"
BACKUP_DIR="$SCRIPT_DIR/.backups"

open_browser() {
  xdg-open "$1" 2>/dev/null || open "$1" 2>/dev/null || echo "  Open manually: $1"
}

backup_sandbox() {
  mkdir -p "$BACKUP_DIR"
  python3 - <<PYEOF
import tarfile, datetime, os
ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
archive = os.path.join('$BACKUP_DIR', f'victim_sandbox_{ts}.tar.gz')
with tarfile.open(archive, 'w:gz') as tar:
    tar.add('$VICTIM_SANDBOX', arcname='victim_sandbox')
print(f'  Backup saved: {os.path.basename(archive)}')
PYEOF
}

restore_sandbox() {
  python3 - <<PYEOF
import tarfile, glob, os, shutil
backups = sorted(glob.glob(os.path.join('$BACKUP_DIR', 'victim_sandbox_*.tar.gz')))
if not backups:
    print('  No backup found — recreating files manually.')
    exit(0)
latest = backups[-1]
shutil.rmtree('$VICTIM_SANDBOX', ignore_errors=True)
os.makedirs('$VICTIM_SANDBOX', exist_ok=True)
parent = os.path.dirname('$VICTIM_SANDBOX')
with tarfile.open(latest, 'r:gz') as tar:
    tar.extractall(path=parent, filter='data')
print(f'  Restored from: {os.path.basename(latest)}')
PYEOF
}

# ─── Parse mode ───────────────────────────────────────────
MODE=""
for arg in "$@"; do
  case $arg in
    --attack-only)   MODE="attack" ;;
    --with-defender) MODE="defend" ;;
    --help)
      echo "Usage: bash demo_social.sh [--attack-only | --with-defender]"
      echo "  --attack-only    Full attack, no defense (files get encrypted)"
      echo "  --with-defender  Static + behavioral defense stops the attack"
      exit 0 ;;
  esac
done

if [ -z "$MODE" ]; then
  echo -e "${YELLOW}Select demo mode:${NC}"
  echo "  1) --attack-only    (no defense)"
  echo "  2) --with-defender  (static + behavioral defense)"
  read -rp "Enter 1 or 2: " choice
  [ "$choice" = "1" ] && MODE="attack" || MODE="defend"
fi

cd "$SCRIPT_DIR"

# ─────────────────────────────────────────────────────────
# ATTACK-ONLY
# ─────────────────────────────────────────────────────────
if [ "$MODE" = "attack" ]; then
  echo -e "\n${RED}========================================"
  echo "   SOCIAL ENGINEERING — ATTACK ONLY"
  echo -e "========================================${NC}\n"

  echo -e "${GREEN}[STEP 1/7] Backing up victim_sandbox...${NC}"
  backup_sandbox; echo ""

  echo -e "${RED}[STEP 2/7] Victim visits fake landing page${NC}"
  open_browser "$ATTACKER_DIR/fake_landing.html"
  read -rp "  [Press Enter after viewing landing page]"; echo ""

  echo -e "${RED}[STEP 3/7] Victim enters email → fake API key generator${NC}"
  open_browser "$ATTACKER_DIR/fake_key_generator.html"
  read -rp "  [Press Enter after viewing key generator]"; echo ""

  echo -e "${RED}[STEP 4/7] Victim runs fake_installer.py${NC}"
  python3 attacker/fake_installer.py; echo ""

  echo -e "${RED}[STEP 5/7] victim_sandbox AFTER attack:${NC}"
  ls -la "$VICTIM_SANDBOX/"; echo ""

  echo -e "${RED}[STEP 6/7] Ransom note (opened by installer — check browser)${NC}"
  read -rp "  [Press Enter to continue]"; echo ""

  echo -e "${GREEN}[STEP 7/7] Restoring victim_sandbox...${NC}"
  restore_sandbox; echo ""

  echo -e "${GREEN}========================================\n   ATTACK DEMO COMPLETE\n========================================${NC}"

# ─────────────────────────────────────────────────────────
# WITH-DEFENDER
# ─────────────────────────────────────────────────────────
elif [ "$MODE" = "defend" ]; then
  echo -e "\n${GREEN}========================================"
  echo "   SOCIAL ENGINEERING — WITH DEFENDER"
  echo -e "========================================${NC}\n"

  echo -e "${GREEN}[STEP 1/10] Backing up victim_sandbox...${NC}"
  backup_sandbox; echo ""

  echo -e "${BLUE}[STEP 2/10] Victim visits fake landing page${NC}"
  open_browser "$ATTACKER_DIR/fake_landing.html"
  read -rp "  [Press Enter after viewing landing page]"; echo ""

  echo -e "${BLUE}[STEP 3/10] Victim sees fake API key generator${NC}"
  open_browser "$ATTACKER_DIR/fake_key_generator.html"
  read -rp "  [Press Enter after viewing key generator]"; echo ""

  echo -e "${GREEN}[STEP 4/10] DEFENDER: Static analyzer scanning fake_installer.py...${NC}"
  python3 defender/static_analyzer.py attacker/fake_installer.py || true; echo ""

  echo -e "${RED}[STEP 5/10] ⚠ CRITICAL threats found — installer is DANGEROUS${NC}"
  read -rp "  Bypass to demo behavioral defense? (y/N): " bypass
  if [ "$bypass" != "y" ] && [ "$bypass" != "Y" ]; then
    echo -e "\n  ${GREEN}✓ Attack prevented at static analysis stage.${NC}"
    restore_sandbox
    exit 0
  fi; echo ""

  echo -e "${GREEN}[STEP 6/10] DEFENDER: Behavior monitor activated — watching victim_sandbox/${NC}"
  echo ""

  echo -e "${BLUE}[STEP 7/10] Running fake_installer.py under monitoring...${NC}"
  python3 defender/behavior_monitor.py attacker/fake_installer.py "$VICTIM_SANDBOX" || true; echo ""

  echo -e "${GREEN}[STEP 8/10] Process killed by behavior monitor${NC}"; echo ""

  echo -e "${GREEN}[STEP 9/10] Prevention success page${NC}"
  open_browser "$SCRIPT_DIR/prevention_success.html"
  read -rp "  [Press Enter to continue]"; echo ""

  echo -e "${GREEN}[STEP 10/10] Restoring victim_sandbox...${NC}"
  restore_sandbox; echo ""

  echo -e "${GREEN}========================================\n   DEFENDER DEMO COMPLETE\n========================================${NC}"
fi
```

- [ ] **Step 2: Smoke test**

```bash
cd social-engineering
chmod +x demo_social.sh
bash demo_social.sh --help
```

Expected:
```
Usage: bash demo_social.sh [--attack-only | --with-defender]
  --attack-only    Full attack, no defense (files get encrypted)
  --with-defender  Static + behavioral defense stops the attack
```

- [ ] **Step 3: Commit**

```bash
git add social-engineering/demo_social.sh
git commit -m "feat: demo_social.sh with --attack-only and --with-defender modes"
```

---

## Task 8: Final Integration Check

- [ ] **Step 1: Run all tests**

```bash
cd ransomware-demo
python3 -m pytest tests/ -v
```
Expected: **10 passed**.

```bash
cd ../social-engineering
python3 -m pytest tests/ -v
```
Expected: **5 passed**.

- [ ] **Step 2: Verify static_analyzer on real installer**

```bash
cd social-engineering
python3 defender/static_analyzer.py attacker/fake_installer.py
echo "Exit: $?"
```

Expected: prints CRITICAL findings, exits with code `1`.

- [ ] **Step 3: Verify victim_sandbox restore cycle**

```bash
cd social-engineering
python3 attacker/fake_installer.py
ls attacker/victim_sandbox/    # must show .encrypted files
python3 -c "
import sys, os
sys.path.insert(0, os.path.join('..', 'ransomware-demo'))
from attacker.ransomware_simulator import RansomwareSimulator
RansomwareSimulator(sandbox_dir='attacker/victim_sandbox').decrypt()
"
ls attacker/victim_sandbox/    # must show original 3 files
```

- [ ] **Step 4: Final commit**

```bash
git add .
git commit -m "chore: 15 tests passing, social-engineering demo complete"
```
