import os
import sys
import time
import subprocess
from typing import Dict, List

_base = os.path.dirname(os.path.abspath(__file__))
_PREVENTION_HTML = os.path.abspath(os.path.join(_base, '..', 'social-engineering', 'prevention_success.html'))
_DEFAULT_INSTALLER = os.path.abspath(os.path.join(_base, '..', 'manager-agent', 'fake_installer.py'))
_DEFAULT_SANDBOX = os.path.abspath(os.path.join(_base, '..', 'shop_data'))


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
