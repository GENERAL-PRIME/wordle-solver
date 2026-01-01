import os
import pickle
import json
import hashlib
from tqdm import tqdm

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
CACHE_DIR = "cache"
ANSWERS_FILE = "answers.txt"
ALLOWED_FILE = "allowed.txt"
VERSION_FILE = os.path.join(CACHE_DIR, "version.json")


# --------------------------------------------------
# Utilities
# --------------------------------------------------
def load_words(path):
    with open(path, "r", encoding="utf-8") as f:
        return [w.strip() for w in f if len(w.strip()) == 5]


def encode_words(words):
    return [[ord(c) - 97 for c in w] for w in words]


def save(obj, path):
    with open(path, "wb") as f:
        pickle.dump(obj, f)


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


# --------------------------------------------------
# Feedback Computation
# --------------------------------------------------
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


# --------------------------------------------------
# Build Feedback Table
# --------------------------------------------------
def build_feedback_table(words_enc, answers_count):
    total_words = len(words_enc)
    table = []

    for i in tqdm(range(answers_count), desc="Building feedback table"):
        gi = words_enc[i]
        row = [0] * total_words
        for j in range(total_words):
            row[j] = compute_feedback(gi, words_enc[j])
        table.append(row)

    return table


# --------------------------------------------------
# Version Handling
# --------------------------------------------------
def current_version():
    return {
        "answers_hash": file_hash(ANSWERS_FILE),
        "allowed_hash": file_hash(ALLOWED_FILE),
    }


def load_saved_version():
    if not os.path.exists(VERSION_FILE):
        return None
    with open(VERSION_FILE, "r") as f:
        return json.load(f)


def save_version(version):
    with open(VERSION_FILE, "w") as f:
        json.dump(version, f, indent=2)


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def main():
    os.makedirs(CACHE_DIR, exist_ok=True)

    current = current_version()
    saved = load_saved_version()

    if saved == current:
        print("⚡ Word list unchanged — cache is up to date.")
        return

    print("🔄 Word list changed — rebuilding cache...")

    answers = load_words(ANSWERS_FILE)
    allowed = load_words(ALLOWED_FILE)

    words = answers + [w for w in allowed if w not in answers]
    answers_count = len(answers)

    words_enc = encode_words(words)
    fb_table = build_feedback_table(words_enc, answers_count)

    save(words, os.path.join(CACHE_DIR, "words.pkl"))
    save(fb_table, os.path.join(CACHE_DIR, "feedback_table.pkl"))
    save(answers_count, os.path.join(CACHE_DIR, "meta.pkl"))
    save_version(current)

    print("✅ Cache rebuilt successfully!")


if __name__ == "__main__":
    main()
