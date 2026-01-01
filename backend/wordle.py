import math
from collections import Counter

entropy_cache = {}


def reset_entropy_cache():
    entropy_cache.clear()


def parse_feedback(s: str) -> int:
    mapping = {"b": 0, "y": 1, "g": 2}
    code = 0
    for ch in s:
        code = code * 3 + mapping[ch]
    return code


def entropy(guess_idx, candidates, fb_get):
    key = (guess_idx, frozenset(candidates))
    if key in entropy_cache:
        return entropy_cache[key]

    counter = Counter(fb_get(c, guess_idx) for c in candidates)
    total = len(candidates)

    ent = -sum((cnt / total) * math.log2(cnt / total) for cnt in counter.values())
    entropy_cache[key] = ent
    return ent


def best_guess(candidates, guess_space, fb_get):
    best, best_score = None, -1
    for g in guess_space:
        score = entropy(g, candidates, fb_get)
        if score > best_score:
            best, best_score = g, score
    return best


def filter_candidates(candidates, guess_idx, feedback, fb_get):
    return [c for c in candidates if fb_get(c, guess_idx) == feedback]
