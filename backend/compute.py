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
    fb = [0] * 5
    used = [False] * 5

    for i in range(5):
        if guess[i] == target[i]:
            fb[i] = 2
            used[i] = True

    for i in range(5):
        if fb[i] == 0:
            for j in range(5):
                if not used[j] and guess[i] == target[j]:
                    fb[i] = 1
                    used[j] = True
                    break

    code = 0
    for v in fb:
        code = code * 3 + v
    return code


def main():
    os.makedirs(CACHE_DIR, exist_ok=True)

    answers = load_words(ANSWERS_FILE)
    allowed = load_words(ALLOWED_FILE)

    words = answers + [w for w in allowed if w not in answers]
    answers_count = len(answers)
    total_words = len(words)

    words_enc = encode_words(words)

    print("🧠 Building mmap feedback.bin …")
    with open(BIN_PATH, "wb") as f:
        for i in tqdm(range(answers_count), desc="Answers"):
            gi = words_enc[i]
            for j in range(total_words):
                fb = compute_feedback(gi, words_enc[j])
                f.write(struct.pack("B", fb))  # 1 byte

    with open(os.path.join(CACHE_DIR, "words.pkl"), "wb") as f:
        pickle.dump(words, f)

    with open(os.path.join(CACHE_DIR, "meta.pkl"), "wb") as f:
        pickle.dump({"answers_count": answers_count, "total_words": total_words}, f)

    print("✅ mmap cache built successfully!")


if __name__ == "__main__":
    main()
