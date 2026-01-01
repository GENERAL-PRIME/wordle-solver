import math
from collections import Counter

entropy_cache = {}


def reset_entropy_cache():
    entropy_cache.clear()


def parse_feedback(s: str) -> int:
    """
    Convert feedback string (gybbg) to base-3 code
    """
    mapping = {"b": 0, "y": 1, "g": 2}
    if len(s) != 5 or any(c not in mapping for c in s):
        raise ValueError("Invalid feedback")

    code = 0
    for ch in s:
        code = code * 3 + mapping[ch]
    return code


def entropy(guess_idx, candidates, fb_table):
    key = (guess_idx, tuple(candidates))
    if key in entropy_cache:
        return entropy_cache[key]

    counter = Counter(fb_table[guess_idx][c] for c in candidates)
    total = len(candidates)

    ent = -sum((cnt / total) * math.log2(cnt / total) for cnt in counter.values())

    entropy_cache[key] = ent
    return ent


def best_guess(candidates, guess_space, fb_table):
    best, best_score = None, -1

    for g in guess_space:
        score = entropy(g, candidates, fb_table)
        if score > best_score:
            best, best_score = g, score

    return best


def filter_candidates(candidates, guess_idx, feedback, fb_table):
    return [c for c in candidates if fb_table[guess_idx][c] == feedback]
