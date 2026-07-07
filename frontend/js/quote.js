/**
 * ============================================================
 * quote.js
 * ============================================================
 * Logic untuk halaman quote.html (Quote Summary).
 *
 * Tanggung jawab:
 * 1. Membaca state aplikasi (customer, vehicle, quote) dari
 *    localStorage yang sudah disimpan oleh index.js.
 * 2. Menampilkan ringkasan lengkap ke pengguna.
 * 3. Saat tombol "Purchase Insurance" ditekan, memanggil
 *    POST /purchase, lalu redirect ke underwriting.html.
 *
 * CATATAN STATE:
 * Menggunakan localStorage key yang sama dengan index.js
 * ("etiqa_mvi_state") agar data konsisten antar halaman.
 * ============================================================
 */

// ------------------------------------------------------------
// STATE KEYS (localStorage) - harus sama persis dengan index.js
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
const btnPurchase = document.getElementById("btn-purchase");
const btnPurchaseText = document.getElementById("btn-purchase-text");
const btnBackToForm = document.getElementById("btn-back-to-form");

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

// ------------------------------------------------------------
// FORMATTING HELPERS
// ------------------------------------------------------------
/**
 * Format angka menjadi format mata uang Rupiah, contoh: Rp 250.000.000
 */
function formatRupiah(value) {
  const num = Number(value);
  if (isNaN(num)) return "-";
  return "Rp " + num.toLocaleString("id-ID", { maximumFractionDigits: 0 });
}

/**
 * Format rate persen dengan 2 angka desimal, contoh: 2.98%
 */
function formatRate(value) {
  const num = Number(value);
  if (isNaN(num)) return "-";
  return num.toFixed(2) + "%";
}

function vehicleTypeLabel(type) {
  return type === "car" ? "Mobil" : type === "motorcycle" ? "Motor" : "-";
}

// ------------------------------------------------------------
// RENDER SUMMARY
// ------------------------------------------------------------
function renderSummary(state) {
  document.getElementById("summary-customer-name").textContent = state.customerName || "-";
  document.getElementById("summary-customer-email").textContent = state.customerEmail || "-";
  document.getElementById("summary-customer-phone").textContent = state.customerPhone || "-";

  document.getElementById("summary-vehicle-type").textContent = vehicleTypeLabel(state.vehicleType);
  document.getElementById("summary-vehicle-brand-model").textContent =
    [state.vehicleBrand, state.vehicleModel].filter(Boolean).join(" / ") || "-";
  document.getElementById("summary-vehicle-year").textContent = state.vehicleYear || "-";
  document.getElementById("summary-vehicle-value").textContent = formatRupiah(state.vehicleMarketValue);
  document.getElementById("summary-vehicle-region").textContent = state.vehicleRegion || "-";
  document.getElementById("summary-vehicle-category").textContent =
    state.vehicleCategory != null ? `Kategori ${state.vehicleCategory}` : "-";

  document.getElementById("summary-coverage").textContent = state.quoteCoverage || "-";
  document.getElementById("summary-rate").textContent = formatRate(state.quoteRateUsed);
  document.getElementById("summary-premium").textContent = formatRupiah(state.quotePremium);
}

// ------------------------------------------------------------
// INIT PAGE
// ------------------------------------------------------------
(function initPage() {
  const state = getAppState();

  if (!state.quoteId || !state.vehicleId || !state.customerId) {
    showAlert(
      "Data quote tidak ditemukan atau sesi telah berakhir. Silakan mulai pengajuan dari awal."
    );
    btnPurchase.disabled = true;
    return;
  }

  renderSummary(state);
})();

// ------------------------------------------------------------
// NAVIGATION: BACK TO FORM
// ------------------------------------------------------------
btnBackToForm.addEventListener("click", () => {
  window.location.href = "index.html";
});

// ------------------------------------------------------------
// PURCHASE INSURANCE -> POST /purchase -> underwriting.html
// ------------------------------------------------------------
btnPurchase.addEventListener("click", async () => {
  clearAlert();
  const state = getAppState();

  if (!state.quoteId) {
    showAlert("Quote tidak ditemukan. Silakan mulai pengajuan dari awal.");
    return;
  }

  btnPurchase.disabled = true;
  btnPurchaseText.innerHTML = `<span class="loading-spinner"></span> Memproses...`;

  try {
    const result = await EtiqaAPI.purchaseQuote({ quoteId: state.quoteId });

    saveAppState({
      isPurchased: result.is_purchased,
    });

    // Redirect ke halaman Underwriting
    window.location.href = "underwriting.html";
  } catch (err) {
    showAlert(err.message || "Gagal memproses pembelian. Silakan coba lagi.");
    btnPurchase.disabled = false;
    btnPurchaseText.textContent = "Purchase Insurance";
  }
});