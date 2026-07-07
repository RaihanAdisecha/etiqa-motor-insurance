"""
Pydantic schemas untuk Motor Vehicle Insurance Web App - Etiqa Insurance Indonesia.

Schema dikelompokkan per domain (customer, vehicle, premium/quote,
underwriting, policy), masing-masing dengan pola:
- *Base   : field bersama
- *Create : payload untuk POST request dari frontend
- *Response / *Out : bentuk data yang dikembalikan ke frontend

Validasi bisnis (email, phone, vehicle value > 0, tahun kendaraan
valid) diterapkan di sini menggunakan Pydantic validators, dengan
pesan error yang ramah pengguna karena akan ditampilkan langsung
di frontend.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator


# ============================================================
# CUSTOMER SCHEMAS
# ============================================================

class CustomerCreate(BaseModel):
    """Payload untuk POST /customers."""
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: str = Field(..., min_length=8, max_length=20)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        """
        Validasi nomor telepon sederhana:
        - Hanya boleh berisi digit, spasi, tanda '+', dan '-'
        - Minimal 8 digit angka
        Pesan error dibuat ramah pengguna agar mudah dipahami saat
        ditampilkan di form frontend.
        """
        cleaned = value.replace(" ", "").replace("-", "")
        if not cleaned.replace("+", "").isdigit():
            raise ValueError("Nomor telepon hanya boleh berisi angka, spasi, '+', dan '-'")
        digits_only = cleaned.replace("+", "")
        if len(digits_only) < 8:
            raise ValueError("Nomor telepon minimal 8 digit angka")
        return value

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Nama tidak boleh kosong")
        return value.strip()


class CustomerResponse(BaseModel):
    """Response untuk data customer."""
    id: int
    name: str
    email: str
    phone: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# VEHICLE SCHEMAS
# ============================================================

class VehicleCreate(BaseModel):
    """Payload untuk POST /vehicles."""
    customer_id: int
    vehicle_type: Literal["car", "motorcycle"]
    brand: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=100)
    year: int
    market_value: float = Field(..., gt=0, description="Nilai pasar kendaraan, harus lebih dari 0")
    region: Literal["Region I", "Region II", "Region III"]

    @field_validator("year")
    @classmethod
    def validate_year(cls, value: int) -> int:
        """
        Validasi tahun kendaraan wajar, yaitu antara 1980 sampai
        tahun berjalan + 1 (mengakomodasi kendaraan indent/inden
        tahun depan). Pesan error ramah pengguna.
        """
        current_year = datetime.now().year
        if value < 1980 or value > current_year + 1:
            raise ValueError(
                f"Tahun kendaraan tidak valid. Masukkan tahun antara 1980 dan {current_year + 1}"
            )
        return value

    @field_validator("market_value")
    @classmethod
    def validate_market_value(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Nilai pasar kendaraan harus lebih besar dari 0")
        return value


class VehicleResponse(BaseModel):
    """Response untuk data vehicle, termasuk category hasil penentuan otomatis backend."""
    id: int
    customer_id: int
    vehicle_type: str
    brand: str
    model: str
    year: int
    market_value: float
    region: str
    category: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# PREMIUM / QUOTE SCHEMAS
# ============================================================

class PremiumCalculateRequest(BaseModel):
    """Payload untuk POST /calculate-premium."""
    vehicle_id: int
    coverage_type: Literal["Comprehensive", "TLO"]


class PremiumCalculateResponse(BaseModel):
    """
    Response WAJIB untuk POST /calculate-premium, mencakup:
    category, region, coverage, rate_used, premium
    (sesuai requirement eksplisit).
    """
    quote_id: int
    vehicle_id: int
    category: Optional[int]
    region: str
    coverage: str
    rate_used: float
    premium: float

    model_config = {"from_attributes": True}


class QuoteResponse(BaseModel):
    """Response umum untuk data quote (dipakai di quote summary)."""
    id: int
    vehicle_id: int
    coverage_type: str
    rate_used: float
    premium: float
    is_purchased: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PurchaseRequest(BaseModel):
    """Payload untuk POST /purchase. Menandai quote sebagai dibeli/dilanjutkan."""
    quote_id: int


class PurchaseResponse(BaseModel):
    """Response setelah quote berhasil ditandai sebagai purchased."""
    quote_id: int
    is_purchased: bool
    message: str


# ============================================================
# UNDERWRITING SCHEMAS
# ============================================================

class UnderwritingCreate(BaseModel):
    """
    Payload untuk POST /underwriting.

    3 pertanyaan yes/no underwriting:
    - has_major_accident : pernah mengalami kecelakaan besar
    - has_modification   : kendaraan mengalami modifikasi
    - is_commercial_use   : kendaraan dipakai untuk keperluan komersial
    """
    quote_id: int
    has_major_accident: bool
    has_modification: bool
    is_commercial_use: bool


class UnderwritingResponse(BaseModel):
    """
    Response hasil underwriting, termasuk decision akhir
    ("Accepted" atau "Manual Review").
    """
    id: int
    quote_id: int
    has_major_accident: bool
    has_modification: bool
    is_commercial_use: bool
    decision: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# POLICY SCHEMAS
# ============================================================

class PolicyIssueRequest(BaseModel):
    """Payload untuk POST /issue-policy."""
    quote_id: int


class PolicyResponse(BaseModel):
    """Response detail polis lengkap, dipakai untuk halaman policy.html (bisa print)."""
    id: int
    quote_id: int
    policy_number: str
    issued_at: datetime

    model_config = {"from_attributes": True}


class PolicyDetailResponse(BaseModel):
    """
    Response detail polis LENGKAP untuk GET /policy/{policy_number},
    menggabungkan data customer, vehicle, quote, underwriting, dan
    policy agar frontend policy.html bisa menampilkan seluruh
    informasi dalam satu kali request.
    """
    policy_number: str
    issued_at: datetime

    # Customer
    customer_name: str
    customer_email: str
    customer_phone: str

    # Vehicle
    vehicle_type: str
    brand: str
    model: str
    year: int
    market_value: float
    region: str
    category: Optional[int]

    # Quote
    coverage_type: str
    rate_used: float
    premium: float

    # Underwriting
    underwriting_decision: str

    model_config = {"from_attributes": True}