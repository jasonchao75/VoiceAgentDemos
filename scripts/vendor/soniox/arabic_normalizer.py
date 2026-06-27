import re
import sys
from typing import List

# Reconfigure standard output to use UTF-8 to prevent GBK encoding errors on Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Harakat / Diacritics
DIACRITICS_RE = re.compile(r"[\u064B-\u0652]")

# Indic Digits Mapping
INDIC_DIGITS_MAP = {
    "٠": "0",
    "١": "1",
    "٢": "2",
    "٣": "3",
    "٤": "4",
    "٥": "5",
    "٦": "6",
    "٧": "7",
    "٨": "8",
    "٩": "9",
}

# Arabic Number Words to Numeric Values
# Note: Keys are written in their NORMALIZED forms to match post-normalization words.
WORDS_TO_NUMS = {
    # Single digits
    "صفر": 0,
    "واحد": 1,
    "واحده": 1,
    "احد": 1,
    "احدا": 1,
    "وحدا": 1,
    "اثنين": 2,
    "اثنان": 2,
    "اثنتين": 2,
    "اثنتان": 2,
    "ثنتين": 2,
    "ثنتان": 2,
    "تنين": 2,
    "ثلاثه": 3,
    "ثلاث": 3,
    "اربعه": 4,
    "اربع": 4,
    "خمسه": 5,
    "خمس": 5,
    "سته": 6,
    "ست": 6,
    "سبعه": 7,
    "سبع": 7,
    "ثمانيه": 8,
    "ثماني": 8,
    "ثمان": 8,
    "تسعه": 9,
    "تسع": 9,
    "عشره": 10,
    "عشر": 10,
    # Tens
    "احد عشر": 11,
    "احدعش": 11,
    "احدعشر": 11,
    "اثني عشر": 12,
    "اثنا عشر": 12,
    "اثنى عشر": 12,
    "اتنا عشر": 12,
    "اتنى عشر": 12,
    "اثنعش": 12,
    "ثلاثه عشر": 13,
    "ثلاثه عش": 13,
    "ثلاثعش": 13,
    "اربعه عشر": 14,
    "اربعه عش": 14,
    "اربععش": 14,
    "خمسه عشر": 15,
    "خمسه عش": 15,
    "خمستعش": 15,
    "سته عشر": 16,
    "سته عش": 16,
    "ستعش": 16,
    "سبعه عشر": 17,
    "سبعه عش": 17,
    "سبعتعش": 17,
    "ثمانيه عشر": 18,
    "ثمانيه عش": 18,
    "ثمانتعش": 18,
    "تسعه عشر": 19,
    "تسعه عش": 19,
    "تسعتعش": 19,
    "عشرين": 20,
    "عشرون": 20,
    "ثلاثين": 30,
    "ثلاثون": 30,
    "اربعين": 40,
    "اربعون": 40,
    "خمسين": 50,
    "خمسون": 50,
    "ستين": 60,
    "ستون": 60,
    "سبعين": 70,
    "سبعون": 70,
    "ثمانين": 80,
    "ثمانون": 80,
    "تسعين": 90,
    "تسعون": 90,
    # Hundreds
    "مئه": 100,
    "مئة": 100,
    "مائه": 100,
    "مائة": 100,
    "ميه": 100,
    "مئتين": 200,
    "مئتان": 200,
    "مائتين": 200,
    "مائتان": 200,
    "ميتين": 200,
    "ثلاثمئه": 300,
    "ثلاثمائة": 300,
    "ثلاثمائه": 300,
    "ثلاثمئة": 300,
    "اربعمئه": 400,
    "اربعمائة": 400,
    "اربعمائه": 400,
    "اربعمئة": 400,
    "خمسمئه": 500,
    "خمسمائة": 500,
    "خمسمائه": 500,
    "خمسمئة": 500,
    "ستمئه": 600,
    "ستمائة": 600,
    "ستمائه": 600,
    "ستمئة": 600,
    "ستميه": 600,
    "سبعمئه": 700,
    "سبعمائة": 700,
    "سبعمائه": 700,
    "سبعمئة": 700,
    "ثمانمئه": 800,
    "ثمانمائة": 800,
    "ثمانمائه": 800,
    "ثمانمئة": 800,
    "تسعمئه": 900,
    "تسعمائة": 900,
    "تسعمائه": 900,
    "تسعمئة": 900,
}


def remove_diacritics(text: str) -> str:
    """Removes Arabic vocalization marks (harakat/diacritics)."""
    return DIACRITICS_RE.sub("", text)


def normalize_alif(text: str) -> str:
    """Normalizes various forms of Alif (أ, إ, آ, ٱ) to a plain Alif (ا)."""
    text = re.sub(r"[أإآٱ]", "ا", text)
    return text


def normalize_ya(text: str) -> str:
    """Normalizes word-final Alif Maqsura (ى) to Ya (ي)."""
    text = re.sub(r"ى(?=\s|$)", "ي", text)
    return text


def normalize_ta_marbuta(text: str) -> str:
    """Normalizes word-final Ta Marbuta (ة) to Ha (ه)."""
    text = re.sub(r"ة(?=\s|$)", "ه", text)
    return text


def normalize_digits(text: str) -> str:
    """Converts Eastern Arabic-Indic digits to standard Western digits."""
    for indic, west in INDIC_DIGITS_MAP.items():
        text = text.replace(indic, west)
    return text


def clean_symbols(text: str) -> str:
    """Removes special characters, separators, and excessive punctuation."""
    text = text.replace("|", " ").replace("-", " ")
    text = re.sub(r"[^\w\s\u0600-\u06FF]", "", text)
    return text


def parse_group_to_num(group: List[str]) -> str:
    """
    Parses a contiguous group of normalized Arabic number words into a single digit string.
    Supports digit-by-digit codes (e.g. 3-8-8) and full compound numbers (e.g. three hundred and thirteen).
    """
    vals = []
    for w in group:
        clean_w = w
        if w.startswith("و") and len(w) > 1:
            test_w = w[1:]
            if test_w in WORDS_TO_NUMS:
                clean_w = test_w
        vals.append(WORDS_TO_NUMS.get(clean_w, 0))

    # If all values in the group are single digits (0-9), concatenate them directly (typical for branch/ATM codes)
    if all(0 <= v <= 9 for v in vals):
        return "".join(str(v) for v in vals)

    # Otherwise, sum them up as a full compound number
    total = 0
    i = 0
    n = len(vals)
    while i < n:
        curr = vals[i]
        # Lookahead: if current is 1-9 and next is 10 (عشر), they form compound teen (e.g. 13)
        if i + 1 < n and 1 <= curr <= 9 and vals[i + 1] == 10:
            total += curr + 10
            i += 2
        else:
            total += curr
            i += 1

    return str(total)


def normalize_numbers_to_digits(text: str) -> str:
    """
    Detects contiguous sequences of Arabic number words in a sentence
    and replaces them with standard digit representations.
    """
    if not text:
        return ""
    words = text.split(" ")
    new_words = []

    i = 0
    n = len(words)
    while i < n:
        word = words[i]
        clean_w = word
        is_num = False
        if word in WORDS_TO_NUMS:
            is_num = True
        elif word.startswith("و") and len(word) > 1 and word[1:] in WORDS_TO_NUMS:
            clean_w = word[1:]
            is_num = True

        if is_num:
            group = [word]
            j = i + 1
            while j < n:
                next_word = words[j]
                next_is_num = False
                if next_word in WORDS_TO_NUMS:
                    next_is_num = True
                elif (
                    next_word.startswith("و")
                    and len(next_word) > 1
                    and next_word[1:] in WORDS_TO_NUMS
                ):
                    next_is_num = True

                if next_is_num:
                    group.append(next_word)
                    j += 1
                else:
                    break

            parsed_num = parse_group_to_num(group)
            new_words.append(parsed_num)
            i = j
        else:
            new_words.append(word)
            i += 1

    return " ".join(new_words)


def normalize_arabic_text(text: str) -> str:
    """Applies complete normalization pipeline including digit-to-text unification."""
    if not text:
        return ""
    text = text.strip()
    text = remove_diacritics(text)
    text = normalize_alif(text)
    text = normalize_ya(text)
    text = normalize_ta_marbuta(text)
    text = normalize_digits(text)
    text = clean_symbols(text)
    # Collapse multiple whitespaces
    text = re.sub(r"\s+", " ", text)
    # Apply number word to digit normalization
    text = normalize_numbers_to_digits(text.strip())
    # Collapse any whitespaces introduced by number normalization
    text = re.sub(r"\s+", " ", text)
    return text.strip()


if __name__ == "__main__":
    # Small self-test
    test_cases = [
        ("بَنْكُ الرِّيَاضِ", "بنك الرياض"),
        ("جامعة الملك فيصل | 388", "جامعه الملك فيصل 388"),
        ("مدرسة مكة", "مدرسه مكه"),
        ("على فرع ١٠٢", "علي فرع 102"),
        ("أنت القدس", "انت القدس"),
        # Number Word Normalization Tests
        ("احد سبعه سته", "176"),
        ("ثلاثمائه وثلاثه عشر", "313"),
        ("فرع ميتين وواحد", "فرع 201"),
        ("ثلاثه المنطقة المحايدة", "3 المنطقه المحايده"),
    ]
    print("Running Arabic Normalizer Self-Test with Number Word Normalization:")
    for inp, expected in test_cases:
        norm = normalize_arabic_text(inp)
        assert norm == expected, (
            f"Failed for '{inp}': Got '{norm}', Expected '{expected}'"
        )
        print(f"PASS: '{inp}' -> '{norm}'")
