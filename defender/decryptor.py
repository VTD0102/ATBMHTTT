import os
import sys
import base64
from cryptography.fernet import Fernet, InvalidToken

DEMO_HEADER = b"ATBMHTTT_DEMO_ENCRYPTED_V1\n"
DEMO_ORIGINAL_EXT = ".demo_original"


def decrypt_sandbox(sandbox_dir: str, key_file: str = None):
    if key_file is None:
        key_file = os.path.join(sandbox_dir, ".ransom_key")

    key = None
    fernet = None
    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            key = f.read()
    count = 0
    errors = 0

    for root, _, files in os.walk(sandbox_dir):
        for filename in files:
            if not filename.endswith(".encrypted"):
                continue
            enc_path = os.path.join(root, filename)
            original_path = enc_path[:-len(".encrypted")]

            try:
                with open(enc_path, "rb") as f:
                    encrypted_data = f.read()
                if encrypted_data.startswith(DEMO_HEADER):
                    backup_path = original_path + DEMO_ORIGINAL_EXT
                    if os.path.exists(backup_path):
                        os.replace(backup_path, original_path)
                        os.remove(enc_path)
                        print(f"[DECRYPTOR] Restored: {os.path.basename(original_path)}")
                        count += 1
                        continue
                    data = base64.b64decode(encrypted_data[len(DEMO_HEADER):])
                else:
                    if key is None:
                        print(f"[DECRYPTOR] Key file not found: {key_file}")
                        errors += 1
                        continue
                    if fernet is None:
                        fernet = Fernet(key)
                    data = fernet.decrypt(encrypted_data)
                with open(original_path, "wb") as f:
                    f.write(data)
                os.remove(enc_path)
                print(f"[DECRYPTOR] Restored: {os.path.basename(original_path)}")
                count += 1
            except InvalidToken:
                print(f"[DECRYPTOR] Wrong key or corrupted file: {filename}")
                errors += 1

    print(f"\n[DECRYPTOR] Result: {count} files restored, {errors} errors.")


if __name__ == "__main__":
    sandbox = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), '..', 'shop_data'
    )
    decrypt_sandbox(sandbox_dir=sandbox)
