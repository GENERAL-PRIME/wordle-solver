import os
import mmap
import pickle
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from wordle import (
    parse_feedback,
    best_guess,
    filter_candidates,
    reset_entropy_cache,
)

CACHE_DIR = "cache"

# --------------------------------------------------
# LOAD METADATA
# --------------------------------------------------
with open(os.path.join(CACHE_DIR, "words.pkl"), "rb") as f:
    words = pickle.load(f)

with open(os.path.join(CACHE_DIR, "meta.pkl"), "rb") as f:
    meta = pickle.load(f)

ANSWERS = meta["answers_count"]
TOTAL = meta["total_words"]

# --------------------------------------------------
# MMAP FEEDBACK TABLE
# --------------------------------------------------
fb_file = open(os.path.join(CACHE_DIR, "feedback.bin"), "rb")
fb_map = mmap.mmap(fb_file.fileno(), 0, access=mmap.ACCESS_READ)


def fb_get(answer_idx, guess_idx):
    return fb_map[answer_idx * TOTAL + guess_idx]


# --------------------------------------------------
# FASTAPI
# --------------------------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

sessions = {}


class StartResponse(BaseModel):
    session_id: str
    guess: str
    candidates: int


class StepRequest(BaseModel):
    session_id: str
    feedback: str


class StepResponse(BaseModel):
    guess: str
    candidates: int
    solved: bool


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/start", response_model=StartResponse)
def start():
    reset_entropy_cache()

    session_id = os.urandom(8).hex()
    candidates = list(range(ANSWERS))
    guess = words.index("crane")

    sessions[session_id] = {"candidates": candidates, "guess": guess}

    return {
        "session_id": session_id,
        "guess": words[guess],
        "candidates": len(candidates),
    }


@app.post("/step", response_model=StepResponse)
def step(req: StepRequest):
    state = sessions.get(req.session_id)
    if not state:
        return {"guess": "", "candidates": 0, "solved": False}

    candidates = state["candidates"]
    guess = state["guess"]
    print(req.feedback)

    fb = parse_feedback(req.feedback)

    if fb == 242:
        return {"guess": words[guess], "candidates": 1, "solved": True}

    candidates = filter_candidates(candidates, guess, fb, fb_get)

    if not candidates:
        return {"guess": "", "candidates": 0, "solved": False}

    if len(candidates) == 1:
        next_guess = candidates[0]
    else:
        guess_space = range(TOTAL)
        next_guess = best_guess(candidates, guess_space, fb_get)

    state["candidates"] = candidates
    state["guess"] = next_guess

    return {
        "guess": words[next_guess],
        "candidates": len(candidates),
        "solved": False,
    }
