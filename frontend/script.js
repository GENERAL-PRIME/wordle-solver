let gameSolved = false;
const API = "https://wordle-solver-dy13.onrender.com"; // Adjust as needed
let sessionId = null;
let currentWord = "";
let tileState = []; // 0=b,1=y,2=g

// ---------------- TILE RENDER ----------------
function tile(letter, state, idx, clickable = true) {
  const colors = [
    "bg-neutral-700",
    "bg-yellow-500 tile-yellow",
    "bg-green-600 tile-green",
  ];

  return `
    <div
      ${clickable && !gameSolved ? `onclick="cycleTile(${idx})"` : ""}
      class="
        tile ${colors[state]}
        aspect-square rounded-xl
        flex items-center justify-center
        uppercase font-black

        ${
          clickable
            ? "text-3xl sm:text-4xl hover:scale-105 hover:brightness-110 cursor-pointer"
            : "text-xl"
        }

      "
    >
      ${letter}
    </div>
  `;
}

function renderCurrentGuess() {
  const container = document.getElementById("currentGuess");
  container.innerHTML = "";
  for (let i = 0; i < 5; i++) {
    container.innerHTML += tile(currentWord[i], tileState[i], i, true);
  }
}

function showLoading() {
  document.getElementById("loadingOverlay")?.classList.remove("hidden");
}

function hideLoading() {
  document.getElementById("loadingOverlay")?.classList.add("hidden");
}

function cycleTile(idx) {
  if (gameSolved) return;
  tileState[idx] = (tileState[idx] + 1) % 3;
  renderCurrentGuess();
}

// ---------------- FEEDBACK BUILD ----------------
function buildFeedback() {
  return tileState.map((v) => (v === 2 ? "g" : v === 1 ? "y" : "b")).join("");
}

// ---------------- HISTORY ----------------
function addToHistory(word, feedback) {
  const row = document.createElement("div");
  row.className = "grid grid-cols-5 gap-2";
  for (let i = 0; i < 5; i++) {
    row.innerHTML += tile(
      word[i],
      feedback[i] === "g" ? 2 : feedback[i] === "y" ? 1 : 0,
      i,
      false
    );
  }
  document.getElementById("history").prepend(row);
}

// ---------------- API ----------------
async function startGame() {
  const res = await fetch(`${API}/start`, {
    method: "POST",
  });

  const data = await res.json();

  sessionId = data.session_id;
  currentWord = data.guess.toUpperCase();
  tileState = [0, 0, 0, 0, 0];

  renderCurrentGuess();
  document.getElementById(
    "info"
  ).innerText = `Candidates remaining: ${data.candidates}`;

  hideLoading();
}

async function wakeBackend() {
  showLoading();

  const start = Date.now();
  const TIMEOUT = 60000; // 60 seconds max wait

  while (true) {
    try {
      const res = await fetch(`${API}/health`);
      if (res.ok) return;
    } catch {}

    if (Date.now() - start > TIMEOUT) {
      alert(
        "Backend is taking too long to start.\nPlease try refreshing in a moment."
      );
      break;
    }

    await new Promise((r) => setTimeout(r, 3000)); // retry every 3s
  }
}

async function submitFeedback() {
  // if (!tileState.some((v) => v !== 0)) {
  //   alert("Please enter feedback before submitting.");
  //   return;
  // }

  if (gameSolved) return;

  const feedback = buildFeedback().toLowerCase();
  addToHistory(currentWord, feedback);

  let res;
  try {
    res = await fetch(`${API}/step`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        feedback: feedback,
      }),
    });
  } catch {
    alert("Backend unreachable. Restarting game.");
    restartGame();
    return;
  }

  if (!res.ok) {
    alert("Session expired or backend restarted. Restarting game.");
    await restartGame();
    return;
  }

  const data = await res.json();

  if (data.solved) {
    gameSolved = true;
    document.getElementById("submitBtn").disabled = true;
  }

  currentWord = data.guess.toUpperCase();
  tileState = [0, 0, 0, 0, 0];

  renderCurrentGuess();

  document.getElementById("info").innerText = data.solved
    ? "🎉 Wordle Solved!"
    : `Candidates remaining: ${data.candidates}`;
}

async function restartGame() {
  gameSolved = false;

  document.getElementById("submitBtn").disabled = false;
  document.getElementById("history").innerHTML = "";
  document.getElementById("info").innerText = "Starting new game...";

  tileState = [0, 0, 0, 0, 0];
  await startGame();
}
async function init() {
  await wakeBackend();
  await startGame();
}

function openHowToPlay() {
  document.getElementById("howToPlayModal").classList.remove("hidden");
  document.getElementById("howToPlayModal").classList.add("flex");
}

function closeHowToPlay() {
  document.getElementById("howToPlayModal").classList.add("hidden");
  document.getElementById("howToPlayModal").classList.remove("flex");
}

init();
