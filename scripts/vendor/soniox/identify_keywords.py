import pandas as pd
import collections
import re
import os
import sys

# Enforce UTF-8 standard output to prevent GBK encoding issues on Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, "soniox_batch_riyadbank_records.csv")

df = pd.read_csv(csv_path)

# Drop NaN values in human_label
df = df.dropna(subset=["human_label"])

all_words = []
for idx, row in df.iterrows():
    label = str(row["human_label"])
    # clean punctuation
    label_clean = re.sub(r"[^\w\s]", " ", label)
    words = label_clean.split()
    all_words.extend(words)

word_counts = collections.Counter(all_words)

print("=== TOP 100 MOST FREQUENT WORDS IN HUMAN LABELS ===")
for word, count in word_counts.most_common(100):
    print(f"{word}: {count}")
