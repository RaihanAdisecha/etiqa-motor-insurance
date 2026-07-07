"""
Route untuk proses Underwriting.

Endpoint:
- POST /underwriting : mengirim jawaban 3 pertanyaan underwriting
  dan mendapatkan keputusan (Accepted / Manual Review)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, crud
from app.database import get_db

router = APIRouter(tags=["Underwriting"])


@router.post(
    "/underwriting",
    response_model=schemas.UnderwritingResponse,
    status_code=201,
    summary="Mengirim jawaban underwriting dan mendapatkan keputusan",
)
def submit_underwriting(payload: schemas.UnderwritingCreate, db: Session = Depends(get_db)):
    """
    Memproses 3 pertanyaan yes/no underwriting:
    - has_major_accident : kecelakaan besar
    - has_modification   : modifikasi kendaraan
    - is_commercial_use  : pemakaian komersial

    Keputusan (decision) dihitung otomatis di crud.create_underwriting()
    menggunakan business rule evaluate_underwriting() di utils.py:
    - Semua "No" -> "Accepted"
    - Salah satu "Yes" -> "Manual Review"

    Validasi tambahan dilakukan di sini untuk memastikan:
    1. quote_id yang dikirim benar-benar ada
    2. quote tersebut sudah berstatus purchased (pelanggan sudah
       menekan tombol "Purchase Insurance"), sesuai urutan alur
       aplikasi yang benar
    3. belum ada record underwriting sebelumnya untuk quote_id ini
       (mencegah duplikasi submission underwriting untuk quote yang
       sama)
    """
    quote = crud.get_quote(db, payload.quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Data quote tidak ditemukan")

    if not quote.is_purchased:
        raise HTTPException(
            status_code=400,
            detail="Quote ini belum dilanjutkan ke tahap pembelian. Silakan tekan tombol 'Purchase Insurance' terlebih dahulu",
        )

    existing_underwriting = crud.get_underwriting_by_quote(db, payload.quote_id)
    if existing_underwriting is not None:
        raise HTTPException(
            status_code=400,
            detail="Underwriting untuk quote ini sudah pernah diajukan sebelumnya",
        )

    underwriting = crud.create_underwriting(db, payload)
    return underwriting