"""
Route untuk penerbitan dan pengambilan data Policy.

Endpoint:
- POST /issue-policy             : menerbitkan polis baru (hanya jika underwriting Accepted)
- GET  /policy/{policy_number}   : mengambil detail lengkap suatu polis
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, crud
from app.database import get_db

router = APIRouter(tags=["Policy"])


@router.post(
    "/issue-policy",
    response_model=schemas.PolicyResponse,
    status_code=201,
    summary="Menerbitkan polis baru",
)
def issue_policy(payload: schemas.PolicyIssueRequest, db: Session = Depends(get_db)):
    """
    Menerbitkan polis baru untuk suatu quote.

    Business rule (sesuai alur aplikasi):
    - Polis HANYA bisa diterbitkan jika quote terkait sudah memiliki
      record underwriting dengan decision == "Accepted".
    - Jika decision == "Manual Review", request ditolak dengan pesan
      ramah pengguna yang menjelaskan bahwa kendaraan memerlukan
      review manual dan tidak bisa langsung diterbitkan polisnya.
    - Jika quote belum memiliki underwriting sama sekali, request
      juga ditolak karena melompati alur aplikasi.
    - Satu quote hanya boleh memiliki satu polis (dicegah duplikasi
      penerbitan).

    Nomor polisi digenerate otomatis oleh crud.create_policy()
    menggunakan format ETQ-2026-000001 (lihat utils.generate_policy_number).
    """
    quote = crud.get_quote(db, payload.quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Data quote tidak ditemukan")

    underwriting = crud.get_underwriting_by_quote(db, payload.quote_id)
    if underwriting is None:
        raise HTTPException(
            status_code=400,
            detail="Quote ini belum melalui proses underwriting. Silakan lengkapi underwriting terlebih dahulu",
        )

    if underwriting.decision != "Accepted":
        raise HTTPException(
            status_code=400,
            detail="Pengajuan ini memerlukan review manual dari underwriter dan belum dapat diterbitkan polisnya secara otomatis",
        )

    if quote.policy is not None:
        raise HTTPException(
            status_code=400,
            detail="Polis untuk quote ini sudah pernah diterbitkan sebelumnya",
        )

    policy = crud.create_policy(db, quote_id=payload.quote_id)
    return policy


@router.get(
    "/policy/{policy_number}",
    response_model=schemas.PolicyDetailResponse,
    summary="Mengambil detail lengkap suatu polis",
)
def get_policy_detail(policy_number: str, db: Session = Depends(get_db)):
    """
    Mengambil detail polis lengkap (data customer, vehicle, quote,
    underwriting, dan policy) berdasarkan policy_number, dipakai
    untuk menampilkan halaman policy.html yang bisa di-print.
    """
    detail = crud.get_policy_full_detail(db, policy_number)
    if detail is None:
        raise HTTPException(status_code=404, detail="Nomor polisi tidak ditemukan")

    return schemas.PolicyDetailResponse(**detail)