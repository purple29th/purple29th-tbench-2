"""Verify the recovered key is accepted by the validator."""
import subprocess
from pathlib import Path

KEY = Path("/app/key.txt")
JAR = "/app/validator.jar"

def test_key_file_exists():
    assert KEY.exists(), "agent did not produce /app/key.txt"

def test_key_is_accepted():
    key = KEY.read_text().strip()
    assert key, "/app/key.txt is empty"
    proc = subprocess.run(
        ["java", "-jar", JAR, key],
        capture_output=True, text=True, timeout=60,
    )
    out = proc.stdout.strip()
    assert out == "ACCEPTED", f"validator did not accept the key; got: {out!r} stderr: {proc.stderr!r}"
