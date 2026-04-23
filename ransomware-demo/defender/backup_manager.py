import os
import sys
import tarfile
from datetime import datetime
from typing import List


class BackupManager:
    def __init__(self, source_dir: str, backup_dir: str):
        self.source_dir = source_dir
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)

    def backup(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"backup_{timestamp}.tar.gz"
        archive_path = os.path.join(self.backup_dir, archive_name)

        # Guarantee uniqueness when multiple backups happen within the same second
        counter = 1
        while os.path.exists(archive_path):
            archive_name = f"backup_{timestamp}_{counter}.tar.gz"
            archive_path = os.path.join(self.backup_dir, archive_name)
            counter += 1

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(self.source_dir, arcname=os.path.basename(self.source_dir))

        size_kb = os.path.getsize(archive_path) / 1024
        print(f"[BACKUP] Created: {archive_name} ({size_kb:.1f} KB)")
        return archive_path

    def restore(self, backup_path: str, restore_dir: str):
        os.makedirs(restore_dir, exist_ok=True)
        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(path=restore_dir)

        extracted_subdir = os.path.join(restore_dir, os.path.basename(self.source_dir))
        if os.path.isdir(extracted_subdir):
            for item in os.listdir(extracted_subdir):
                src = os.path.join(extracted_subdir, item)
                dst = os.path.join(restore_dir, item)
                os.rename(src, dst)
            os.rmdir(extracted_subdir)

        print(f"[BACKUP] Restored from: {os.path.basename(backup_path)}")

    def list_backups(self) -> List[str]:
        return sorted([
            os.path.join(self.backup_dir, f)
            for f in os.listdir(self.backup_dir)
            if f.startswith("backup_") and f.endswith(".tar.gz")
        ])


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "backup"
    sandbox = os.path.join(os.path.dirname(__file__), '..', 'attacker', 'sandbox')
    backup_dir = os.path.join(os.path.dirname(__file__), '..', 'backups')

    mgr = BackupManager(source_dir=sandbox, backup_dir=backup_dir)

    if action == "list":
        backups = mgr.list_backups()
        print(f"[BACKUP] {len(backups)} backup(s):")
        for b in backups:
            print(f"  - {os.path.basename(b)}")
    elif action == "restore" and len(sys.argv) > 2:
        mgr.restore(backup_path=sys.argv[2], restore_dir=sandbox)
    else:
        mgr.backup()
