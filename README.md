# 🧠 Wordle Solver — Logical Working & System Design

This project implements a **provably correct, entropy-optimal Wordle solver** with a **modern web UI** and a **FastAPI backend**, designed to run within **strict memory limits (≤512 MB)** on free cloud platforms like **Render**.

All expensive computation is **preprocessed once** and accessed via **memory-mapped files**, enabling fast, real-time interaction without sacrificing correctness.

---

## 1. High-Level Architecture

The system is split into **five logical layers**:

1. **Cache Builder** (`compute.py`)
2. **Memory-Mapped Feedback Store** (`feedback.bin`)
3. **Solver Engine** (`wordle.py`)
4. **Backend API** (`server.py`)
5. **Frontend UI** (`index.html + script.js`)

```
answers.txt + allowed.txt
        ↓
    compute.py
        ↓
  feedback.bin (mmap)
        ↓
FastAPI backend (server.py)
        ↓
Entropy Solver (wordle.py)
        ↓
 Web Frontend (Wordle-style UI)
```

---

## 2. Core Problem: Wordle Feedback Computation

In Wordle, each guess produces 5 tiles:

- 🟩 Green → correct letter & position
- 🟨 Yellow → correct letter, wrong position
- ⬛ Black → letter not present

### Feedback Encoding

Each tile is encoded as:

```
Black  = 0
Yellow = 1
Green  = 2
```

The 5-tile pattern is converted to a **base-3 integer**:

```
Example: g y b b g
          2 1 0 0 2

Code = 2×3⁴ + 1×3³ + 0×3² + 0×3¹ + 2×3⁰ = 242
```

### Why This Matters

- Enables **constant-time comparison**
- Compact (fits in **1 byte per pair**)
- Perfectly preserves Wordle rules
- Allows deterministic filtering

---

## 3. Memory-Mapped Precomputation (Critical Upgrade)

### The Problem

A naïve feedback table requires:

```
13,000 × 13,000 ≈ 169 million entries
```

Storing this in RAM **exceeds Render’s 512 MB limit**.

### The Solution: `mmap`

Instead of keeping the table in memory:

- Feedback is stored in `feedback.bin`
- Accessed via **OS-level memory mapping**
- Pages are loaded **only when accessed**

```python
def fb_get(answer_idx, guess_idx):
    return fb_map[answer_idx * TOTAL + guess_idx]
```

### Result

| Property    | Value                       |
| ----------- | --------------------------- |
| RAM usage   | ~30–40 MB                   |
| Lookup      | O(1)                        |
| Correctness | Identical to full NxN table |
| Scalability | OS-managed                  |

---

## 4. Cache Builder (`compute.py`)

### What Is Built

- `feedback.bin` → mmap feedback table (answers × all guesses)
- `words.pkl` → ordered word list
- `meta.pkl` → counts (answers, total words)

### Why Only `answers × guesses`?

Wordle’s true solution space is **answers only**.
Feedback for non-answer targets is never needed.

This reduces storage from:

```
13k × 13k  →  2315 × 13k
```

**Without breaking correctness.**

---

## 5. Solver Logic (Entropy Maximization)

### Candidate Space

- **Candidates** → remaining possible answers
- **Guess Space** → all allowed guesses

### Entropy Formula

For guess `g`:

```
Entropy(g) = − Σ p(f) · log₂ p(f)
```

Where:

- `f` = possible feedback patterns
- `p(f)` = probability over remaining candidates

### Interpretation

- High entropy → best information gain
- Low entropy → weak guess

The solver always selects the guess that **maximally splits the candidate space**.

---

## 6. Candidate Filtering (Correctness Guarantee)

After user feedback `f`:

```
new_candidates = {
  word ∈ candidates |
  feedback(word, guess) == f
}
```

This filtering is:

- Deterministic
- Exact (matches Wordle rules)
- O(N) per step
- Uses mmap lookups (no recomputation)

---

## 7. Backend Design (FastAPI)

### Stateless Solver Core

`wordle.py`:

- No I/O
- No global state
- Pure computation

### Stateful API Layer

`server.py` manages:

- Active sessions
- Candidate lists
- Guess progression

### Endpoints

| Endpoint      | Purpose              |
| ------------- | -------------------- |
| `GET /health` | Wake-up & monitoring |
| `POST /start` | Start new game       |
| `POST /step`  | Submit feedback      |

### Session Safety

- TTL-based cleanup
- Hard session cap
- Thread-safe locking
- Render sleep-resilient

---

## 8. Frontend (Wordle-Style UI)

### Tile Interaction

- Click cycles: ⬛ → 🟨 → 🟩
- No manual typing (`gybbg`)
- Feedback always valid

### UX Enhancements

- Guess history
- Mobile-friendly layout
- Disabled input after solve
- Restart without reload
- “How to Play” popup

### Backend Safety

- Auto wake (`/health`)
- Session reset on restart
- Graceful error recovery

---

## 9. Performance Characteristics

| Component         | Complexity      |
| ----------------- | --------------- |
| Cache build       | O(N²) (offline) |
| Feedback lookup   | O(1)            |
| Entropy per guess | O(N)            |
| Candidate filter  | O(N)            |
| Frontend actions  | O(1)            |

Gameplay is **instantaneous**, even on free tiers.

---

## 10. Correctness Proof (Summary)

This solver is **logically equivalent** to the classic NxN Wordle solver because:

1. Feedback computation is identical
2. Candidate filtering is exact
3. Entropy calculation uses full feedback distribution
4. mmap only changes _storage_, not logic

The solver passes:

- Official Wordle answer sets
- Known hard cases (duplicate letters)
- Automated regression tests

---

## 11. Deployment Architecture

- **Backend** → Render (FastAPI + mmap)
- **Frontend** → Vercel / GitHub Pages
- **Storage** → Local filesystem (ephemeral OK)
- **Secrets** → None required

# 🧠 Wordle Solver — Logical Working & System Design

This project implements a **provably correct, entropy-optimal Wordle solver** with a **modern web UI** and a **FastAPI backend**, designed to run within **strict memory limits (≤512 MB)** on free cloud platforms like **Render**.

All expensive computation is **preprocessed once** and accessed via **memory-mapped files**, enabling fast, real-time interaction without sacrificing correctness.

---

## 1. High-Level Architecture

The system is split into **five logical layers**:

1. **Cache Builder** (`compute.py`)
2. **Memory-Mapped Feedback Store** (`feedback.bin`)
3. **Solver Engine** (`wordle.py`)
4. **Backend API** (`server.py`)
5. **Frontend UI** (`index.html + script.js`)

```
answers.txt + allowed.txt
        ↓
    compute.py
        ↓
  feedback.bin (mmap)
        ↓
FastAPI backend (server.py)
        ↓
Entropy Solver (wordle.py)
        ↓
 Web Frontend (Wordle-style UI)
```

---

## 2. Core Problem: Wordle Feedback Computation

In Wordle, each guess produces 5 tiles:

- 🟩 Green → correct letter & position
- 🟨 Yellow → correct letter, wrong position
- ⬛ Black → letter not present

### Feedback Encoding

Each tile is encoded as:

```
Black  = 0
Yellow = 1
Green  = 2
```

The 5-tile pattern is converted to a **base-3 integer**:

```
Example: g y b b g
          2 1 0 0 2

Code = 2×3⁴ + 1×3³ + 0×3² + 0×3¹ + 2×3⁰ = 242
```

### Why This Matters

- Enables **constant-time comparison**
- Compact (fits in **1 byte per pair**)
- Perfectly preserves Wordle rules
- Allows deterministic filtering

---

## 3. Memory-Mapped Precomputation (Critical Upgrade)

### The Problem

A naïve feedback table requires:

```
13,000 × 13,000 ≈ 169 million entries
```

Storing this in RAM **exceeds Render’s 512 MB limit**.

### The Solution: `mmap`

Instead of keeping the table in memory:

- Feedback is stored in `feedback.bin`
- Accessed via **OS-level memory mapping**
- Pages are loaded **only when accessed**

```python
def fb_get(answer_idx, guess_idx):
    return fb_map[answer_idx * TOTAL + guess_idx]
```

### Result

| Property    | Value                       |
| ----------- | --------------------------- |
| RAM usage   | ~30–40 MB                   |
| Lookup      | O(1)                        |
| Correctness | Identical to full NxN table |
| Scalability | OS-managed                  |

---

## 4. Cache Builder (`compute.py`)

### What Is Built

- `feedback.bin` → mmap feedback table (answers × all guesses)
- `words.pkl` → ordered word list
- `meta.pkl` → counts (answers, total words)

### Why Only `answers × guesses`?

Wordle’s true solution space is **answers only**.
Feedback for non-answer targets is never needed.

This reduces storage from:

```
13k × 13k  →  2315 × 13k
```

**Without breaking correctness.**

---

## 5. Solver Logic (Entropy Maximization)

### Candidate Space

- **Candidates** → remaining possible answers
- **Guess Space** → all allowed guesses

### Entropy Formula

For guess `g`:

```
Entropy(g) = − Σ p(f) · log₂ p(f)
```

Where:

- `f` = possible feedback patterns
- `p(f)` = probability over remaining candidates

### Interpretation

- High entropy → best information gain
- Low entropy → weak guess

The solver always selects the guess that **maximally splits the candidate space**.

---

## 6. Candidate Filtering (Correctness Guarantee)

After user feedback `f`:

```
new_candidates = {
  word ∈ candidates |
  feedback(word, guess) == f
}
```

This filtering is:

- Deterministic
- Exact (matches Wordle rules)
- O(N) per step
- Uses mmap lookups (no recomputation)

---

## 7. Backend Design (FastAPI)

### Stateless Solver Core

`wordle.py`:

- No I/O
- No global state
- Pure computation

### Stateful API Layer

`server.py` manages:

- Active sessions
- Candidate lists
- Guess progression

### Endpoints

| Endpoint      | Purpose              |
| ------------- | -------------------- |
| `GET /health` | Wake-up & monitoring |
| `POST /start` | Start new game       |
| `POST /step`  | Submit feedback      |

### Session Safety

- TTL-based cleanup
- Hard session cap
- Thread-safe locking
- Render sleep-resilient

---

## 8. Frontend (Wordle-Style UI)

### Tile Interaction

- Click cycles: ⬛ → 🟨 → 🟩
- No manual typing (`gybbg`)
- Feedback always valid

### UX Enhancements

- Guess history
- Mobile-friendly layout
- Disabled input after solve
- Restart without reload
- “How to Play” popup

### Backend Safety

- Auto wake (`/health`)
- Session reset on restart
- Graceful error recovery

---

## 9. Performance Characteristics

| Component         | Complexity      |
| ----------------- | --------------- |
| Cache build       | O(N²) (offline) |
| Feedback lookup   | O(1)            |
| Entropy per guess | O(N)            |
| Candidate filter  | O(N)            |
| Frontend actions  | O(1)            |

Gameplay is **instantaneous**, even on free tiers.

---

## 10. Correctness Proof (Summary)

This solver is **logically equivalent** to the classic NxN Wordle solver because:

1. Feedback computation is identical
2. Candidate filtering is exact
3. Entropy calculation uses full feedback distribution
4. mmap only changes _storage_, not logic

The solver passes:

- Official Wordle answer sets
- Known hard cases (duplicate letters)
- Automated regression tests

---

## 11. Deployment Architecture

- **Backend** → Render (FastAPI + mmap)
- **Frontend** → Vercel / GitHub Pages
- **Storage** → Local filesystem (ephemeral OK)
- **Secrets** → None required

## 📄 License

This project is licensed under the **MIT License**.  
You are free to use, modify, and distribute this software with attribution.
