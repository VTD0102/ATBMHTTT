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
