"""
Route untuk resource Customer.

Endpoint:
- POST /customers : membuat data customer baru
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas, crud
from app.database import get_db

router = APIRouter(tags=["Customer"])


@router.post(
    "/customers",
    response_model=schemas.CustomerResponse,
    status_code=201,
    summary="Membuat data customer baru",
)
def create_customer(payload: schemas.CustomerCreate, db: Session = Depends(get_db)):
    """
    Membuat customer baru sebagai langkah pertama alur aplikasi
    (Customer Info: nama, email, telp).

    Validasi email dan phone sudah ditangani otomatis oleh
    schemas.CustomerCreate (lihat schemas.py).
    """
    customer = crud.create_customer(db, payload)
    return customer