"""
Data tarif premi asuransi kendaraan bermotor berdasarkan
SEOJK No. 6/SEOJK.05/2017.

PENTING - PENJELASAN PENGGUNAAN MIDPOINT:
Seluruh tarif yang ditetapkan OJK berbentuk RANGE (batas bawah - batas
atas), bukan angka tunggal. Untuk kebutuhan kalkulasi otomatis di
aplikasi ini, kita menggunakan MIDPOINT (nilai tengah) dari setiap
range sebagai rate yang dipakai dalam formula premi.

Alasan penggunaan midpoint (dijelaskan juga di README):
1. OJK memberikan range agar perusahaan asuransi punya fleksibilitas
   dalam penetapan tarif final berdasarkan risk appetite masing-masing.
   Karena aplikasi ini adalah simulasi/technical assessment tanpa
   proses underwriting risk-based yang kompleks, midpoint dipilih
   sebagai pendekatan yang paling netral dan tidak bias ke batas
   bawah (terlalu murah, tidak sustainable) maupun batas atas
   (terlalu mahal, tidak kompetitif).
2. Midpoint merepresentasikan estimasi premi yang wajar dan mudah
   dipertanggungjawabkan secara bisnis maupun akademis dibandingkan
   memilih batas bawah atau batas atas secara sepihak.
3. Pendekatan ini konsisten diterapkan ke seluruh kombinasi kategori,
   region, dan jenis coverage sehingga tidak ada perlakuan khusus
   pada kombinasi tertentu.

Struktur data:
- CAR_COMPREHENSIVE_RATES: dict[kategori][region] -> rate (%)
- CAR_TLO_RATES: dict[kategori][region] -> rate (%)
- MOTORCYCLE_COMPREHENSIVE_RATE: rate tunggal (%), berlaku semua region
- MOTORCYCLE_TLO_RATES: dict[region] -> rate (%)

Semua rate dalam satuan PERSEN (%), sesuai format asli SEOJK.
Formula pemakaian (lihat utils.py):
    Premium = Vehicle Value * rate_used / 100
"""


def _midpoint(low: float, high: float) -> float:
    """
    Helper untuk menghitung midpoint dari sebuah range tarif OJK.
    Dipakai hanya di file ini saat membangun konstanta rate,
    agar sumber angka range asli tetap terlihat jelas dan mudah
    diaudit/diverifikasi terhadap SEOJK No. 6/SEOJK.05/2017.
    """
    return round((low + high) / 2, 4)


# ------------------------------------------------------------------
# CAR - COMPREHENSIVE
# ------------------------------------------------------------------
# Struktur asli range (disimpan sebagai referensi/dokumentasi):
# Kategori 1: Region I 3.82-4.20 | Region II 3.26-3.59 | Region III 2.53-2.78
# Kategori 2: Region I 2.67-2.94 | Region II 2.47-2.72 | Region III 2.69-2.96
# Kategori 3: Region I 2.18-2.40 | Region II 2.08-2.29 | Region III 1.79-1.97
# Kategori 4: Region I 1.20-1.32 | Region II 1.20-1.32 | Region III 1.14-1.25
# Kategori 5: Region I 1.05-1.16 | Region II 1.05-1.16 | Region III 1.05-1.16
CAR_COMPREHENSIVE_RATES = {
    1: {
        "Region I": _midpoint(3.82, 4.20),
        "Region II": _midpoint(3.26, 3.59),
        "Region III": _midpoint(2.53, 2.78),
    },
    2: {
        "Region I": _midpoint(2.67, 2.94),
        "Region II": _midpoint(2.47, 2.72),
        "Region III": _midpoint(2.69, 2.96),
    },
    3: {
        "Region I": _midpoint(2.18, 2.40),
        "Region II": _midpoint(2.08, 2.29),
        "Region III": _midpoint(1.79, 1.97),
    },
    4: {
        "Region I": _midpoint(1.20, 1.32),
        "Region II": _midpoint(1.20, 1.32),
        "Region III": _midpoint(1.14, 1.25),
    },
    5: {
        "Region I": _midpoint(1.05, 1.16),
        "Region II": _midpoint(1.05, 1.16),
        "Region III": _midpoint(1.05, 1.16),
    },
}


# ------------------------------------------------------------------
# CAR - TLO (Total Loss Only)
# ------------------------------------------------------------------
# Struktur asli range (disimpan sebagai referensi/dokumentasi):
# Kategori 1: Region I 0.47-0.56 | Region II 0.65-0.78 | Region III 0.51-0.56
# Kategori 2: Region I 0.63-0.69 | Region II 0.44-0.53 | Region III 0.44-0.48
# Kategori 3: Region I 0.41-0.46 | Region II 0.38-0.42 | Region III 0.29-0.35
# Kategori 4: Region I 0.25-0.30 | Region II 0.25-0.30 | Region III 0.23-0.27
# Kategori 5: Region I 0.20-0.24 | Region II 0.20-0.24 | Region III 0.20-0.24
CAR_TLO_RATES = {
    1: {
        "Region I": _midpoint(0.47, 0.56),
        "Region II": _midpoint(0.65, 0.78),
        "Region III": _midpoint(0.51, 0.56),
    },
    2: {
        "Region I": _midpoint(0.63, 0.69),
        "Region II": _midpoint(0.44, 0.53),
        "Region III": _midpoint(0.44, 0.48),
    },
    3: {
        "Region I": _midpoint(0.41, 0.46),
        "Region II": _midpoint(0.38, 0.42),
        "Region III": _midpoint(0.29, 0.35),
    },
    4: {
        "Region I": _midpoint(0.25, 0.30),
        "Region II": _midpoint(0.25, 0.30),
        "Region III": _midpoint(0.23, 0.27),
    },
    5: {
        "Region I": _midpoint(0.20, 0.24),
        "Region II": _midpoint(0.20, 0.24),
        "Region III": _midpoint(0.20, 0.24),
    },
}


# ------------------------------------------------------------------
# MOTORCYCLE - COMPREHENSIVE
# ------------------------------------------------------------------
# Motor hanya memiliki kategori tunggal (tidak ada kategori 1-5 seperti
# mobil), dan rate comprehensive sama untuk semua region.
# Range asli: 3.18-3.50
MOTORCYCLE_COMPREHENSIVE_RATE = _midpoint(3.18, 3.50)


# ------------------------------------------------------------------
# MOTORCYCLE - TLO
# ------------------------------------------------------------------
# Berbeda dengan comprehensive, TLO motor tetap dibedakan per region.
# Range asli:
# Region I: 1.76-2.11
# Region II: 1.80-2.16
# Region III: 0.67-0.80
MOTORCYCLE_TLO_RATES = {
    "Region I": _midpoint(1.76, 2.11),
    "Region II": _midpoint(1.80, 2.16),
    "Region III": _midpoint(0.67, 0.80),
}


# ------------------------------------------------------------------
# Konstanta pendukung business rule kategori & region
# ------------------------------------------------------------------
# Kategori kendaraan mobil valid (1-5). Digunakan untuk validasi
# input dan dokumentasi business rule penentuan kategori di utils.py.
VALID_CAR_CATEGORIES = [1, 2, 3, 4, 5]

# Region valid yang berlaku untuk seluruh jenis kendaraan.
VALID_REGIONS = ["Region I", "Region II", "Region III"]

# Jenis kendaraan valid sesuai scope aplikasi (OUT OF SCOPE: truk/bus).
VALID_VEHICLE_TYPES = ["car", "motorcycle"]

# Jenis coverage valid.
VALID_COVERAGE_TYPES = ["Comprehensive", "TLO"]