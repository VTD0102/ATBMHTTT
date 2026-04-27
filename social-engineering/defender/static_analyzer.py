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
        except Exception as e:
            print(f"[static_analyzer] YARA scan skipped: {e}", file=sys.stderr)

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
