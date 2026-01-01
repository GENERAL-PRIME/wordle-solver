import os
import mmap
import pickle
import time
import logging
import threading
import re
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from wordle import (
    parse_feedback,
    best_guess,
    filter_candidates,
    reset_entropy_cache,
)

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
CACHE_DIR = "cache"
SESSION_TTL = 15 * 60  # 15 minutes
MAX_SESSIONS = 500  # hard cap
MAX_ENTROPY_GUESSES = 64  # entropy limit
START_WORD = "crane"
SOLVED_FEEDBACK = int("22222", 3)

# --------------------------------------------------
# LOGGING
# --------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("wordle-api")

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
with open(os.path.join(CACHE_DIR, "words.pkl"), "rb") as f:
    words: List[str] = pickle.load(f)

with open(os.path.join(CACHE_DIR, "meta.pkl"), "rb") as f:
    meta = pickle.load(f)

ANSWERS = meta["answers_count"]
TOTAL = meta["total_words"]

WORD_TO_INDEX = {w: i for i, w in enumerate(words)}

if START_WORD not in WORD_TO_INDEX:
    raise RuntimeError("Start word missing from dictionary")

# --------------------------------------------------
# MMAP FEEDBACK TABLE
# --------------------------------------------------
fb_file = open(os.path.join(CACHE_DIR, "feedback.bin"), "rb")
fb_map = mmap.mmap(fb_file.fileno(), 0, access=mmap.ACCESS_READ)


def fb_get(answer_idx: int, guess_idx: int) -> int:
    return fb_map[answer_idx * TOTAL + guess_idx]


# --------------------------------------------------
# FASTAPI
# --------------------------------------------------
app = FastAPI(title="Wordle Solver API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# SESSION STORE (SAFE + BOUNDED)
# --------------------------------------------------
sessions: Dict[str, Dict] = {}
lock = threading.Lock()


def cleanup_sessions():
    now = time.time()
    expired = [sid for sid, s in sessions.items() if now - s["last_seen"] > SESSION_TTL]
    for sid in expired:
        del sessions[sid]


# --------------------------------------------------
# MODELS
# --------------------------------------------------
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


# --------------------------------------------------
# LIFECYCLE
# --------------------------------------------------
@app.on_event("startup")
def startup():
    reset_entropy_cache()
    logger.info("Entropy cache initialized")


@app.on_event("shutdown")
def shutdown():
    fb_map.close()
    fb_file.close()
    logger.info("Clean shutdown")


# --------------------------------------------------
# ROUTES
# --------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/start", response_model=StartResponse)
def start():
    with lock:
        cleanup_sessions()

        if len(sessions) >= MAX_SESSIONS:
            raise HTTPException(503, "Server busy")

        session_id = os.urandom(8).hex()
        candidates = list(range(ANSWERS))
        guess = WORD_TO_INDEX[START_WORD]

        sessions[session_id] = {
            "candidates": candidates,
            "guess": guess,
            "last_seen": time.time(),
        }

    return {
        "session_id": session_id,
        "guess": words[guess],
        "candidates": len(candidates),
    }


@app.post("/step", response_model=StepResponse)
def step(req: StepRequest):

    with lock:
        state = sessions.get(req.session_id)
        if not state:
            raise HTTPException(404, "Invalid session")

        state["last_seen"] = time.time()

    try:
        logger.info(f"Parsing feedback: {req.feedback}")
        fb = parse_feedback(req.feedback)
        logger.info(f"Parsing feedback: {req.feedback}", extra={"fb_code": fb})
    except ValueError as e:
        logger.warning(f"Bad feedback '{req.feedback}': {e}")
        raise HTTPException(400, "Invalid feedback")

    if fb == SOLVED_FEEDBACK:
        return {
            "guess": words[state["guess"]],
            "candidates": 1,
            "solved": True,
        }

    candidates = filter_candidates(
        state["candidates"],
        state["guess"],
        fb,
        fb_get,
    )

    if not candidates:
        raise HTTPException(500, "No candidates remaining")

    # ---- RAM-SAFE GUESS STRATEGY ----
    if len(candidates) == 1:
        next_guess = candidates[0]
    else:
        next_guess = best_guess(
            candidates,
            range(TOTAL),
            fb_get,
        )

    with lock:
        state["candidates"] = candidates
        state["guess"] = next_guess

    return {
        "guess": words[next_guess],
        "candidates": len(candidates),
        "solved": False,
    }
