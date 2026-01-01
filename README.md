# 🧠 Wordle Solver — Logical Working & System Design

This project implements an **optimal Wordle solver** using **information theory (entropy maximization)**, combined with a **modern web interface** and a **FastAPI backend**.  
Heavy computation is preprocessed and cached to ensure fast, real-time interaction.

---

## 1. High-Level Architecture

The system is divided into four logical components:

1. **Cache Builder** (`build_cache.py`)
2. **Solver Engine** (`wordle.py`)
3. **Backend API** (`server.py`)
4. **Frontend UI** (`index.html`)

```
Word Lists → Cache Builder → Cached Feedback Table
↓
Frontend → FastAPI → Solver Engine → Next Guess
```

---

## 2. Core Problem: Wordle Feedback Computation

In Wordle, each guess produces a 5-character feedback:

- 🟩 Green → correct letter, correct position
- 🟨 Yellow → correct letter, wrong position
- ⬛ Black → letter not present

### Feedback Encoding

Each tile is encoded as:

```
Black  = 0
Yellow = 1
Green  = 2
```

The 5-tile feedback is converted into a **base-3 number**:

```
Example: g y b b g
2 1 0 0 2

Code = 2×3⁴ + 1×3³ + 0×3² + 0×3¹ + 2×3⁰ = 242
```

This allows:

- Fast comparison
- Efficient table storage
- Constant-time filtering

---

## 3. Precomputation (Cache Builder)

### Why Precompute?

Wordle has ~13,000 valid words.  
Computing feedback between all pairs costs:

```
O(N² × 5) ≈ 13,000² × 5 ≈ very expensive
```

So this computation is done **once**, offline.

### What Is Cached?

- `words.pkl` → combined word list (answers first)
- `feedback_table.pkl` → feedback code for every (guess, target) pair
- `meta.pkl` → number of valid answers
- `version.json` → hash of word lists (for auto-rebuild)

### Auto-Rebuild Logic

1. Compute SHA-256 hash of `answers.txt` and `allowed.txt`
2. Compare with stored hash
3. Rebuild cache **only if word lists changed**

This ensures correctness with zero unnecessary recomputation.

---

## 4. Solver Logic (Entropy Maximization)

### Candidate Space

- **Candidates**: possible correct answers (shrinks every turn)
- **Guess Space**: all allowed words (answers + non-answers)

### Entropy Formula

For a guess `g`:

```

Entropy(g) = − Σ p(f) · log₂ p(f)

```

Where:

- `f` = possible feedback patterns
- `p(f)` = probability of that feedback over remaining candidates

### Interpretation

- High entropy = guess splits candidates evenly
- Low entropy = guess gives little information

The solver always chooses the guess with **maximum expected information gain**.

---

## 5. Candidate Filtering

After user feedback:

```
new_candidates = {
word ∈ candidates |
feedback(guess, word) == user_feedback
}
```

This filtering is:

- Deterministic
- O(N) per step
- Uses the precomputed feedback table

---

## 6. Backend Design (FastAPI)

### Stateless Solver Core

The solver engine:

- Contains **no I/O**
- Performs only computation
- Is reusable and testable

### Session Handling

Each game session stores:

- Remaining candidates
- Last guess index

Endpoints:

- `POST /start` → start new game
- `POST /step` → submit feedback, receive next guess

---

## 7. Frontend Logic (Wordle-Style UI)

### Tile Interaction

- Tiles cycle on click: ⬛ → 🟨 → 🟩
- Feedback is constructed automatically
- No manual typing (`gybbg`) required

### UX Safety

After solving:

- Tiles become non-interactive
- Submit button is disabled
- Pointer events are blocked

Restart:

- Clears UI state
- Starts new backend session
- No page reload

---

## 8. Performance Characteristics

| Component            | Complexity       |
| -------------------- | ---------------- |
| Cache build          | O(N²) (one-time) |
| Per guess entropy    | O(N)             |
| Candidate filtering  | O(N)             |
| Frontend interaction | O(1)             |

With caching, gameplay is **instantaneous**.
