import os
import sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from defender.backup_manager import BackupManager

def test_backup_creates_archive(tmp_path):
    """Backup must create a .tar.gz file in backup_dir."""
    source = tmp_path / "data"
    source.mkdir()
    (source / "file.txt").write_text("important data")
    backup_dir = tmp_path / "backups"

    mgr = BackupManager(source_dir=str(source), backup_dir=str(backup_dir))
    backup_path = mgr.backup()

    assert os.path.exists(backup_path)
    assert backup_path.endswith(".tar.gz")

def test_restore_recovers_files(tmp_path):
    """Restore from backup must recover original content."""
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
    """list_backups must return all created backups."""
    source = tmp_path / "data"
    source.mkdir()
    (source / "x.txt").write_text("x")
    backup_dir = tmp_path / "backups"

    mgr = BackupManager(source_dir=str(source), backup_dir=str(backup_dir))
    mgr.backup()
    mgr.backup()

    backups = mgr.list_backups()
    assert len(backups) == 2
