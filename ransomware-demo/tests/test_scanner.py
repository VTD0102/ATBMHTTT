import os
import sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from defender.scanner import RansomwareScanner

def make_high_entropy_file(path):
    data = os.urandom(1024)
    with open(path, 'wb') as f:
        f.write(data)

def make_low_entropy_file(path, content="hello world this is plain text " * 20):
    with open(path, 'w') as f:
        f.write(content)

def test_detect_encrypted_extension(tmp_path):
    """File .encrypted must be flagged."""
    f = tmp_path / "data.txt.encrypted"
    f.write_bytes(b"some data")
    scanner = RansomwareScanner(scan_dir=str(tmp_path))
    results = scanner.scan()
    assert any(r["file"].endswith(".encrypted") for r in results)
    assert any(r["reason"] == "encrypted_extension" for r in results)

def test_detect_high_entropy(tmp_path):
    """File with entropy > 7.5 must be flagged."""
    f = tmp_path / "normal.txt"
    make_high_entropy_file(str(f))
    scanner = RansomwareScanner(scan_dir=str(tmp_path))
    results = scanner.scan()
    assert any(r["reason"] == "high_entropy" for r in results)

def test_no_false_positive_plain_text(tmp_path):
    """Plain text file must NOT be flagged for high entropy."""
    f = tmp_path / "readme.txt"
    make_low_entropy_file(str(f))
    scanner = RansomwareScanner(scan_dir=str(tmp_path))
    results = scanner.scan()
    entropy_flags = [r for r in results if r["reason"] == "high_entropy"]
    assert len(entropy_flags) == 0

def test_detect_simulator_signature(tmp_path):
    """File containing RANSOMWARE_SIMULATOR_DEMO_SAFE must be flagged."""
    f = tmp_path / "suspect.py"
    f.write_text('SIMULATOR_SIGNATURE = "RANSOMWARE_SIMULATOR_DEMO_SAFE"')
    scanner = RansomwareScanner(scan_dir=str(tmp_path))
    results = scanner.scan()
    assert any(r["reason"] == "simulator_signature" for r in results)
