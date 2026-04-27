import os
import sys
from cryptography.fernet import Fernet, InvalidToken


def decrypt_sandbox(sandbox_dir: str, key_file: str = None):
    if key_file is None:
        key_file = os.path.join(sandbox_dir, ".ransom_key")

    if not os.path.exists(key_file):
        print(f"[DECRYPTOR] Key file not found: {key_file}")
        sys.exit(1)

    with open(key_file, "rb") as f:
        key = f.read()

    fernet = Fernet(key)
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
