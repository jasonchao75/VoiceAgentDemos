import pandas as pd
import re
import os
import sys

# Enforce UTF-8 standard output to prevent GBK encoding issues on Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Paths
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, "soniox_batch_riyadbank_records.csv")

# Load data
df = pd.read_csv(csv_path)

print("=== ORIGINAL CATEGORY DISTRIBUTION ===")
print(df["category"].value_counts(dropna=False))
print("\n" + "=" * 50)

# Let's inspect some samples from each category to see what's going on
categories = df["category"].unique()
for cat in categories:
    print(
        f"\n--- Samples of category: {cat} (Total: {len(df[df['category'] == cat])}) ---"
    )
    samples = df[df["category"] == cat].head(25)
    for idx, row in samples.iterrows():
        human = str(row["human_label"])
        asr = str(row["asr_transcript"])
        print(
            f"ID: {row['audio_id']} | Human: {human} | ASR: {asr} | WER: {row['wer']}"
        )
