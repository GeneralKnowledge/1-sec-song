let currentRound = null;
let activeAudio = null;

const scoreEl = document.getElementById("score");
const streakEl = document.getElementById("streak");
const statusEl = document.getElementById("status");
const resultTextEl = document.getElementById("result-text");
const choicesEl = document.getElementById("choices");
const playBtn = document.getElementById("play-btn");
const nextBtn = document.getElementById("next-btn");

async function fetchState() {
  const response = await fetch("/api/state");
  if (!response.ok) return;
  const state = await response.json();
  scoreEl.textContent = state.score;
  streakEl.textContent = state.streak;
}

function setLoading(message) {
  statusEl.textContent = message;
}

function renderChoices(choices) {
  choicesEl.innerHTML = "";
  choices.forEach((choice) => {
    const button = document.createElement("button");
    button.className = "choice";
    button.textContent = choice.title;
    button.addEventListener("click", () => submitGuess(choice.title));
    choicesEl.appendChild(button);
  });
}

function disableChoices() {
  document.querySelectorAll(".choice").forEach((btn) => (btn.disabled = true));
}

async function loadRound() {
  setLoading("Loading round...");
  resultTextEl.textContent = "";
  resultTextEl.className = "";
  nextBtn.hidden = true;
  playBtn.disabled = true;

  try {
    const response = await fetch("/api/round");
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Failed to load round");

    currentRound = data;
    renderChoices(data.choices);
    setLoading("Round ready. Press play and guess!");
  } catch (error) {
    setLoading(error.message);
  } finally {
    playBtn.disabled = false;
  }
}

async function playClip() {
  if (!currentRound) return;

  try {
    if (activeAudio) {
      activeAudio.pause();
      activeAudio = null;
    }

    const audio = new Audio(currentRound.preview_url);
    audio.preload = "auto";
    activeAudio = audio;

    await new Promise((resolve, reject) => {
      audio.addEventListener("loadedmetadata", resolve, { once: true });
      audio.addEventListener("error", () => reject(new Error("Could not load preview audio")), { once: true });
    });

    audio.currentTime = currentRound.start_ms / 1000;
    await audio.play();

    setTimeout(() => {
      audio.pause();
    }, currentRound.duration_ms);
  } catch (error) {
    setLoading(error.message || "Playback failed.");
  }
}

async function submitGuess(selectedChoice) {
  if (!currentRound) return;

  disableChoices();
  setLoading("Checking answer...");

  try {
    const response = await fetch("/api/guess", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        round_id: currentRound.round_id,
        token: currentRound.token,
        selected_choice: selectedChoice,
      }),
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Failed to submit guess");

    scoreEl.textContent = data.score;
    streakEl.textContent = data.streak;
    resultTextEl.className = data.correct ? "correct" : "incorrect";
    resultTextEl.textContent = data.correct
      ? `✅ Correct! ${data.correct_answer} — ${data.artist}`
      : `❌ Not quite. Correct answer: ${data.correct_answer} — ${data.artist}`;

    nextBtn.hidden = false;
    setLoading("Answer locked in. Start the next round when ready.");
  } catch (error) {
    setLoading(error.message);
  }
}

playBtn.addEventListener("click", playClip);
nextBtn.addEventListener("click", loadRound);

fetchState().then(loadRound);
