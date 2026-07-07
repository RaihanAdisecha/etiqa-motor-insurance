/**
 * ============================================================
 * index.js
 * ============================================================
 * Logic untuk halaman index.html:
 * - Landing page
 * - Step 1: Customer Info
 * - Step 2: Vehicle Info
 * - Step 3: Coverage selection -> trigger POST /calculate-premium
 *
 * Setelah premi berhasil dihitung, data quote_id, vehicle_id, dan
 * seluruh data terkait disimpan ke sessionStorage-like in-memory
 * object (lihat catatan di bawah), lalu redirect ke quote.html.
 *
 * CATATAN PENYIMPANAN STATE ANTAR HALAMAN:
 * Karena project ini adalah aplikasi multi-page (bukan SPA),
 * state seperti quote_id perlu dibawa dari index.html ke
 * quote.html, underwriting.html, dan policy.html. Kita
 * menggunakan localStorage browser (bukan browser storage API
 * artifact) untuk keperluan ini, karena ini adalah aplikasi
 * frontend statis biasa (bukan Claude artifact), sehingga
 * localStorage aman dan didukung penuh di Vercel.
 * ============================================================
 */

// ------------------------------------------------------------
// STATE KEYS (localStorage)
// ------------------------------------------------------------
const STORAGE_KEY = "etiqa_mvi_state";

/**
 * Mengambil state aplikasi yang tersimpan di localStorage.
 * Mengembalikan object kosong jika belum ada state sama sekali.
 */
function getAppState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch (e) {
    return {};
  }
}

/**
 * Menyimpan (merge) state aplikasi ke localStorage.
 */
function saveAppState(partialState) {
  const current = getAppState();
  const updated = { ...current, ...partialState };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  return updated;
}

// ------------------------------------------------------------
// DOM ELEMENTS
// ------------------------------------------------------------
const landingSection = document.getElementById("landing-section");
const formSection = document.getElementById("form-section");
const btnStart = document.getElementById("btn-start");

const stepCustomer = document.getElementById("step-customer");
const stepVehicle = document.getElementById("step-vehicle");
const stepCoverage = document.getElementById("step-coverage");

const stepperSteps = document.querySelectorAll(".stepper__step");

const formAlertContainer = document.getElementById("form-alert-container");

// Step 1 fields
const inputName = document.getElementById("customer-name");
const inputEmail = document.getElementById("customer-email");
const inputPhone = document.getElementById("customer-phone");

// Step 2 fields
const optionCar = document.getElementById("option-vehicle-car");
const optionMotorcycle = document.getElementById("option-vehicle-motorcycle");
const inputBrand = document.getElementById("vehicle-brand");
const inputModel = document.getElementById("vehicle-model");
const inputYear = document.getElementById("vehicle-year");
const inputValue = document.getElementById("vehicle-value");
const selectRegion = document.getElementById("vehicle-region");

// Step 3 fields
const optionComprehensive = document.getElementById("option-coverage-comprehensive");
const optionTlo = document.getElementById("option-coverage-tlo");
const btnCalculatePremium = document.getElementById("btn-calculate-premium");
const btnCalculateText = document.getElementById("btn-calculate-text");

// Local (non-persisted) selection state for this page's session
let selectedVehicleType = null;
let selectedCoverageType = null;

// ------------------------------------------------------------
// UTILITY: ALERT / ERROR DISPLAY
// ------------------------------------------------------------
function showAlert(message, type = "danger") {
  formAlertContainer.innerHTML = `<div class="alert alert-${type}">${escapeHtml(message)}</div>`;
}

function clearAlert() {
  formAlertContainer.innerHTML = "";
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

function clearAllFieldErrors(scope) {
  scope.querySelectorAll(".field-error").forEach((el) => el.classList.remove("visible"));
  scope.querySelectorAll("input, select").forEach((el) => el.classList.remove("input-error"));
}

function markInputError(inputEl) {
  if (inputEl) inputEl.classList.add("input-error");
}

// ------------------------------------------------------------
// STEPPER NAVIGATION
// ------------------------------------------------------------
function setActiveStep(stepNumber) {
  stepperSteps.forEach((stepEl) => {
    const num = parseInt(stepEl.dataset.step, 10);
    stepEl.classList.remove("stepper__step--active", "stepper__step--done");
    if (num < stepNumber) {
      stepEl.classList.add("stepper__step--done");
    } else if (num === stepNumber) {
      stepEl.classList.add("stepper__step--active");
    }
  });
}

function showFormStep(stepEl, stepNumber) {
  [stepCustomer, stepVehicle, stepCoverage].forEach((s) => s.classList.add("hidden"));
  stepEl.classList.remove("hidden");
  setActiveStep(stepNumber);
  clearAlert();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ------------------------------------------------------------
// LANDING -> FORM
// ------------------------------------------------------------
btnStart.addEventListener("click", () => {
  landingSection.classList.add("hidden");
  formSection.classList.remove("hidden");
  showFormStep(stepCustomer, 1);
});

// ------------------------------------------------------------
// STEP 1: CUSTOMER INFO VALIDATION
// ------------------------------------------------------------
/**
 * Validasi client-side untuk mengurangi round-trip ke server,
 * meski validasi final tetap dilakukan oleh backend
 * (schemas.CustomerCreate) sebagai source of truth.
 */
function validateCustomerForm() {
  clearAllFieldErrors(stepCustomer);
  let isValid = true;

  const name = inputName.value.trim();
  const email = inputEmail.value.trim();
  const phone = inputPhone.value.trim();

  if (name.length < 2) {
    showFieldError("error-customer-name");
    markInputError(inputName);
    isValid = false;
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    showFieldError("error-customer-email");
    markInputError(inputEmail);
    isValid = false;
  }

  const cleanedPhone = phone.replace(/[\s-]/g, "").replace("+", "");
  if (!/^\d+$/.test(cleanedPhone) || cleanedPhone.length < 8) {
    showFieldError("error-customer-phone");
    markInputError(inputPhone);
    isValid = false;
  }

  return isValid ? { name, email, phone } : null;
}

document.getElementById("btn-to-vehicle").addEventListener("click", async () => {
  const customerData = validateCustomerForm();
  if (!customerData) return;

  const btn = document.getElementById("btn-to-vehicle");
  const originalText = btn.textContent;
  btn.disabled = true;
  btn.innerHTML = `<span class="loading-spinner"></span> Menyimpan...`;

  try {
    const customer = await EtiqaAPI.createCustomer(customerData);
    saveAppState({
      customerId: customer.id,
      customerName: customer.name,
      customerEmail: customer.email,
      customerPhone: customer.phone,
    });
    showFormStep(stepVehicle, 2);
  } catch (err) {
    showAlert(err.message || "Gagal menyimpan data diri. Silakan coba lagi.");
  } finally {
    btn.disabled = false;
    btn.textContent = originalText;
  }
});

// ------------------------------------------------------------
// STEP 2: VEHICLE INFO
// ------------------------------------------------------------
function selectVehicleType(type) {
  selectedVehicleType = type;
  optionCar.classList.toggle("selected", type === "car");
  optionMotorcycle.classList.toggle("selected", type === "motorcycle");
  clearFieldError("error-vehicle-type");
}

optionCar.addEventListener("click", () => selectVehicleType("car"));
optionMotorcycle.addEventListener("click", () => selectVehicleType("motorcycle"));

document.getElementById("btn-back-to-customer").addEventListener("click", () => {
  showFormStep(stepCustomer, 1);
});

function validateVehicleForm() {
  clearAllFieldErrors(stepVehicle);
  let isValid = true;

  if (!selectedVehicleType) {
    showFieldError("error-vehicle-type");
    isValid = false;
  }

  const brand = inputBrand.value.trim();
  if (!brand) {
    showFieldError("error-vehicle-brand");
    markInputError(inputBrand);
    isValid = false;
  }

  const model = inputModel.value.trim();
  if (!model) {
    showFieldError("error-vehicle-model");
    markInputError(inputModel);
    isValid = false;
  }

  const year = parseInt(inputYear.value, 10);
  const currentYear = new Date().getFullYear();
  if (!year || year < 1980 || year > currentYear + 1) {
    showFieldError("error-vehicle-year");
    markInputError(inputYear);
    isValid = false;
  }

  const marketValue = parseFloat(inputValue.value);
  if (!marketValue || marketValue <= 0) {
    showFieldError("error-vehicle-value");
    markInputError(inputValue);
    isValid = false;
  }

  const region = selectRegion.value;
  if (!region) {
    showFieldError("error-vehicle-region");
    markInputError(selectRegion);
    isValid = false;
  }

  if (!isValid) return null;

  return {
    vehicleType: selectedVehicleType,
    brand,
    model,
    year,
    marketValue,
    region,
  };
}

document.getElementById("btn-to-coverage").addEventListener("click", async () => {
  const vehicleData = validateVehicleForm();
  if (!vehicleData) return;

  const state = getAppState();
  if (!state.customerId) {
    showAlert("Sesi data diri tidak ditemukan. Silakan mulai dari awal.");
    return;
  }

  const btn = document.getElementById("btn-to-coverage");
  const originalText = btn.textContent;
  btn.disabled = true;
  btn.innerHTML = `<span class="loading-spinner"></span> Menyimpan...`;

  try {
    const vehicle = await EtiqaAPI.createVehicle({
      customerId: state.customerId,
      ...vehicleData,
    });
    saveAppState({
      vehicleId: vehicle.id,
      vehicleType: vehicle.vehicle_type,
      vehicleBrand: vehicle.brand,
      vehicleModel: vehicle.model,
      vehicleYear: vehicle.year,
      vehicleMarketValue: vehicle.market_value,
      vehicleRegion: vehicle.region,
      vehicleCategory: vehicle.category,
    });
    showFormStep(stepCoverage, 3);
  } catch (err) {
    showAlert(err.message || "Gagal menyimpan data kendaraan. Silakan coba lagi.");
  } finally {
    btn.disabled = false;
    btn.textContent = originalText;
  }
});

// ------------------------------------------------------------
// STEP 3: COVERAGE SELECTION -> CALCULATE PREMIUM
// ------------------------------------------------------------
function selectCoverageType(type) {
  selectedCoverageType = type;
  optionComprehensive.classList.toggle("selected", type === "Comprehensive");
  optionTlo.classList.toggle("selected", type === "TLO");
  clearFieldError("error-coverage-type");
}

optionComprehensive.addEventListener("click", () => selectCoverageType("Comprehensive"));
optionTlo.addEventListener("click", () => selectCoverageType("TLO"));

document.getElementById("btn-back-to-vehicle").addEventListener("click", () => {
  showFormStep(stepVehicle, 2);
});

btnCalculatePremium.addEventListener("click", async () => {
  clearAllFieldErrors(stepCoverage);

  if (!selectedCoverageType) {
    showFieldError("error-coverage-type");
    return;
  }

  const state = getAppState();
  if (!state.vehicleId) {
    showAlert("Sesi data kendaraan tidak ditemukan. Silakan mulai dari awal.");
    return;
  }

  btnCalculatePremium.disabled = true;
  btnCalculateText.innerHTML = `<span class="loading-spinner"></span> Menghitung Premi...`;

  try {
    const quote = await EtiqaAPI.calculatePremium({
      vehicleId: state.vehicleId,
      coverageType: selectedCoverageType,
    });

    saveAppState({
      quoteId: quote.quote_id,
      quoteCategory: quote.category,
      quoteRegion: quote.region,
      quoteCoverage: quote.coverage,
      quoteRateUsed: quote.rate_used,
      quotePremium: quote.premium,
    });

    // Redirect ke halaman Quote Summary
    window.location.href = "quote.html";
  } catch (err) {
    showAlert(err.message || "Gagal menghitung premi. Silakan coba lagi.");
    btnCalculatePremium.disabled = false;
    btnCalculateText.textContent = "Hitung Premi";
  }
});

// ------------------------------------------------------------
// RESET STATE ON FRESH LANDING VISIT
// ------------------------------------------------------------
/**
 * Jika user kembali ke index.html dari awal (bukan via tombol back
 * browser di tengah proses), kita bersihkan state lama supaya tidak
 * tercampur dengan pengajuan baru.
 */
(function initPage() {
  // Hanya reset jika landing section terlihat (state awal halaman).
  if (!landingSection.classList.contains("hidden")) {
    localStorage.removeItem(STORAGE_KEY);
  }
})();