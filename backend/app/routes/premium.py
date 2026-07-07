"""
Route untuk kalkulasi premi dan pembelian quote.

Endpoint:
- POST /calculate-premium : menghitung premi berdasarkan vehicle_id dan coverage_type
- POST /purchase          : menandai suatu quote sebagai dibeli (lanjut ke underwriting)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, crud
from app.database import get_db

router = APIRouter(tags=["Premium"])


@router.post(
    "/calculate-premium",
    response_model=schemas.PremiumCalculateResponse,
    status_code=201,
    summary="Menghitung premi asuransi kendaraan",
)
def calculate_premium_endpoint(payload: schemas.PremiumCalculateRequest, db: Session = Depends(get_db)):
    """
    Menghitung premi untuk suatu vehicle berdasarkan coverage_type
    yang dipilih (Comprehensive/TLO).

    Response WAJIB mencakup category, region, coverage, rate_used,
    dan premium sesuai requirement, yang dipetakan langsung dari
    hasil crud.create_quote() (yang secara internal memakai
    utils.get_rate() dan utils.calculate_premium()).

    Jika terjadi kombinasi tarif yang tidak valid (misalnya region
    atau kategori tidak dikenali), ValueError dari utils.py akan
    ditangkap dan diteruskan sebagai HTTP 400 dengan pesan yang
    ramah pengguna.
    """
    vehicle = crud.get_vehicle(db, payload.vehicle_id)
    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Data kendaraan tidak ditemukan. Silakan lengkapi data kendaraan terlebih dahulu",
        )

    try:
        quote = crud.create_quote(db, vehicle=vehicle, coverage_type=payload.coverage_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return schemas.PremiumCalculateResponse(
        quote_id=quote.id,
        vehicle_id=vehicle.id,
        category=vehicle.category,
        region=vehicle.region,
        coverage=quote.coverage_type,
        rate_used=quote.rate_used,
        premium=quote.premium,
    )


@router.post(
    "/purchase",
    response_model=schemas.PurchaseResponse,
    summary="Melanjutkan quote ke tahap pembelian (underwriting)",
)
def purchase_quote(payload: schemas.PurchaseRequest, db: Session = Depends(get_db)):
    """
    Menandai quote sebagai purchased, dipicu saat pelanggan menekan
    tombol "Purchase Insurance" pada halaman Quote Summary.

    Setelah ini, alur aplikasi berlanjut ke halaman underwriting.html
    yang akan memanggil POST /underwriting dengan quote_id yang sama.
    """
    quote = crud.get_quote(db, payload.quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Data quote tidak ditemukan")

    updated_quote = crud.mark_quote_purchased(db, quote)

    return schemas.PurchaseResponse(
        quote_id=updated_quote.id,
        is_purchased=updated_quote.is_purchased,
        message="Quote berhasil dilanjutkan ke tahap underwriting",
    )