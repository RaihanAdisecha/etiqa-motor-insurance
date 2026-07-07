/**
 * ============================================================
 * underwriting.js
 * ============================================================
 * Logic untuk halaman underwriting.html.
 *
 * Tanggung jawab:
 * 1. Menampilkan 3 pertanyaan yes/no underwriting.
 * 2. Validasi bahwa seluruh pertanyaan sudah dijawab.
 * 3. Memanggil POST /underwriting dengan quote_id dari state.
 * 4. Menampilkan hasil keputusan (Accepted / Manual Review)
 *    berdasarkan response backend (bukan dihitung ulang di
 *    frontend), karena business rule adalah source of truth
 *    di backend (lihat backend/app/utils.py).
 *
 * CATATAN STATE:
 * Menggunakan localStorage key yang sama dengan index.js dan
 * quote.js ("etiqa_mvi_state").
 * ============================================================
 */

// ------------------------------------------------------------
// STATE KEYS (localStorage) - harus sama persis dengan file lain
// ------------------------------------------------------------
const STORAGE_KEY = "etiqa_mvi_state";

function getAppState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch (e) {
    return {};
  }
}

function saveAppState(partialState) {
  const current = getAppState();
  const updated = { ...current, ...partialState };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  return updated;
}

// ------------------------------------------------------------
// DOM ELEMENTS
// ------------------------------------------------------------
const pageAlertContainer = document.getElementById("page-alert-container");

const formSection = document.getElementById("underwriting-form-section");
const resultSection = document.getElementById("underwriting-result-section");

const toggleMajorAccident = document.getElementById("toggle-major-accident");
const toggleModification = document.getElementById("toggle-modification");
const toggleCommercialUse = document.getElementById("toggle-commercial-use");

const btnSubmit = document.getElementById("btn-submit-underwriting");
const btnSubmitText = document.getElementById("btn-submit-underwriting-text");

const statusBadge = document.getElementById("underwriting-status-badge");
const resultAcceptedBlock = document.getElementById("result-accepted-block");
const resultReviewBlock = document.getElementById("result-review-block");

const btnToPolicy = document.getElementById("btn-to-policy");
const btnBackHomeReview = document.getElementById("btn-back-home-review");

// Local answer state: null = belum dijawab, true/false = sudah dijawab
let answers = {
  hasMajorAccident: null,
  hasModification: null,
  isCommercialUse: null,
};

// ------------------------------------------------------------
// UTILITY: ALERT DISPLAY
// ------------------------------------------------------------
function showAlert(message, type = "danger") {
  pageAlertContainer.innerHTML = `<div class="alert alert-${type}">${escapeHtml(message)}</div>`;
}

function clearAlert() {
  pageAlertContainer.innerHTML = "";
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function showFieldError(elementId) {
  const el = document.getElementById(elementId);
  if (el) el.classList.add("visible");
}

function clearFieldError(elementId) {
  const el = document.getElementById(elementId);
  if (el) el.classList.remove("visible");
}

// ------------------------------------------------------------
// YES/NO TOGGLE HANDLING
// ------------------------------------------------------------
/**
 * Menghubungkan satu grup toggle (.yes-no-toggle) dengan key
 * jawaban tertentu, dan mengatur class visual "selected-yes" /
 * "selected-no" sesuai pilihan pengguna.
 */
function setupToggle(toggleEl, answerKey, errorElId) {
  const buttons = toggleEl.querySelectorAll(".toggle-btn");
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const value = btn.dataset.value === "true";
      answers[answerKey] = value;

      buttons.forEach((b) => {
        b.classList.remove("selected-yes", "selected-no");
      });

      if (value === true) {
        // Tombol "Ya" yang diklik
        btn.classList.add("selected-yes");
      } else {
        // Tombol "Tidak" yang diklik
        btn.classList.add("selected-no");
      }

      clearFieldError(errorElId);
    });
  });
}

setupToggle(toggleMajorAccident, "hasMajorAccident", "error-major-accident");
setupToggle(toggleModification, "hasModification", "error-modification");
setupToggle(toggleCommercialUse, "isCommercialUse", "error-commercial-use");

// ------------------------------------------------------------
// VALIDATION
// ------------------------------------------------------------
function validateAnswers() {
  let isValid = true;

  clearFieldError("error-major-accident");
  clearFieldError("error-modification");
  clearFieldError("error-commercial-use");

  if (answers.hasMajorAccident === null) {
    showFieldError("error-major-accident");
    isValid = false;
  }
  if (answers.hasModification === null) {
    showFieldError("error-modification");
    isValid = false;
  }
  if (answers.isCommercialUse === null) {
    showFieldError("error-commercial-use");
    isValid = false;
  }

  return isValid;
}

// ------------------------------------------------------------
// INIT PAGE
// ------------------------------------------------------------
(function initPage() {
  const state = getAppState();

  if (!state.quoteId || !state.isPurchased) {
    showAlert(
      "Sesi pembelian tidak ditemukan. Silakan mulai pengajuan dari awal atau lakukan pembelian terlebih dahulu."
    );
    btnSubmit.disabled = true;
  }
})();

// ------------------------------------------------------------
// SUBMIT UNDERWRITING -> POST /underwriting
// ------------------------------------------------------------
btnSubmit.addEventListener("click", async () => {
  clearAlert();

  if (!validateAnswers()) return;

  const state = getAppState();
  if (!state.quoteId) {
    showAlert("Quote tidak ditemukan. Silakan mulai pengajuan dari awal.");
    return;
  }

  btnSubmit.disabled = true;
  btnSubmitText.innerHTML = `<span class="loading-spinner"></span> Memproses...`;

  try {
    const result = await EtiqaAPI.submitUnderwriting({
      quoteId: state.quoteId,
      hasMajorAccident: answers.hasMajorAccident,
      hasModification: answers.hasModification,
      isCommercialUse: answers.isCommercialUse,
    });

    saveAppState({
      underwritingId: result.id,
      underwritingDecision: result.decision,
    });

    renderResult(result.decision);
  } catch (err) {
    showAlert(err.message || "Gagal mengirim jawaban underwriting. Silakan coba lagi.");
    btnSubmit.disabled = false;
    btnSubmitText.textContent = "Submit Underwriting";
  }
});

// ------------------------------------------------------------
// RENDER RESULT (Accepted / Manual Review)
// ------------------------------------------------------------
function renderResult(decision) {
  formSection.classList.add("hidden");
  resultSection.classList.remove("hidden");

  resultAcceptedBlock.classList.add("hidden");
  resultReviewBlock.classList.add("hidden");
  statusBadge.classList.remove("status-badge--accepted", "status-badge--review");

  if (decision === "Accepted") {
    statusBadge.textContent = "Accepted";
    statusBadge.classList.add("status-badge--accepted");
    resultAcceptedBlock.classList.remove("hidden");
  } else {
    statusBadge.textContent = "Manual Review";
    statusBadge.classList.add("status-badge--review");
    resultReviewBlock.classList.remove("hidden");
  }

  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ------------------------------------------------------------
// NAVIGATION
// ------------------------------------------------------------
btnToPolicy.addEventListener("click", () => {
  window.location.href = "policy.html";
});

btnBackHomeReview.addEventListener("click", () => {
  window.location.href = "index.html";
});