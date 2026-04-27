import os
import sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from defender.static_analyzer import analyze_file
from attacker.fake_manager import trigger_encryption


def test_static_analyzer_detects_fake_manager():
    """static_analyzer flags fake_manager.py as CRITICAL (YARA + dangerous strings)."""
    fake_manager_path = os.path.join(os.path.dirname(__file__), '..', 'attacker', 'fake_manager.py')
    findings = analyze_file(fake_manager_path)
    critical = [f for f in findings if f['severity'] == 'CRITICAL']
    assert len(critical) >= 1


def test_fake_manager_encrypts_sandbox(tmp_path):
    """trigger_encryption() encrypts all files in the given directory."""
    (tmp_path / 'data.txt').write_text('sensitive data')
    (tmp_path / 'report.csv').write_text('col1,col2\nval1,val2')

    trigger_encryption(str(tmp_path))

    encrypted = list(tmp_path.glob('*.encrypted'))
    assert len(encrypted) == 2
    assert not (tmp_path / 'data.txt').exists()
    assert not (tmp_path / 'report.csv').exists()
