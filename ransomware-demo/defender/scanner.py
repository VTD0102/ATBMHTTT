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
                "detail": f"Extension '{ext}' commonly used by ransomware"
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
                    "detail": f"Entropy = {entropy:.2f} (threshold: {ENTROPY_THRESHOLD})"
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
                    "detail": "Ransomware simulator signature detected"
                })
        except (IOError, PermissionError):
            pass

    def report(self):
        if not self.findings:
            print("[SCANNER] No threats detected.")
            return
        print(f"\n[SCANNER] {len(self.findings)} threat(s) found:\n")
        for i, f in enumerate(self.findings, 1):
            print(f"  [{i}] {f['severity']} | {f['reason']}")
            print(f"       File: {f['file']}")
            print(f"       Detail: {f['detail']}\n")


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    print(f"[SCANNER] Scanning: {target}")
    scanner = RansomwareScanner(scan_dir=target)
    scanner.scan()
    scanner.report()
