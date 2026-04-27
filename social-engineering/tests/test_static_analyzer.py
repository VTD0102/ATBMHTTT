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
