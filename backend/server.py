import os
import pickle
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from wordle import parse_feedback, best_guess, filter_candidates, reset_entropy_cache

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# LOAD CACHED DATA
CACHE_DIR = "cache"

with open(os.path.join(CACHE_DIR, "words.pkl"), "rb") as f:
    words = pickle.load(f)

with open(os.path.join(CACHE_DIR, "feedback_table.pkl"), "rb") as f:
    fb_table = pickle.load(f)

with open(os.path.join(CACHE_DIR, "meta.pkl"), "rb") as f:
    answers_count = pickle.load(f)


# SESSION STORAGE (IN-MEMORY)
sessions = {}


# API MODELS
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


# API ENDPOINTS
@app.post("/start", response_model=StartResponse)
def start_game():
    reset_entropy_cache()

    session_id = os.urandom(8).hex()
    candidates = list(range(answers_count))

    guess = words.index("crane") if "crane" in words else candidates[0]

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
        raise ValueError("Invalid session")

    candidates = state["candidates"]
    guess = state["guess"]

    feedback = parse_feedback(req.feedback)

    if feedback == 242:
        return {"guess": words[guess], "candidates": 1, "solved": True}

    candidates = filter_candidates(candidates, guess, feedback, fb_table)

    if not candidates:
        return {"guess": "", "candidates": 0, "solved": False}

    if len(candidates) == 1:
        next_guess = candidates[0]
    else:
        guess_space = list(range(len(words)))
        next_guess = best_guess(candidates, guess_space, fb_table)

    state["candidates"] = candidates
    state["guess"] = next_guess

    return {"guess": words[next_guess], "candidates": len(candidates), "solved": False}
