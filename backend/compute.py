import os
import pickle
import struct
from tqdm import tqdm

CACHE_DIR = "cache"
ANSWERS_FILE = "answers.txt"
ALLOWED_FILE = "allowed.txt"
BIN_PATH = os.path.join(CACHE_DIR, "feedback.bin")


def load_words(path):
    with open(path) as f:
        return [w.strip() for w in f if len(w.strip()) == 5]


def encode_words(words):
    return [[ord(c) - 97 for c in w] for w in words]


def compute_feedback(guess, target):
    fb0 = fb1 = fb2 = fb3 = fb4 = 0

    # Frequency dict for unmatched target chars
    freq = {}

    # Pass 1: exact matches + count leftovers
    g0, g1, g2, g3, g4 = guess
    t0, t1, t2, t3, t4 = target

    if g0 == t0:
        fb0 = 2
    else:
        freq[t0] = freq.get(t0, 0) + 1

    if g1 == t1:
        fb1 = 2
    else:
        freq[t1] = freq.get(t1, 0) + 1

    if g2 == t2:
        fb2 = 2
    else:
        freq[t2] = freq.get(t2, 0) + 1

    if g3 == t3:
        fb3 = 2
    else:
        freq[t3] = freq.get(t3, 0) + 1

    if g4 == t4:
        fb4 = 2
    else:
        freq[t4] = freq.get(t4, 0) + 1

    # Pass 2: partial matches (no nested loops)
    if fb0 == 0 and freq.get(g0, 0):
        fb0 = 1
        freq[g0] -= 1
    if fb1 == 0 and freq.get(g1, 0):
        fb1 = 1
        freq[g1] -= 1
    if fb2 == 0 and freq.get(g2, 0):
        fb2 = 1
        freq[g2] -= 1
    if fb3 == 0 and freq.get(g3, 0):
        fb3 = 1
        freq[g3] -= 1
    if fb4 == 0 and freq.get(g4, 0):
        fb4 = 1
        freq[g4] -= 1

    # Base-3 encoding (fully unrolled)
    return (((fb0 * 3 + fb1) * 3 + fb2) * 3 + fb3) * 3 + fb4


def main():
    os.makedirs(CACHE_DIR, exist_ok=True)

    answers = load_words(ANSWERS_FILE)
    allowed = load_words(ALLOWED_FILE)

    words = answers + [w for w in allowed if w not in answers]
    answers_count = len(answers)
    total_words = len(words)

    words_enc = encode_words(words)

    # Local bindings (IMPORTANT for speed)
    compute_fb = compute_feedback
    enc = words_enc
    guess_range = range(total_words)

    print("🧠 Building mmap feedback.bin …")

    # Large buffer improves throughput
    with open(BIN_PATH, "wb", buffering=1024 * 1024) as f:
        for answer_idx in tqdm(range(answers_count), desc="Answers"):
            answer = enc[answer_idx]

            # One full row = total_words bytes
            row = bytearray(total_words)

            for guess_idx in guess_range:
                row[guess_idx] = compute_fb(enc[guess_idx], answer)

            # SINGLE write per answer (huge win)
            f.write(row)

    with open(os.path.join(CACHE_DIR, "words.pkl"), "wb") as f:
        pickle.dump(words, f)

    with open(os.path.join(CACHE_DIR, "meta.pkl"), "wb") as f:
        pickle.dump(
            {
                "answers_count": answers_count,
                "total_words": total_words,
            },
            f,
        )

    print("✅ mmap cache built successfully!")


if __name__ == "__main__":
    main()
