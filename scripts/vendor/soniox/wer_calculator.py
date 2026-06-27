import sys
from typing import Tuple, List

# Reconfigure standard output to use UTF-8 to prevent GBK encoding errors on Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def calculate_levenshtein_distance(
    ref_words: List[str], hyp_words: List[str]
) -> Tuple[int, int, int, int]:
    """
    Computes Levenshtein distance on word lists.
    Returns: (substitutions, deletions, insertions, edit_distance)
    """
    n_ref = len(ref_words)
    n_hyp = len(hyp_words)

    # DP matrix of dimensions (n_ref + 1) x (n_hyp + 1)
    # Each cell stores (distance, substitutions, deletions, insertions)
    dp = [[(0, 0, 0, 0) for _ in range(n_hyp + 1)] for _ in range(n_ref + 1)]

    # Initialize base cases
    for i in range(1, n_ref + 1):
        dp[i][0] = (i, 0, i, 0)  # deletions only
    for j in range(1, n_hyp + 1):
        dp[0][j] = (j, 0, 0, j)  # insertions only

    for i in range(1, n_ref + 1):
        for j in range(1, n_hyp + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                # 1. Substitution
                sub_dist, sub_s, sub_d, sub_i = dp[i - 1][j - 1]
                sub_candidate = (sub_dist + 1, sub_s + 1, sub_d, sub_i)

                # 2. Deletion
                del_dist, del_s, del_d, del_i = dp[i - 1][j]
                del_candidate = (del_dist + 1, del_s, del_d + 1, del_i)

                # 3. Insertion
                ins_dist, ins_s, ins_d, ins_i = dp[i][j - 1]
                ins_candidate = (ins_dist + 1, ins_s, ins_d, ins_i + 1)

                # Pick the operation that minimizes distance
                best = min(
                    sub_candidate, del_candidate, ins_candidate, key=lambda x: x[0]
                )
                dp[i][j] = best

    dist, s, d, i = dp[n_ref][n_hyp]
    return s, d, i, dist


def calculate_wer(ref_text: str, hyp_text: str) -> Tuple[float, int, int, int, int]:
    """
    Computes Word Error Rate between normalized reference and hypothesis texts.
    Returns: (wer_float, substitutions, deletions, insertions, ref_word_count)
    """
    ref_words = [w for w in ref_text.split(" ") if w]
    hyp_words = [w for w in hyp_text.split(" ") if w]

    n_ref = len(ref_words)
    if n_ref == 0:
        if len(hyp_words) == 0:
            return 0.0, 0, 0, 0, 0
        else:
            # All words in hypothesis are insertions
            return 1.0, 0, 0, len(hyp_words), 0

    s, d, i, dist = calculate_levenshtein_distance(ref_words, hyp_words)
    wer = float(dist) / n_ref
    return wer, s, d, i, n_ref


if __name__ == "__main__":
    # Small self-test
    test_cases = [
        ("احد سبعه سته", "احد 7 سته", 1, 0, 0),  # 1 substitution
        ("جامعه الملك فيصل", "جامعه الملك فيصل", 0, 0, 0),  # exact match
        ("فرع مكه", "فرع مكه الرئيسي", 0, 0, 1),  # 1 insertion
        ("فرع مكه الرئيسي", "فرع مكه", 0, 1, 0),  # 1 deletion
    ]
    print("Running WER Calculator Self-Test:")
    for ref, hyp, exp_s, exp_d, exp_i in test_cases:
        wer, s, d, i, n = calculate_wer(ref, hyp)
        exp_dist = exp_s + exp_d + exp_i
        calc_dist = s + d + i
        assert calc_dist == exp_dist, (
            f"Failed for '{ref}' vs '{hyp}': Got dist {calc_dist}, Expected {exp_dist}"
        )
        print(f"PASS: '{ref}' vs '{hyp}' -> WER: {wer:.2%} (S:{s}, D:{d}, I:{i})")
