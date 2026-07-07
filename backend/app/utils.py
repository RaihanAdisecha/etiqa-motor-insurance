"""
Fungsi-fungsi utility (business logic murni) untuk Motor Vehicle
Insurance Web App - Etiqa Insurance Indonesia.

File ini berisi logic inti yang TIDAK berhubungan langsung dengan
database (murni fungsi Python), agar mudah di-unit-test dan
dipisahkan dari layer CRUD/routes:

- Penentuan kategori kendaraan mobil (1-5) berdasarkan nilai pasar
- Lookup tarif OJK (rate_used) berdasarkan vehicle_type, category,
  region, coverage_type
- Kalkulasi premi
- Evaluasi keputusan underwriting
- Generator nomor polisi format ETQ-2026-000001
"""

from app.config import settings
from app.tariff_data import (
    CAR_COMPREHENSIVE_RATES,
    CAR_TLO_RATES,
    MOTORCYCLE_COMPREHENSIVE_RATE,
    MOTORCYCLE_TLO_RATES,
    VALID_CAR_CATEGORIES,
)


# ------------------------------------------------------------------
# BUSINESS RULE: Penentuan Kategori Kendaraan (khusus mobil)
# ------------------------------------------------------------------
# OJK SEOJK No. 6/SEOJK.05/2017 membagi mobil ke dalam 5 kategori
# berdasarkan nilai pasar kendaraan (Harga Pertanggungan). Karena
# SEOJK tidak menetapkan batas nilai pasar per kategori secara baku
# untuk seluruh jenis kendaraan (tergantung jenis & penggunaan),
# aplikasi ini menggunakan pembagian rentang nilai pasar berikut
# sebagai pendekatan yang wajar dan konsisten untuk keperluan
# simulasi/technical assessment. Aturan ini didokumentasikan juga
# di README agar transparan sebagai asumsi bisnis aplikasi.
#
# Kategori 1: > Rp 800.000.000
# Kategori 2: Rp 400.000.000 - Rp 800.000.000
# Kategori 3: Rp 200.000.000 - Rp 400.000.000
# Kategori 4: Rp 100.000.000 - Rp 200.000.000
# Kategori 5: < Rp 100.000.000
def determine_car_category(market_value: float) -> int:
    """
    Menentukan kategori mobil (1-5) berdasarkan nilai pasar kendaraan.

    Kategori 1 = kendaraan paling mahal (nilai pasar tertinggi),
    Kategori 5 = kendaraan paling murah (nilai pasar terendah).
    Semakin tinggi nilai pasar, semakin tinggi risiko finansial,
    sehingga kategori 1 (termahal) juga memiliki rate comprehensive
    tertinggi sesuai tabel tarif OJK.
    """
    if market_value > 800_000_000:
        return 1
    elif market_value >= 400_000_000:
        return 2
    elif market_value >= 200_000_000:
        return 3
    elif market_value >= 100_000_000:
        return 4
    else:
        return 5


# ------------------------------------------------------------------
# TARIFF LOOKUP
# ------------------------------------------------------------------
def get_rate(
    vehicle_type: str,
    coverage_type: str,
    region: str,
    category: int | None = None,
) -> float:
    """
    Mengambil rate (dalam persen) sesuai kombinasi vehicle_type,
    coverage_type, region, dan category (khusus mobil).

    - Untuk vehicle_type == "car": category WAJIB diisi (1-5),
      rate diambil dari CAR_COMPREHENSIVE_RATES atau CAR_TLO_RATES
      sesuai coverage_type.
    - Untuk vehicle_type == "motorcycle": category diabaikan karena
      motor tidak memiliki kategori 1-5.
        - Comprehensive: rate sama untuk semua region
          (MOTORCYCLE_COMPREHENSIVE_RATE)
        - TLO: rate berbeda per region (MOTORCYCLE_TLO_RATES)

    Raises:
        ValueError: jika kombinasi input tidak valid, dengan pesan
        ramah pengguna untuk ditampilkan di frontend.
    """
    if vehicle_type == "car":
        if category is None or category not in VALID_CAR_CATEGORIES:
            raise ValueError("Kategori kendaraan mobil tidak valid. Kategori harus antara 1 sampai 5")

        if coverage_type == "Comprehensive":
            rate_table = CAR_COMPREHENSIVE_RATES
        elif coverage_type == "TLO":
            rate_table = CAR_TLO_RATES
        else:
            raise ValueError("Jenis coverage tidak valid. Pilih 'Comprehensive' atau 'TLO'")

        try:
            return rate_table[category][region]
        except KeyError:
            raise ValueError(f"Kombinasi kategori {category} dan region '{region}' tidak ditemukan")

    elif vehicle_type == "motorcycle":
        if coverage_type == "Comprehensive":
            return MOTORCYCLE_COMPREHENSIVE_RATE
        elif coverage_type == "TLO":
            try:
                return MOTORCYCLE_TLO_RATES[region]
            except KeyError:
                raise ValueError(f"Region '{region}' tidak ditemukan untuk tarif TLO motor")
        else:
            raise ValueError("Jenis coverage tidak valid. Pilih 'Comprehensive' atau 'TLO'")

    else:
        raise ValueError("Tipe kendaraan tidak valid. Pilih 'car' atau 'motorcycle'")


# ------------------------------------------------------------------
# KALKULASI PREMI
# ------------------------------------------------------------------
def calculate_premium(market_value: float, rate_used: float) -> float:
    """
    Formula resmi kalkulasi premi:
        Premium = Vehicle Value x Rate Terpilih / 100

    rate_used dalam satuan persen (%), sehingga dibagi 100 untuk
    mendapatkan nilai premi dalam satuan Rupiah yang sama dengan
    market_value.

    Hasil dibulatkan ke 2 desimal (representasi Rupiah dengan sen).
    """
    if market_value <= 0:
        raise ValueError("Nilai pasar kendaraan harus lebih besar dari 0")
    premium = market_value * rate_used / 100
    return round(premium, 2)


# ------------------------------------------------------------------
# BUSINESS RULE: Evaluasi Keputusan Underwriting
# ------------------------------------------------------------------
def evaluate_underwriting(
    has_major_accident: bool,
    has_modification: bool,
    is_commercial_use: bool,
) -> str:
    """
    Menentukan keputusan underwriting berdasarkan 3 pertanyaan
    yes/no.

    Business rule:
    - Jika SEMUA jawaban "No" (False) -> decision = "Accepted"
    - Jika SALAH SATU SAJA jawaban "Yes" (True) -> decision = "Manual Review"

    Ini merepresentasikan pendekatan underwriting konservatif standar
    industri asuransi kendaraan bermotor, di mana adanya riwayat
    kecelakaan besar, modifikasi kendaraan, atau penggunaan komersial
    meningkatkan risiko sehingga memerlukan review manual oleh
    underwriter, bukan otomatis diterima.
    """
    if has_major_accident or has_modification or is_commercial_use:
        return "Manual Review"
    return "Accepted"


# ------------------------------------------------------------------
# GENERATOR NOMOR POLISI
# ------------------------------------------------------------------
def generate_policy_number(sequence_number: int) -> str:
    """
    Menghasilkan nomor polisi dengan format:
        ETQ-2026-000001

    Format terdiri dari:
    - Prefix perusahaan (settings.POLICY_NUMBER_PREFIX, default "ETQ")
    - Tahun (settings.POLICY_NUMBER_YEAR, default "2026")
    - Sequence number dengan zero-padding sesuai
      settings.POLICY_NUMBER_SEQUENCE_DIGITS (default 6 digit)

    sequence_number diperoleh dari crud.py, yaitu jumlah polis yang
    sudah pernah diterbitkan sebelumnya ditambah 1, sehingga nomor
    polisi bersifat sequential dan unik.
    """
    padded_sequence = str(sequence_number).zfill(settings.POLICY_NUMBER_SEQUENCE_DIGITS)
    return f"{settings.POLICY_NUMBER_PREFIX}-{settings.POLICY_NUMBER_YEAR}-{padded_sequence}"