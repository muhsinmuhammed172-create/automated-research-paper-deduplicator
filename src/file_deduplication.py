
import hashlib
import json
from pathlib import Path

HASH_DATABASE = Path("output/processed_files.json")


def calculate_file_hash(file_path):
    """Calculate the SHA-256 hash of a file."""
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def load_processed_files():
    """Load previously recorded file hashes."""
    if HASH_DATABASE.exists():
        with open(HASH_DATABASE, "r", encoding="utf-8") as file:
            return json.load(file)

    return {}


def check_and_register_file(file_path):
    """Check whether a file was processed before."""
    file_path = Path(file_path)

    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_hash = calculate_file_hash(file_path)
    processed = load_processed_files()

    if file_hash in processed:
        print(f"Duplicate file: {file_path}")
        print(f"Previously processed as: {processed[file_hash]}")
        return False

    HASH_DATABASE.parent.mkdir(parents=True, exist_ok=True)
    processed[file_hash] = str(file_path)

    with open(HASH_DATABASE, "w", encoding="utf-8") as file:
        json.dump(processed, file, indent=4)

    print(f"New file registered: {file_path}")
    print(f"SHA-256: {file_hash}")
    return True
