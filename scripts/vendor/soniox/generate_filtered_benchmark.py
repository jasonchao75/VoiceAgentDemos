import pandas as pd
import os
import sys

# Enforce UTF-8 standard output to prevent GBK encoding issues on Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

base_dir = os.path.dirname(os.path.abspath(__file__))
reclassified_csv_path = os.path.join(base_dir, "riyadbank_records_reclassified_v6.csv")
root_dir = os.path.abspath(os.path.join(base_dir, "../../../"))
output_benchmark_csv_path = os.path.join(
    root_dir, "benchmarks/arabic_audio/RiyadBank/filtered_riyadbank_benchmark.csv"
)

# Load reclassified records
df = pd.read_csv(reclassified_csv_path)

# Filter for valid evaluation categories
valid_categories = ["branch_code", "branch_name", "branch_name_and_code"]
df_filtered = df[df["refined_category"].isin(valid_categories)].copy()

# Update the 'category' column to our high-precision refined category
df_filtered["category"] = df_filtered["refined_category"]

# Select original columns for compatibility + our classification reason
columns_to_keep = [
    "audio_id",
    "category",
    "human_label",
    "asr_transcript",
    "normalized_human",
    "normalized_asr",
    "wer",
    "sub",
    "del",
    "ins",
    "ref_word_count",
    "status",
    "error_message",
    "refined_reason",
]
df_filtered = df_filtered[columns_to_keep]

# Save to destination
os.makedirs(os.path.dirname(output_benchmark_csv_path), exist_ok=True)
df_filtered.to_csv(output_benchmark_csv_path, index=False, encoding="utf-8")

print(f"=== BENCHMARK FILTERING COMPLETE ===")
print(f"Original total records: {len(df)}")
print(f"Filtered valid records: {len(df_filtered)} ({len(df_filtered) / len(df):.1%})")
print(f"Excluded records:       {len(df) - len(df_filtered)}")
print("\nFiltered Category Breakdown:")
print(df_filtered["category"].value_counts())
print(
    f"\nSuccessfully generated and saved filtered benchmark metadata to:\n{output_benchmark_csv_path}"
)
