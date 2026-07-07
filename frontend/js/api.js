/**
 * ============================================================
 * api.js
 * ============================================================
 * Layer terpusat untuk seluruh komunikasi dengan backend FastAPI
 * (Etiqa Motor Vehicle Insurance API).
 *
 * Semua halaman (index.js, quote.js, underwriting.js, policy.js)
 * WAJIB memanggil backend melalui fungsi-fungsi di file ini,
 * bukan memanggil fetch() langsung, agar:
 * - Base URL backend hanya perlu diubah di satu tempat
 * - Format request/response konsisten dengan schemas.py backend
 * - Penanganan error konsisten di seluruh aplikasi
 *
 * Konfigurasi:
 * - Saat local development, BASE_URL menunjuk ke uvicorn lokal.
 * - Saat production, BASE_URL diganti ke URL Railway
 *   (lihat instruksi di README.md bagian deployment).
 * ============================================================
 */

// ------------------------------------------------------------
// KONFIGURASI BASE URL
// ------------------------------------------------------------
// GANTI nilai ini dengan URL backend Railway setelah deploy,
// contoh: "https://etiqa-mvi-backend.up.railway.app"
const API_BASE_URL = "etiqa-motor-insurance-production.up.railway.app";

// ------------------------------------------------------------
// ERROR HANDLER TERPUSAT
// ------------------------------------------------------------
/**
 * ApiError: custom error class agar pesan error dari FastAPI
 * (baik 422 validation error maupun HTTPException) bisa
 * ditangkap dan ditampilkan dengan ramah di UI.
 */
class ApiError extends Error {
  constructor(message, status, details) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

/**
 * Mengubah response error FastAPI menjadi pesan yang ramah
 * pengguna.
 *
 * FastAPI mengirim error dalam 2 bentuk utama:
 * 1. HTTPException -> { "detail": "pesan string" }
 * 2. Pydantic validation error (422) ->
 *    { "detail": [ { "loc": [...], "msg": "...", "type": "..." }, ... ] }
 */
function extractErrorMessage(errorBody) {
  if (!errorBody || !errorBody.detail) {
    return "Terjadi kesalahan yang tidak diketahui. Silakan coba lagi.";
  }

  const { detail } = errorBody;

  // Kasus HTTPException biasa (detail berupa string)
  if (typeof detail === "string") {
    return detail;
  }

  // Kasus validation error Pydantic (detail berupa array)
  if (Array.isArray(detail)) {
    return detail
      .map((err) => {
        const field = Array.isArray(err.loc) ? err.loc[err.loc.length - 1] : "field";
        return `${field}: ${err.msg}`;
      })
      .join(" | ");
  }

  return "Terjadi kesalahan yang tidak diketahui. Silakan coba lagi.";
}

/**
 * Wrapper inti untuk seluruh request ke backend.
 * Menangani JSON parsing, error handling, dan network failure
 * secara konsisten untuk semua endpoint.
 */
async function request(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;

  let response;
  try {
    response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });
  } catch (networkError) {
    // Terjadi ketika backend tidak bisa dihubungi sama sekali
    // (misal server down, CORS diblok, atau tidak ada koneksi internet)
    throw new ApiError(
      "Tidak dapat terhubung ke server. Periksa koneksi internet Anda atau coba lagi nanti.",
      0,
      networkError
    );
  }

  // Response tanpa body (jarang terjadi di API ini, tapi dijaga agar aman)
  const isJson = response.headers.get("content-type")?.includes("application/json");
  const body = isJson ? await response.json().catch(() => null) : null;

  if (!response.ok) {
    const message = extractErrorMessage(body);
    throw new ApiError(message, response.status, body);
  }

  return body;
}

// ------------------------------------------------------------
// 1. CUSTOMER
// ------------------------------------------------------------
/**
 * POST /customers
 * payload: { name, email, phone }
 * -> CustomerResponse { id, name, email, phone, created_at }
 */
async function createCustomer({ name, email, phone }) {
  return request("/customers", {
    method: "POST",
    body: JSON.stringify({ name, email, phone }),
  });
}

// ------------------------------------------------------------
// 2. VEHICLE
// ------------------------------------------------------------
/**
 * POST /vehicles
 * payload: { customer_id, vehicle_type, brand, model, year, market_value, region }
 * -> VehicleResponse { id, customer_id, vehicle_type, brand, model, year,
 *                       market_value, region, category, created_at }
 */
async function createVehicle({
  customerId,
  vehicleType,
  brand,
  model,
  year,
  marketValue,
  region,
}) {
  return request("/vehicles", {
    method: "POST",
    body: JSON.stringify({
      customer_id: customerId,
      vehicle_type: vehicleType,
      brand,
      model,
      year,
      market_value: marketValue,
      region,
    }),
  });
}

// ------------------------------------------------------------
// 3. PREMIUM / QUOTE
// ------------------------------------------------------------
/**
 * POST /calculate-premium
 * payload: { vehicle_id, coverage_type }
 * -> PremiumCalculateResponse { quote_id, vehicle_id, category, region,
 *                                coverage, rate_used, premium }
 */
async function calculatePremium({ vehicleId, coverageType }) {
  return request("/calculate-premium", {
    method: "POST",
    body: JSON.stringify({
      vehicle_id: vehicleId,
      coverage_type: coverageType,
    }),
  });
}

/**
 * POST /purchase
 * payload: { quote_id }
 * -> PurchaseResponse { quote_id, is_purchased, message }
 */
async function purchaseQuote({ quoteId }) {
  return request("/purchase", {
    method: "POST",
    body: JSON.stringify({ quote_id: quoteId }),
  });
}

// ------------------------------------------------------------
// 4. UNDERWRITING
// ------------------------------------------------------------
/**
 * POST /underwriting
 * payload: { quote_id, has_major_accident, has_modification, is_commercial_use }
 * -> UnderwritingResponse { id, quote_id, has_major_accident, has_modification,
 *                            is_commercial_use, decision, created_at }
 *
 * decision akan bernilai "Accepted" jika ketiga jawaban "No" (false),
 * selain itu "Manual Review" (lihat business rule di backend/app/utils.py).
 */
async function submitUnderwriting({
  quoteId,
  hasMajorAccident,
  hasModification,
  isCommercialUse,
}) {
  return request("/underwriting", {
    method: "POST",
    body: JSON.stringify({
      quote_id: quoteId,
      has_major_accident: hasMajorAccident,
      has_modification: hasModification,
      is_commercial_use: isCommercialUse,
    }),
  });
}

// ------------------------------------------------------------
// 5. POLICY
// ------------------------------------------------------------
/**
 * POST /issue-policy
 * payload: { quote_id }
 * -> PolicyResponse { id, quote_id, policy_number, issued_at }
 *
 * Hanya berhasil jika underwriting terkait quote_id sudah "Accepted".
 */
async function issuePolicy({ quoteId }) {
  return request("/issue-policy", {
    method: "POST",
    body: JSON.stringify({ quote_id: quoteId }),
  });
}

/**
 * GET /policy/{policy_number}
 * -> PolicyDetailResponse (data lengkap customer, vehicle, quote,
 *                           underwriting, dan policy)
 */
async function getPolicyDetail(policyNumber) {
  return request(`/policy/${encodeURIComponent(policyNumber)}`, {
    method: "GET",
  });
}

// ------------------------------------------------------------
// EXPORT (global object, dipakai tanpa module bundler)
// ------------------------------------------------------------
// Karena project ini pakai Vanilla JS ES6 tanpa build step,
// seluruh fungsi diekspos lewat satu object global `EtiqaAPI`
// supaya gampang dipanggil dari index.js, quote.js, underwriting.js,
// dan policy.js melalui <script src="js/api.js"> yang di-load
// lebih dulu di setiap halaman HTML.
window.EtiqaAPI = {
  ApiError,
  createCustomer,
  createVehicle,
  calculatePremium,
  purchaseQuote,
  submitUnderwriting,
  issuePolicy,
  getPolicyDetail,
};