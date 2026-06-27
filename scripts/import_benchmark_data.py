import os
import shutil
import sys
import argparse
from pathlib import Path

# Dynamically add the backend directory to sys.path
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "realtimeasr-en-arabic"
sys.path.insert(0, str(BACKEND_DIR))

from backend.database import save_ground_truth

# The default destination directory inside the backend app
DEFAULT_DEST_DIR = BACKEND_DIR / "backend" / "benchmark_data"


def main():
    parser = argparse.ArgumentParser(
        description="Import benchmark audio and ground truth txt files into the system."
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Path to the source folder containing .wav and .txt files (e.g., /path/to/RiyadBank_filter)",
    )
    parser.add_argument(
        "--folder-name",
        required=False,
        help="Target folder name inside benchmark_data (e.g., RiyadBank_filter). Defaults to the source folder name.",
    )
    args = parser.parse_args()

    src_dir = Path(args.source)
    if not src_dir.exists() or not src_dir.is_dir():
        print(f"Error: Source directory does not exist or is not a folder: {src_dir}")
        sys.exit(1)

    folder_name = args.folder_name if args.folder_name else src_dir.name
    dest_dir = DEFAULT_DEST_DIR / folder_name

    dest_dir.mkdir(parents=True, exist_ok=True)
    wav_count = 0
    txt_count = 0

    print(f"Importing files from: {src_dir}")
    print(f"Target directory: {dest_dir}")

    for root, dirs, files in os.walk(src_dir):
        for filename in files:
            src_file = Path(root) / filename
            rel_path = src_file.relative_to(src_dir)
            dest_file = dest_dir / rel_path

            # The relative path to store in the DB (relative to benchmark_data)
            posix_path = rel_path.with_suffix(".wav").as_posix()
            db_rel_path = f"{folder_name}/{posix_path}"

            if filename.lower().endswith(".wav"):
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dest_file)
                wav_count += 1
            elif filename.lower().endswith(".txt"):
                try:
                    with open(src_file, "r", encoding="utf-8") as f:
                        text = f.read().strip()
                    save_ground_truth(db_rel_path, text)
                    txt_count += 1
                except Exception as e:
                    print(f"Error processing text file {src_file}: {e}")

    print("\nImport completed successfully!")
    print(f"Copied {wav_count} WAV files.")
    print(f"Saved {txt_count} ground truth annotations to database.")


if __name__ == "__main__":
    main()
