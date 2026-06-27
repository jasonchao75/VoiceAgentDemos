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

# Comprehensive Dictionary of specific Saudi branch locations
location_keywords = [
    # Core branch names / cities / neighborhoods
    "العليا",
    "العلية",
    "مكة",
    "جدة",
    "جده",
    "الدمام",
    "الرياض",
    "الرصيفة",
    "قباء",
    "الرس",
    "الدوادمي",
    "المجمعة",
    "الزلفي",
    "بلجرشي",
    "الهفوف",
    "تاروت",
    "النعمان",
    "بريدة",
    "البساتين",
    "الفلاح",
    "الواحة",
    "الراكة",
    "صبيا",
    "نجران",
    "سبت",
    "العلاية",
    "الغاط",
    "السليل",
    "الباحة",
    "الشرفية",
    "الكندرة",
    "الملز",
    "البطحاء",
    "الشرائع",
    "الأرطاوية",
    "الارطاوية",
    "الطاوية",
    "برزان",
    "الخالدية",
    "البحيرة",
    "الريان",
    "البكيرية",
    "الخبرة",
    "الخبراء",
    "الحوية",
    "رابغ",
    "تربة",
    "المحجر",
    "المعابدة",
    "المعابد",
    "المعبدة",
    "العتيبية",
    "النماص",
    "أبو عريش",
    "عريش",
    "وادي الدواسر",
    "الدواسر",
    "الجبيل",
    "أرامكو",
    "العسكرية",
    "قرية",
    "العزيزية",
    "النخيل",
    "الحرمين",
    "الجلوية",
    "ينبع",
    "تبوك",
    "الثقبة",
    "العوالي",
    "الظهران",
    "طبرجل",
    "حائل",
    "حايل",
    "الخفجي",
    "بيشة",
    "تنورة",
    "المزروعة",
    "المزروعية",
    "شراع",
    "شراء",
    "حراء",
    "عبدالعزيز",
    "الجابرية",
    "عنيزة",
    "الخضراء",
    "برايد",
    "العناية",
    "العيون",
    "الربيع",
    "الملز",
    "مبيعات جدة",
    "تاروت",
    "السيح",
    "بريد",
    # Newly discovered geographic terms / branch locations from inspection
    "الفيصلية",
    "فيصلية",
    "فصلية",
    "ابن خلدون",
    "خلدون",
    "السليمانية",
    "سليمانية",
    "الخزامى",
    "خزامى",
    "خميس مشيط",
    "خميس",
    "مشيط",
    "النعيرية",
    "نعيرية",
    "الجسر",
    "المذنب",
    "مذنب",
    "أم الحمام",
    "الحمام",
    "الشهابية",
    "شهابية",
    "الحديثة",
    "الحديث",
    "الماجد",
    "الصفراء",
    "صفراء",
    "الندى",
    "ندى",
    "عرعر",
    "دومة الجندل",
    "دومة",
    "الجندل",
    "حالة عمار",
    "عمار",
    "حجر",
    "النجاة",
    "الدوحة",
    "دوحة",
    "سكاكا",
    "غرناطة",
    "أملج",
    "املج",
    "القدس",
    "قدس",
    "العلا",
    "علا",
    "سيهات",
    "خيبر",
    "المركبات",
    "مركبات",
    "سلوى",
    "صفوة",
    "الخبر",
    "خبر",
    "الجفر",
    "المسارحة",
    "مسارحة",
    "جازان",
    "الجردة",
    "جردة",
    "شرورة",
    "شروره",
    "الشريفة",
    "شريفة",
    "السوق التجاري",
    "جامعة الملك",
    "ابن",
    "الكلوية",
    "البارحة",
    "المنطقة المحايدة",
]

# Dictionary of Arabic numeric words (used to identify branch codes in text form)
number_keywords = [
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
    "تلتمية",
    "تلتمئة",
    "خمسمية",
]

# Words that indicate conversational filler or generic bank statements
conversational_indicators = [
    "تحوليني",
    "حولني",
    "ساعات",
    "العمل",
    "مبيعات",
    "سيلز",
    "خدمة",
    "أقرب",
    "مدير",
    "تيلر",
    "أوبريتر",
    "بلاغ",
    "سيئة",
    "الخدمة",
    "بطاقتي",
    "ضاعت",
    "مساعدة",
    "مرحبا",
    "أهلاً",
    "كيف",
    "اكتب",
    "صحيح",
]


def clean_arabic_text(text):
    if not isinstance(text, str):
        return ""
    # Remove punctuation and normalize spaces
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def classify_row_v6(row):
    audio_id = row["audio_id"]
    human_label = (
        str(row["human_label"]).strip() if pd.notna(row["human_label"]) else ""
    )
    cleaned = clean_arabic_text(human_label)

    # 1. Silence or Garbage
    if not human_label or human_label.lower() == "nan":
        return "silence_or_garbage", "Empty or NaN label"

    # Check if English noise/greetings
    if re.search(r"[a-zA-Z]{3,}", human_label) and not any(
        kw in human_label for kw in ["العليا", "الدمام", "مكة"]
    ):
        return "silence_or_garbage", "English text noise"

    # Extremely short single-word general utterances
    words = cleaned.split()
    if len(words) <= 1:
        # Check if it is a number or specific location keyword
        is_num = any(c.isdigit() for c in cleaned) or any(
            nw in cleaned for nw in number_keywords
        )
        is_loc = (
            any(loc in cleaned for loc in location_keywords) or "الرئيسي" in cleaned
        )
        if not (is_num or is_loc):
            return (
                "silence_or_garbage",
                f'Extremely short single-word noise: "{human_label}"',
            )

    # 2. Check for numeric digits or Arabic number keywords (using substring check on cleaned text to handle prefixes)
    has_digits = re.search(r"\d+", cleaned) is not None
    has_num_words = any(nw in cleaned for nw in number_keywords)
    is_code = has_digits or has_num_words

    # 3. Check for specific branch locations
    has_locations = any(loc in cleaned for loc in location_keywords)
    # Also if it explicitly mentions "الفرع الرئيسي" or "فرع رئيسي" or similar
    has_explicit_branch = "الرئيسي" in cleaned or "رئيسي" in cleaned
    is_name = has_locations or has_explicit_branch

    # 4. Final Categorization Decision Tree
    if is_code and is_name:
        # Contains both name and code (e.g. "300 | مول أرامكو" or "خمسمية وثمانية نجران")
        return (
            "branch_name_and_code",
            "Contains both branch location/name and code details",
        )
    elif is_code:
        # Let's verify it's not a general number in context of something else (like "3 months" or "100 dollars")
        if any(ci in words for ci in conversational_indicators) and len(words) > 4:
            return "conversational_noise", "Conversational query containing a number"
        return "branch_code", "Contains numeric or text branch code only"
    elif is_name:
        return "branch_name", "Contains specific branch name or location"
    else:
        # No branch name and no code detected
        return (
            "conversational_noise",
            "General conversational filler with no branch details",
        )


# Apply the refined classification
results = []
reasons = []
for idx, row in df.iterrows():
    cat, reason = classify_row_v6(row)
    results.append(cat)
    reasons.append(reason)

df["refined_category"] = results
df["refined_reason"] = reasons

print("\n=== REFINED CATEGORY DISTRIBUTION (V6) ===")
print(df["refined_category"].value_counts())
print("\n" + "=" * 50)

# Check some of the interesting changes
print("\n=== SAMPLES OF REFINED CATEGORIES ===")
for cat in [
    "branch_code",
    "branch_name",
    "branch_name_and_code",
    "conversational_noise",
    "silence_or_garbage",
]:
    print(
        f"\n--- Category: {cat} (Total: {len(df[df['refined_category'] == cat])}) ---"
    )
    samples = df[df["refined_category"] == cat].head(15)
    for idx, row in samples.iterrows():
        print(
            f"ID: {row['audio_id']} | Orig: {row['category']} | Human: {row['human_label']} | Reason: {row['refined_reason']}"
        )

df.to_csv(
    os.path.join(base_dir, "riyadbank_records_reclassified_v6.csv"),
    index=False,
    encoding="utf-8",
)
print("\nSaved refined records to: riyadbank_records_reclassified_v6.csv")
