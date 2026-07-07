"""
CRUD (Create, Read, Update, Delete) operations untuk Motor Vehicle
Insurance Web App - Etiqa Insurance Indonesia.

File ini menjembatani layer routes (FastAPI endpoints) dengan layer
database (SQLAlchemy models). Setiap fungsi menerima db: Session
sebagai parameter pertama, mengikuti pola dependency injection
FastAPI (lihat database.py -> get_db).

Logic bisnis murni (penentuan kategori, lookup tarif, kalkulasi
premi, evaluasi underwriting, generate nomor polisi) TIDAK ditaruh
di sini, melainkan di utils.py, agar crud.py fokus pada operasi
database saja.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models, schemas
from app.utils import (
    determine_car_category,
    get_rate,
    calculate_premium,
    evaluate_underwriting,
    generate_policy_number,
)


# ============================================================
# CUSTOMER
# ============================================================

def create_customer(db: Session, payload: schemas.CustomerCreate) -> models.Customer:
    """Membuat record customer baru di tabel customers."""
    customer = models.Customer(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def get_customer(db: Session, customer_id: int) -> models.Customer | None:
    """Mengambil satu customer berdasarkan id."""
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()


# ============================================================
# VEHICLE
# ============================================================

def create_vehicle(db: Session, payload: schemas.VehicleCreate) -> models.Vehicle:
    """
    Membuat record vehicle baru.

    Kategori kendaraan (category) hanya ditentukan otomatis untuk
    vehicle_type == "car" menggunakan determine_car_category().
    Untuk motorcycle, category disimpan sebagai None karena motor
    tidak memiliki kategori 1-5 (lihat business rule di utils.py
    dan tariff_data.py).
    """
    category = None
    if payload.vehicle_type == "car":
        category = determine_car_category(payload.market_value)

    vehicle = models.Vehicle(
        customer_id=payload.customer_id,
        vehicle_type=payload.vehicle_type,
        brand=payload.brand,
        model=payload.model,
        year=payload.year,
        market_value=payload.market_value,
        region=payload.region,
        category=category,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


def get_vehicle(db: Session, vehicle_id: int) -> models.Vehicle | None:
    """Mengambil satu vehicle berdasarkan id."""
    return db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()


# ============================================================
# QUOTE / PREMIUM
# ============================================================

def create_quote(
    db: Session,
    vehicle: models.Vehicle,
    coverage_type: str,
) -> models.Quote:
    """
    Membuat quote baru berdasarkan data vehicle dan coverage_type
    yang dipilih.

    Alur:
    1. Lookup rate_used menggunakan get_rate() berdasarkan
       vehicle_type, coverage_type, region, dan category vehicle.
    2. Hitung premium menggunakan calculate_premium().
    3. Simpan hasilnya sebagai record baru di tabel quotes.
    """
    rate_used = get_rate(
        vehicle_type=vehicle.vehicle_type,
        coverage_type=coverage_type,
        region=vehicle.region,
        category=vehicle.category,
    )
    premium = calculate_premium(market_value=vehicle.market_value, rate_used=rate_used)

    quote = models.Quote(
        vehicle_id=vehicle.id,
        coverage_type=coverage_type,
        rate_used=rate_used,
        premium=premium,
        is_purchased=False,
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)
    return quote


def get_quote(db: Session, quote_id: int) -> models.Quote | None:
    """Mengambil satu quote berdasarkan id."""
    return db.query(models.Quote).filter(models.Quote.id == quote_id).first()


def mark_quote_purchased(db: Session, quote: models.Quote) -> models.Quote:
    """
    Menandai quote sebagai purchased (is_purchased = True), dipanggil
    saat pelanggan menekan tombol "Purchase Insurance" pada quote
    summary, sebelum lanjut ke tahap underwriting.
    """
    quote.is_purchased = True
    db.commit()
    db.refresh(quote)
    return quote


# ============================================================
# UNDERWRITING
# ============================================================

def create_underwriting(
    db: Session,
    payload: schemas.UnderwritingCreate,
) -> models.Underwriting:
    """
    Membuat record underwriting baru berdasarkan 3 jawaban yes/no,
    dengan decision dihitung otomatis menggunakan
    evaluate_underwriting() dari utils.py.
    """
    decision = evaluate_underwriting(
        has_major_accident=payload.has_major_accident,
        has_modification=payload.has_modification,
        is_commercial_use=payload.is_commercial_use,
    )

    underwriting = models.Underwriting(
        quote_id=payload.quote_id,
        has_major_accident=payload.has_major_accident,
        has_modification=payload.has_modification,
        is_commercial_use=payload.is_commercial_use,
        decision=decision,
    )
    db.add(underwriting)
    db.commit()
    db.refresh(underwriting)
    return underwriting


def get_underwriting_by_quote(db: Session, quote_id: int) -> models.Underwriting | None:
    """Mengambil record underwriting berdasarkan quote_id terkait."""
    return db.query(models.Underwriting).filter(models.Underwriting.quote_id == quote_id).first()


# ============================================================
# POLICY
# ============================================================

def get_next_policy_sequence(db: Session) -> int:
    """
    Menghitung sequence number berikutnya untuk nomor polisi,
    berdasarkan jumlah total polis yang sudah pernah diterbitkan
    ditambah 1.

    Menggunakan COUNT(*) sederhana yang cukup untuk skala aplikasi
    technical assessment ini. Untuk skala production dengan
    concurrency tinggi, pendekatan ini sebaiknya diganti dengan
    database sequence/auto-increment khusus untuk menghindari race
    condition, hal ini dicatat sebagai catatan Future Work di README.
    """
    total_policies = db.query(func.count(models.Policy.id)).scalar() or 0
    return total_policies + 1


def create_policy(db: Session, quote_id: int) -> models.Policy:
    """
    Menerbitkan polis baru untuk suatu quote yang sudah Accepted
    pada tahap underwriting.

    Nomor polisi digenerate menggunakan generate_policy_number()
    dengan sequence number yang didapat dari get_next_policy_sequence().
    """
    sequence_number = get_next_policy_sequence(db)
    policy_number = generate_policy_number(sequence_number)

    policy = models.Policy(
        quote_id=quote_id,
        policy_number=policy_number,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def get_policy_by_number(db: Session, policy_number: str) -> models.Policy | None:
    """Mengambil satu polis berdasarkan policy_number, dipakai untuk GET /policy/{policy_number}."""
    return db.query(models.Policy).filter(models.Policy.policy_number == policy_number).first()


def get_policy_full_detail(db: Session, policy_number: str) -> dict | None:
    """
    Mengambil detail polis LENGKAP dengan join manual ke customer,
    vehicle, quote, dan underwriting, untuk memenuhi kebutuhan
    schemas.PolicyDetailResponse pada endpoint GET /policy/{policy_number}.

    Mengembalikan dict mentah (bukan model) agar mudah di-mapping
    langsung ke PolicyDetailResponse di layer route.
    """
    policy = get_policy_by_number(db, policy_number)
    if policy is None:
        return None

    quote = policy.quote
    vehicle = quote.vehicle
    customer = vehicle.customer
    underwriting = quote.underwriting

    return {
        "policy_number": policy.policy_number,
        "issued_at": policy.issued_at,
        "customer_name": customer.name,
        "customer_email": customer.email,
        "customer_phone": customer.phone,
        "vehicle_type": vehicle.vehicle_type,
        "brand": vehicle.brand,
        "model": vehicle.model,
        "year": vehicle.year,
        "market_value": vehicle.market_value,
        "region": vehicle.region,
        "category": vehicle.category,
        "coverage_type": quote.coverage_type,
        "rate_used": quote.rate_used,
        "premium": quote.premium,
        "underwriting_decision": underwriting.decision if underwriting else "N/A",
    }