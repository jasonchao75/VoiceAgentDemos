import os
import sys
import shutil
import pandas as pd
import logging

# Enforce UTF-8 standard output to prevent GBK encoding issues on Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Paths
base_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(base_dir, "../../../"))
csv_path = os.path.join(base_dir, "riyadbank_records_reclassified_v6.csv")

source_dir = os.path.join(root_dir, "benchmarks/arabic_audio/RiyadBank")
target_dir = os.path.join(root_dir, "benchmarks/arabic_audio/RiyadBank_filter")

# Setup simple logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def scan_wav_files(directory: str) -> dict:
    """Recursively scans directory for wav files and returns a map of filename (without ext) -> abs_path."""
    wav_map = {}
    for root, _, files in os.walk(directory):
        for f in files:
            if f.lower().endswith(".wav"):
                name_without_ext = os.path.splitext(f)[0]
                wav_map[name_without_ext] = os.path.join(root, f)
    return wav_map


def main():
    logging.info("Starting RiyadBank dataset re-organization and filtering...")

    # 1. Scan source directory for wav files
    local_wavs = scan_wav_files(source_dir)
    logging.info(f"Scanned source directory. Found {len(local_wavs)} .wav files.")

    # 2. Load the reclassified records
    if not os.path.exists(csv_path):
        logging.error(f"Reclassified records CSV not found at: {csv_path}")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    logging.info(f"Loaded {len(df)} records from {os.path.basename(csv_path)}.")

    # 3. Create target directory structure
    categories = ["branch_code", "branch_name", "branch_name_and_code"]
    for cat in categories:
        cat_dir = os.path.join(target_dir, cat)
        os.makedirs(cat_dir, exist_ok=True)
        logging.info(f"Ensured target folder exists: {cat_dir}")

    # 4. Copy files and write txt transcripts
    copied_count = 0
    missing_count = 0
    copied_records = []

    for idx, row in df.iterrows():
        audio_id = row["audio_id"]
        refined_cat = row["refined_category"]
        human_label = str(row["human_label"]) if pd.notna(row["human_label"]) else ""

        # We only process the 3 selected valid categories
        if refined_cat not in categories:
            continue

        # Find matching wav file
        if audio_id in local_wavs:
            src_wav_path = local_wavs[audio_id]
            dest_cat_dir = os.path.join(target_dir, refined_cat)

            # Destination file paths
            dest_wav_filename = f"{audio_id}.wav"
            dest_wav_path = os.path.join(dest_cat_dir, dest_wav_filename)
            dest_txt_filename = f"{audio_id}.txt"
            dest_txt_path = os.path.join(dest_cat_dir, dest_txt_filename)

            # Copy wav file
            shutil.copy2(src_wav_path, dest_wav_path)

            # Write txt transcript file (UTF-8)
            with open(dest_txt_path, "w", encoding="utf-8") as txt_file:
                txt_file.write(human_label)

            copied_count += 1

            # Collect for filtered metadata
            copied_records.append(
                {
                    "audio_id": audio_id,
                    "category": refined_cat,
                    "audio_file": f"{refined_cat}/{dest_wav_filename}",
                    "transcript_file": f"{refined_cat}/{dest_txt_filename}",
                    "human_label": human_label,
                    "asr_transcript": row.get("asr_transcript", ""),
                    "normalized_human": row.get("normalized_human", ""),
                    "normalized_asr": row.get("normalized_asr", ""),
                    "wer": row.get("wer", ""),
                    "status": row.get("status", ""),
                    "refined_reason": row.get("refined_reason", ""),
                }
            )
        else:
            logging.warning(
                f"Audio file for ID {audio_id} not found under source folder."
            )
            missing_count += 1

    logging.info(
        f"Copying complete. Successfully copied {copied_count} wav/txt pairs. Missing {missing_count} audios."
    )

    # 5. Generate metadata.csv in RiyadBank_filter folder
    if copied_records:
        metadata_df = pd.DataFrame(copied_records)
        metadata_output_path = os.path.join(target_dir, "metadata.csv")
        metadata_df.to_csv(metadata_output_path, index=False, encoding="utf-8")
        logging.info(f"Saved filtered metadata.csv to: {metadata_output_path}")

        # Verify counts per folder
        print("\n=== RiyadBank_filter Dataset Breakdown ===")
        print(metadata_df["category"].value_counts())
        print(f"Total files in folder: {len(metadata_df)} pairs of .wav and .txt\n")
    else:
        logging.warning("No records were copied. metadata.csv not generated.")


if __name__ == "__main__":
    main()
