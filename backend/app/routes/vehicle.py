"""
Route untuk resource Vehicle.

Endpoint:
- POST /vehicles : membuat data kendaraan baru untuk seorang customer
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, crud
from app.database import get_db

router = APIRouter(tags=["Vehicle"])


@router.post(
    "/vehicles",
    response_model=schemas.VehicleResponse,
    status_code=201,
    summary="Membuat data kendaraan baru",
)
def create_vehicle(payload: schemas.VehicleCreate, db: Session = Depends(get_db)):
    """
    Membuat vehicle baru sebagai langkah kedua alur aplikasi
    (Vehicle Info: tipe, brand, model, tahun, nilai pasar, region).

    Sebelum membuat vehicle, dipastikan customer_id yang dikirim
    memang terdaftar di tabel customers, agar tidak terjadi
    foreign key yang menunjuk ke data yang tidak ada, dengan pesan
    error ramah pengguna jika customer tidak ditemukan.

    Kategori kendaraan (khusus mobil) ditentukan otomatis oleh
    backend di dalam crud.create_vehicle() menggunakan
    determine_car_category(), sehingga frontend TIDAK perlu dan
    TIDAK boleh mengirim field category secara manual.
    """
    customer = crud.get_customer(db, payload.customer_id)
    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Data customer tidak ditemukan. Silakan lengkapi data customer terlebih dahulu",
        )

    vehicle = crud.create_vehicle(db, payload)
    return vehicle