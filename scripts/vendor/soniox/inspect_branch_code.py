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

base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, "riyadbank_records_reclassified_v3.csv")

df = pd.read_csv(csv_path)

# Show all records in branch_code that have any letters that are not standard numbers
number_words_set = {
    "واحد",
    "اثنين",
    "ثلاثة",
    "ثلاث",
    "اربعة",
    "أربعة",
    "خمسة",
    "خمس",
    "ستة",
    "ست",
    "سبعة",
    "ثمانية",
    "تسعة",
    "عشرة",
    "عشر",
    "عشرين",
    "ثلاثين",
    "اربعين",
    "خمسين",
    "ستين",
    "سبعين",
    "ثمانين",
    "تسعين",
    "مية",
    "مئة",
    "مائة",
    "ميتين",
    "مائتان",
    "ثلاثمئة",
    "ثلاثمائة",
    "اربعمئة",
    "اربعمائة",
    "خمسمئة",
    "خمسمائة",
    "ستمئة",
    "ستمائة",
    "سبعمئة",
    "سبعمائة",
    "ثمانمئة",
    "ثمانمائة",
    "تسعمئة",
    "تسعمائة",
    "ألف",
    "لا",
    "فرع",
    "رع",
    "قصدي",
    "صفر",
    "سبت",
}

print("=== CHECKING BRANCH_CODE FOR UNRECOGNIZED GEOGRAPHIC TERMS ===")
code_df = df[df["refined_category"] == "branch_code"]
for idx, row in code_df.iterrows():
    human = str(row["human_label"])
    cleaned = re.sub(r"[^\w\s]", " ", human)
    words = cleaned.split()
    # Find words that are not digits and not in number_words_set
    non_num_words = []
    for w in words:
        if not w.isdigit() and w not in number_words_set:
            non_num_words.append(w)
    if non_num_words:
        print(
            f"ID: {row['audio_id']} | Human: {human} | Non-numeric words: {non_num_words}"
        )
