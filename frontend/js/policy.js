/**
 * ============================================================
 * policy.js
 * ============================================================
 * Logic untuk halaman policy.html.
 *
 * Tanggung jawab:
 * 1. Saat halaman dibuka dari alur normal (setelah underwriting
 *    Accepted), otomatis memanggil POST /issue-policy menggunakan
 *    quote_id dari state, lalu GET /policy/{policy_number} untuk
 *    menampilkan detail lengkap.
 * 2. Menyediakan form pencarian polis manual via GET /policy/{policy_number}
 *    (misalnya jika pengguna membuka kembali halaman ini di kemudian hari).
 * 3. Menyediakan tombol Print yang memanfaatkan window.print() dan
 *    CSS @media print (lihat style.css) untuk menyembunyikan elemen
 *    non-esensial (header, footer, stepper, tombol) saat dicetak.
 *
 * CATATAN STATE:
 * Menggunakan localStorage key yang sama dengan index.js, quote.js,
 * dan underwriting.js ("etiqa_mvi_state").
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

const loadingSection = document.getElementById("policy-loading-section");
const policySection = document.getElementById("policy-section");
const searchSection = document.getElementById("policy-search-section");

const policyNumberEl = document.getElementById("policy-number");
const policyIssuedAtEl = document.getElementById("policy-issued-at");

const detailCustomerName = document.getElementById("detail-customer-name");
const detailCustomerEmail = document.getElementById("detail-customer-email");
const detailCustomerPhone = document.getElementById("detail-customer-phone");

const detailVehicleType = document.getElementById("detail-vehicle-type");
const detailVehicleBrandModel = document.getElementById("detail-vehicle-brand-model");
const detailVehicleYear = document.getElementById("detail-vehicle-year");
const detailVehicleValue = document.getElementById("detail-vehicle-value");
const detailVehicleRegion = document.getElementById("detail-vehicle-region");
const detailVehicleCategory = document.getElementById("detail-vehicle-category");

const detailCoverage = document.getElementById("detail-coverage");
const detailRate = document.getElementById("detail-rate");
const detailPremium = document.getElementById("detail-premium");

const detailUnderwritingDecision = document.getElementById("detail-underwriting-decision");

const btnBackHome = document.getElementById("btn-back-home");
const btnPrintPolicy = document.getElementById("btn-print-policy");

const inputSearchPolicyNumber = document.getElementById("input-search-policy-number");
const btnSearchPolicy = document.getElementById("btn-search-policy");
const btnSearchPolicyText = document.getElementById("btn-search-policy-text");

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
// FORMATTING HELPERS
// ------------------------------------------------------------
function formatCurrency(value) {
  const number = Number(value);
  if (Number.isNaN(number)) return "-";
  return `Rp ${number.toLocaleString("id-ID", { maximumFractionDigits: 0 })}`;
}

function formatPercent(value) {
  const number = Number(value);
  if (Number.isNaN(number)) return "-";
  return `${number.toFixed(2)}%`;
}

function formatDateTime(isoString) {
  if (!isoString) return "-";
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString("id-ID", {
    day: "2-digit",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function capitalize(str) {
  if (!str) return "-";
  return str.charAt(0).toUpperCase() + str.slice(1);
}

// ------------------------------------------------------------
// RENDER POLICY DETAIL (dari PolicyDetailResponse backend)
// ------------------------------------------------------------
function renderPolicyDetail(detail) {
  policyNumberEl.textContent = detail.policy_number;
  policyIssuedAtEl.textContent = `Diterbitkan pada ${formatDateTime(detail.issued_at)}`;

  detailCustomerName.textContent = detail.customer_name;
  detailCustomerEmail.textContent = detail.customer_email;
  detailCustomerPhone.textContent = detail.customer_phone;

  detailVehicleType.textContent = capitalize(detail.vehicle_type);
  detailVehicleBrandModel.textContent = `${detail.brand} ${detail.model}`;
  detailVehicleYear.textContent = detail.year;
  detailVehicleValue.textContent = formatCurrency(detail.market_value);
  detailVehicleRegion.textContent = detail.region;
  detailVehicleCategory.textContent = detail.category ? `Kategori ${detail.category}` : "-";

  detailCoverage.textContent = detail.coverage_type;
  detailRate.textContent = formatPercent(detail.rate_used);
  detailPremium.textContent = formatCurrency(detail.premium);

  detailUnderwritingDecision.textContent = detail.underwriting_decision;

  loadingSection.classList.add("hidden");
  policySection.classList.remove("hidden");

  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ------------------------------------------------------------
// FLOW: ISSUE POLICY (dipanggil otomatis jika datang dari underwriting)
// ------------------------------------------------------------
async function issueAndShowPolicy(quoteId) {
  try {
    const policy = await EtiqaAPI.issuePolicy({ quoteId });

    saveAppState({
      policyNumber: policy.policy_number,
    });

    const detail = await EtiqaAPI.getPolicyDetail(policy.policy_number);
    renderPolicyDetail(detail);
  } catch (err) {
    loadingSection.classList.add("hidden");
    showAlert(err.message || "Gagal menerbitkan polis. Silakan coba lagi.");
  }
}

// ------------------------------------------------------------
// FLOW: LOAD POLICY YANG SUDAH PERNAH DITERBITKAN (dari state)
// ------------------------------------------------------------
async function showExistingPolicy(policyNumber) {
  try {
    const detail = await EtiqaAPI.getPolicyDetail(policyNumber);
    renderPolicyDetail(detail);
  } catch (err) {
    loadingSection.classList.add("hidden");
    showAlert(err.message || "Gagal mengambil detail polis. Silakan coba lagi.");
  }
}

// ------------------------------------------------------------
// INIT PAGE
// ------------------------------------------------------------
(function initPage() {
  const state = getAppState();

  if (state.policyNumber) {
    // Polis sudah pernah diterbitkan sebelumnya di sesi ini
    showExistingPolicy(state.policyNumber);
    return;
  }

  if (state.underwritingDecision === "Accepted" && state.quoteId) {
    // Baru datang dari underwriting yang Accepted -> terbitkan polis
    issueAndShowPolicy(state.quoteId);
    return;
  }

  // Tidak ada state valid -> sembunyikan loading, biarkan pengguna
  // mencari polis secara manual lewat form pencarian
  loadingSection.classList.add("hidden");
  showAlert(
    "Sesi penerbitan polis tidak ditemukan. Anda tetap dapat mencari polis yang sudah diterbitkan menggunakan form di bawah."
  );
})();

// ------------------------------------------------------------
// NAVIGATION & PRINT
// ------------------------------------------------------------
btnBackHome.addEventListener("click", () => {
  localStorage.removeItem(STORAGE_KEY);
  window.location.href = "index.html";
});

btnPrintPolicy.addEventListener("click", () => {
  window.print();
});

// ------------------------------------------------------------
// SEARCH POLICY MANUAL -> GET /policy/{policy_number}
// ------------------------------------------------------------
btnSearchPolicy.addEventListener("click", async () => {
  clearAlert();
  clearFieldError("error-search-policy-number");

  const policyNumber = inputSearchPolicyNumber.value.trim();

  if (!policyNumber) {
    showFieldError("error-search-policy-number");
    return;
  }

  btnSearchPolicy.disabled = true;
  btnSearchPolicyText.innerHTML = `<span class="loading-spinner"></span> Mencari...`;

  try {
    const detail = await EtiqaAPI.getPolicyDetail(policyNumber);

    saveAppState({ policyNumber: detail.policy_number });

    searchSection.classList.add("hidden");
    renderPolicyDetail(detail);
  } catch (err) {
    showFieldError("error-search-policy-number");
    showAlert(err.message || "Nomor polis tidak ditemukan.");
  } finally {
    btnSearchPolicy.disabled = false;
    btnSearchPolicyText.textContent = "Cari Polis";
  }
});