import math
from collections import Counter

# Cache entropy per game
entropy_cache = {}


def reset_entropy_cache():
    entropy_cache.clear()


def parse_feedback(s: str) -> int:
    """
    Convert feedback string (e.g. gybbg) to base-3 code
    """
    mapping = {"b": 0, "y": 1, "g": 2}
    if len(s) != 5 or any(c not in mapping for c in s):
        raise ValueError("Invalid feedback")

    code = 0
    for ch in s:
        code = code * 3 + mapping[ch]
    return code


def entropy(guess_idx, candidates, fb_table):
    """
    Compute entropy of a guess over remaining answer candidates

    fb_table shape:
        fb_table[answer_idx][guess_idx]
    """
    key = (guess_idx, tuple(candidates))
    if key in entropy_cache:
        return entropy_cache[key]

    counter = Counter(fb_table[candidate][guess_idx] for candidate in candidates)

    total = len(candidates)

    ent = -sum((cnt / total) * math.log2(cnt / total) for cnt in counter.values())

    entropy_cache[key] = ent
    return ent


def best_guess(candidates, guess_space, fb_table):
    """
    Choose guess with maximum expected information gain
    """
    best = None
    best_score = -1.0

    for guess_idx in guess_space:
        score = entropy(guess_idx, candidates, fb_table)
        if score > best_score:
            best = guess_idx
            best_score = score

    return best


def filter_candidates(candidates, guess_idx, feedback, fb_table):
    """
    Keep only answers that would produce the same feedback
    """
    return [
        candidate
        for candidate in candidates
        if fb_table[candidate][guess_idx] == feedback
    ]
