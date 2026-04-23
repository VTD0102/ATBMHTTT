import os
import sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from attacker.ransomware_simulator import RansomwareSimulator

def test_only_encrypts_sandbox(tmp_path):
    """Simulator MUST NOT touch files outside sandbox."""
    sim = RansomwareSimulator(sandbox_dir=str(tmp_path / "sandbox"))
    os.makedirs(tmp_path / "sandbox")
    (tmp_path / "sandbox" / "test.txt").write_text("hello")
    (tmp_path / "outside.txt").write_text("do not touch")

    sim.encrypt()

    assert (tmp_path / "outside.txt").read_text() == "do not touch"

def test_encrypt_then_decrypt(tmp_path):
    """Encrypt then decrypt must recover original content."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    original = "noi dung quan trong"
    (sandbox / "data.txt").write_text(original)

    sim = RansomwareSimulator(sandbox_dir=str(sandbox))
    sim.encrypt()

    encrypted_file = sandbox / "data.txt.encrypted"
    assert encrypted_file.exists()
    assert not (sandbox / "data.txt").exists()

    sim.decrypt()
    assert (sandbox / "data.txt").read_text() == original

def test_key_saved_to_file(tmp_path):
    """Key must be saved to a file after encryption."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    (sandbox / "x.txt").write_text("x")

    sim = RansomwareSimulator(sandbox_dir=str(sandbox))
    sim.encrypt()

    assert os.path.exists(sim.key_file)
