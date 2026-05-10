import os
import sys
import tarfile
from datetime import datetime
from typing import List


class BackupManager:
    def __init__(self, source_dir: str, backup_dir: str, max_backups: int = 0):
        self.source_dir = source_dir
        self.backup_dir = backup_dir
        self.max_backups = max_backups  # 0 = unlimited
        os.makedirs(backup_dir, exist_ok=True)

    _SKIP_SUFFIXES = ('.encrypted', '.demo_original', '.ransom_key')

    def _should_include(self, path: str) -> bool:
        return not any(path.endswith(s) for s in self._SKIP_SUFFIXES)

    def backup(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"backup_{timestamp}.tar.gz"
        archive_path = os.path.join(self.backup_dir, archive_name)

        counter = 1
        while os.path.exists(archive_path):
            archive_name = f"backup_{timestamp}_{counter}.tar.gz"
            archive_path = os.path.join(self.backup_dir, archive_name)
            counter += 1

        with tarfile.open(archive_path, "w:gz") as tar:
            for root, dirs, files in os.walk(self.source_dir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    if self._should_include(fpath):
                        arcname = os.path.join(
                            os.path.basename(self.source_dir),
                            os.path.relpath(fpath, self.source_dir)
                        )
                        tar.add(fpath, arcname=arcname)

        size_kb = os.path.getsize(archive_path) / 1024
        print(f"[BACKUP] Created: {archive_name} ({size_kb:.1f} KB)")

        if self.max_backups > 0:
            self._prune()

        return archive_path

    def _prune(self):
        backups = self.list_backups()
        for old in backups[:-self.max_backups]:
            try:
                os.remove(old)
                print(f"[BACKUP] Pruned: {os.path.basename(old)}")
            except OSError:
                pass

    def _clean_infected(self, directory: str):
        """Xóa file mã hóa + ransom key trong một thư mục."""
        for fname in os.listdir(directory):
            if any(fname.endswith(s) for s in ('.encrypted', '.ransom_key')):
                try:
                    os.remove(os.path.join(directory, fname))
                except OSError:
                    pass

    def restore(self, backup_path: str, restore_dir: str):
        os.makedirs(restore_dir, exist_ok=True)

        self._clean_infected(restore_dir)

        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(path=restore_dir, filter='data')

        extracted_subdir = os.path.join(restore_dir, os.path.basename(self.source_dir))
        if os.path.isdir(extracted_subdir):
            # Xóa file mã hóa bên trong subdir trước khi move lên
            self._clean_infected(extracted_subdir)
            for item in os.listdir(extracted_subdir):
                src = os.path.join(extracted_subdir, item)
                dst = os.path.join(restore_dir, item)
                if os.path.exists(dst):
                    os.remove(dst)
                os.rename(src, dst)
            os.rmdir(extracted_subdir)

        # Pass cuối: xóa bất kỳ file mã hóa nào còn sót (có thể từ backup cũ)
        self._clean_infected(restore_dir)

        print(f"[BACKUP] Restored from: {os.path.basename(backup_path)}")

    def list_backups(self) -> List[str]:
        return sorted([
            os.path.join(self.backup_dir, f)
            for f in os.listdir(self.backup_dir)
            if f.startswith("backup_") and f.endswith(".tar.gz")
        ])


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "backup"
    sandbox = os.path.join(os.path.dirname(__file__), '..', 'shop_data')
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
