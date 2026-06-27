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
csv_path = os.path.join(base_dir, "soniox_batch_riyadbank_records.csv")

df = pd.read_csv(csv_path)

# Dictionary of Saudi branch / location keywords
branch_keywords = [
    r"العليا",
    r"مكة",
    r"جدة",
    r"الدمام",
    r"الرياض",
    r"الرصيفة",
    r"قباء",
    r"الرس",
    r"الدوادمي",
    r"المجمعة",
    r"الزلفي",
    r"بلجرشي",
    r"الهفوف",
    r"تاروت",
    r"النعمان",
    r"بريدة",
    r"البساتين",
    r"الفلاح",
    r"الواحة",
    r"الراكة",
    r"صبيا",
    r"نجران",
    r"سبت",
    r"العلاية",
    r"الغاط",
    r"السليل",
    r"الباحة",
    r"الشرفية",
    r"الكندرة",
    r"الملز",
    r"البطحاء",
    r"الشرائع",
    r"الأرطاوية",
    r"برزان",
    r"الخالدية",
    r"البحيرة",
    r"الريان",
    r"البكيرية",
    r"الخبرة",
    r"الخبراء",
    r"الحوية",
    r"رابغ",
    r"تربة",
    r"المحجر",
    r"المعابدة",
    r"المعابد",
    r"العتيبية",
    r"النماص",
    r"أبو عريش",
    r"عريش",
    r"وادي الدواسر",
    r"الدواسر",
    r"الجبيل",
    r"أرامكو",
    r"العسكرية",
    r"قرية",
    r"العزيزية",
    r"النخيل",
    r"الحرمين",
    r"الجلوية",
    r"ينبع",
    r"تبوك",
    r"الثقبة",
    r"العوالي",
    r"الظهران",
    r"طبرجل",
    r"حائل",
    r"حايل",
    r"الخفجي",
    r"بيشة",
    r"تنورة",
    r"المزروعة",
    r"المزروعية",
    r"شراع",
    r"شراء",
    r"حراء",
    r"عبدالعزيز",
    r"الجابرية",
    r"عنيزة",
    r"الخضراء",
    r"برايد",
    r"العناية",
    r"العيون",
    r"الربيع",
    r"الملز",
    r"مبيعات جدة",
    r"تاروت",
]

# Dictionary of Arabic numeric words
number_words = [
    r"واحد",
    r"اثنين",
    r"ثلاثة",
    r"اربعة",
    r"خمسة",
    r"ستة",
    r"سبعة",
    r"ثمانية",
    r"تسعة",
    r"عشرة",
    r"عشر",
    r"عشرين",
    r"ثلاثين",
    r"اربعين",
    r"خمسين",
    r"ستين",
    r"سبعين",
    r"ثمانين",
    r"تسعين",
    r"مئة",
    r"مائة",
    r"ميتين",
    r"مائتان",
    r"ثلاثمئة",
    r"ثلاثمائة",
    r"اربعمئة",
    r"اربعمائة",
    r"خمسمئة",
    r"خمسمائة",
    r"ستمئة",
    r"ستمائة",
    r"سبعمئة",
    r"سبعمائة",
    r"ثمانمئة",
    r"ثمانمائة",
    r"تسعمئة",
    r"تسعمائة",
    r"ألف",
]

# Specific exclusion list for conversational phrases (fully matched or highly conversational)
conversational_phrases = [
    r"أنا عميل ماسي",
    r"أنا عميلة ماسية",
    r"أنا عميل",
    r"أنا عميلة",
    r"ايه حوليني",
    r"اي حوليني",
    r"حوليني",
    r"حولني",
    r"يه صحيح صحيح",
    r"صحيح صحيح",
    r"اي قلت لك صحيح",
    r"قلت لك صحيح",
    r"صحيح بس ايش اسم الفرع",
    r"أخوي ولا اختي",
    r"أبغا اتأكد من ساعات العمل",
    r"اتأكد من ساعات العمل",
    r"ساعات العمل",
    r"ممكن تحوليني على قسم المبيعات",
    r"قسم المبيعات",
    r"خدمة مبيعات",
    r"السيلز",
    r"أقرب فرع لي",
    r"الفرع القريب مني",
    r"أقرب فرع",
    r"أقرب فرع لي",
    r"ماعرف انتي المفروض تعرفين",
    r"ما اعرف",
    r"ماعرف",
    r"ما ادري",
    r"كم فرع عندكم",
    r"كم فرع",
    r"ابي فروع",
    r"ايش الفروع",
    r"ممكن تحوليني على مدير الفرع",
    r"مدير الفرع",
    r"تحولني على التيلر",
    r"التيلر",
    r"تحوليني على الأوبريتر",
    r"الأوبريتر",
    r"قسم المساعدة",
    r"خدمة العملاء",
    r"كيف اكتب لك",
    r"ودي أقدم بلاغ",
    r"الخدمة كانت سيئة",
    r"بلاغ",
    r"ما يهمك اسم الفرع",
    r"وش بيفرق",
    r"ما يهمني",
    r"معليش ممكن تعيدينهم",
    r"أنا أسأل",
    r"بنك الرياض",
    r"ممكن تخدميني",
]


def classify_row(row):
    audio_id = row["audio_id"]
    human_label = (
        str(row["human_label"]).strip() if pd.notna(row["human_label"]) else ""
    )
    original_category = row["category"]

    # 1. Silence or Garbage
    if not human_label or human_label.lower() == "nan":
        return "silence_or_garbage", "Empty or NaN label"

    # Check if label is English noise
    if re.search(r"[a-zA-Z]{3,}", human_label) and not any(
        kw in human_label for kw in ["العليا", "الدمام", "مكة"]
    ):
        # If it has long English words and is not Arabic branch name
        return "silence_or_garbage", "English noise/greetings"

    # Check if too short or just greetings/garbage
    if human_label in ["أنا", "أهلًا", "عربي", "لا", "نعم", "صحيح", "أعرب"]:
        return "silence_or_garbage", "Extremely short greeting or single filler word"

    # 2. Conversational Noise
    # Check if matches any core conversational phrases
    for phrase in conversational_phrases:
        if phrase in human_label:
            # Let's double check if it also contains a branch code or specific branch name
            has_num = re.search(r"\d+", human_label) is not None
            has_num_word = any(
                re.search(rf"\b{nw}\b", human_label) for nw in number_words
            )
            has_branch = any(
                re.search(rf"\b{kw}\b", human_label) for kw in branch_keywords
            )

            # If it has a branch name or code, we might want to keep it if it is an evaluation candidate,
            # but if it's mostly filler like "طيب بتحوليني على اي فرع" (which has 'فرع' but no specific branch name/code),
            # or "أنا عند فرع جده الرئيسي وأبي اتكلم مع المدير" (which actually has 'جده' - so it has branch name!)
            if (has_num or has_num_word) and has_branch:
                return (
                    "branch_name_and_code",
                    "Contains branch name, code, and conversational context",
                )
            elif has_branch:
                # If it mentions a specific branch name like "جده" or "الرياض", keep it as branch_name
                # Let's make sure it's not a generic word like "فرع" only
                # "طيب بتحوليني على اي فرع" doesn't have a specific location, so let's check which keyword matched
                matched_kws = [
                    kw for kw in branch_keywords if re.search(rf"\b{kw}\b", human_label)
                ]
                if matched_kws:
                    return (
                        "branch_name",
                        f"Contains specific branch name: {matched_kws}",
                    )

            return "conversational_noise", f"Matches conversational phrase: {phrase}"

    # 3. Code and Name detection
    has_digits = re.search(r"\d+", human_label) is not None
    # Check for Arabic number words
    has_num_words = any(re.search(rf"\b{nw}\b", human_label) for nw in number_words)
    # Check for specific branch keywords
    has_branch_names = any(
        re.search(rf"\b{kw}\b", human_label) for kw in branch_keywords
    )

    is_code = has_digits or has_num_words
    is_name = has_branch_names or "فرع" in human_label or "الرئيسي" in human_label

    if is_code and is_name:
        return (
            "branch_name_and_code",
            "Contains both branch name/location and code details",
        )
    elif is_code:
        # Check if it has some non-branch text that might be conversational, but default is code
        return "branch_code", "Contains numeric or text branch code only"
    elif is_name:
        # Make sure it's not just the word "الفرع" or "فرع" without specific branch name or location context
        if human_label in ["فرع", "الفرع", "فرع ايش", "الفرع الرئيسي"]:
            if human_label == "الفرع الرئيسي":
                return "branch_name", "The main branch (general but standard entity)"
            return "conversational_noise", "Generic branch query"
        return "branch_name", "Contains specific branch name or location"
    else:
        # Default fallback
        return (
            "conversational_noise",
            "Fallback: no specific branch name or code detected",
        )


# Apply classification
results = []
reasons = []
for idx, row in df.iterrows():
    cat, reason = classify_row(row)
    results.append(cat)
    reasons.append(reason)

df["new_category"] = results
df["classification_reason"] = reasons

# Stats
print("\n=== NEW CATEGORY DISTRIBUTION ===")
print(df["new_category"].value_counts())
print("\n" + "=" * 50)

# Print examples for each new category
new_categories = df["new_category"].unique()
for cat in new_categories:
    print(
        f"\n--- Samples of NEW category: {cat} (Total: {len(df[df['new_category'] == cat])}) ---"
    )
    samples = df[df["new_category"] == cat].head(15)
    for idx, row in samples.iterrows():
        print(
            f"ID: {row['audio_id']} | Orig: {row['category']} | Human: {row['human_label']} | Reason: {row['classification_reason']}"
        )

# Save the updated CSV
output_path = os.path.join(base_dir, "riyadbank_records_reclassified.csv")
df.to_csv(output_path, index=False, encoding="utf-8")
print(f"\nSaved reclassified records to: {output_path}")
