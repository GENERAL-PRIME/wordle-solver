import os
import pickle
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
# App setup
# --------------------------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Load cached data (must exist at startup)
# --------------------------------------------------
CACHE_DIR = "cache"

try:
    with open(os.path.join(CACHE_DIR, "words.pkl"), "rb") as f:
        words = pickle.load(f)

    with open(os.path.join(CACHE_DIR, "feedback_table.pkl"), "rb") as f:
        fb_table = pickle.load(f)

    with open(os.path.join(CACHE_DIR, "meta.pkl"), "rb") as f:
        answers_count = pickle.load(f)

except FileNotFoundError:
    raise RuntimeError(
        "Cache files missing. Ensure build_cache.py ran during deployment."
    )

# --------------------------------------------------
# In-memory session store
# --------------------------------------------------
sessions = {}


# --------------------------------------------------
# API Models
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
# Endpoints
# --------------------------------------------------
@app.post("/start", response_model=StartResponse)
def start_game():
    reset_entropy_cache()

    session_id = os.urandom(8).hex()
    candidates = list(range(answers_count))

    # Strong fixed opener
    guess = words.index("crane") if "crane" in words else candidates[0]

    sessions[session_id] = {
        "candidates": candidates,
        "guess": guess,
    }

    return {
        "session_id": session_id,
        "guess": words[guess],
        "candidates": len(candidates),
    }


@app.post("/step", response_model=StepResponse)
def step(req: StepRequest):
    state = sessions.get(req.session_id)
    if state is None:
        # IMPORTANT: do NOT crash the server
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired session",
        )

    candidates = state["candidates"]
    guess = state["guess"]

    feedback = parse_feedback(req.feedback)

    # Solved
    if feedback == 242:
        return {
            "guess": words[guess],
            "candidates": 1,
            "solved": True,
        }

    # Filter candidates (RECTANGULAR TABLE SAFE)
    candidates = filter_candidates(candidates, guess, feedback, fb_table)

    if not candidates:
        return {
            "guess": "",
            "candidates": 0,
            "solved": False,
        }

    # Next guess
    if len(candidates) == 1:
        next_guess = candidates[0]
    else:
        guess_space = list(range(len(words)))
        next_guess = best_guess(candidates, guess_space, fb_table)

    state["candidates"] = candidates
    state["guess"] = next_guess

    return {
        "guess": words[next_guess],
        "candidates": len(candidates),
        "solved": False,
    }
