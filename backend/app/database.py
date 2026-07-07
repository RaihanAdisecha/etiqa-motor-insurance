"""
Konfigurasi koneksi database untuk Motor Vehicle Insurance Web App.

File ini bertanggung jawab untuk:
- Membuat SQLAlchemy engine yang terhubung ke PostgreSQL (Supabase)
- Menyediakan SessionLocal untuk membuat session database per-request
- Menyediakan Base class yang akan diwarisi oleh seluruh model di models.py
- Menyediakan dependency get_db() yang dipakai di setiap route FastAPI

Menggunakan SQLAlchemy 2.x style dengan pendekatan declarative base.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings


# ----------------------------------------------------------------------
# Engine
# ----------------------------------------------------------------------
# pool_pre_ping=True penting untuk koneksi ke Supabase karena koneksi
# yang idle terlalu lama bisa terputus dari sisi server. Dengan
# pre_ping, SQLAlchemy akan mengecek koneksi sebelum dipakai dan
# membuat ulang jika sudah mati, sehingga menghindari error
# "connection already closed" saat aplikasi idle lalu dipakai lagi.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# ----------------------------------------------------------------------
# Session
# ----------------------------------------------------------------------
# autocommit=False dan autoflush=False adalah best practice standar
# FastAPI + SQLAlchemy, agar transaksi dikontrol secara eksplisit
# di dalam setiap fungsi CRUD.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ----------------------------------------------------------------------
# Base class untuk seluruh model (customers, vehicles, quotes,
# underwriting, policies) di models.py
# ----------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ----------------------------------------------------------------------
# Dependency injection untuk FastAPI
# ----------------------------------------------------------------------
def get_db():
    """
    Dependency yang menyediakan session database untuk setiap request.

    Session akan otomatis ditutup setelah request selesai diproses,
    baik berhasil maupun terjadi exception, berkat penggunaan
    try/finally.

    Contoh pemakaian di route:
        @router.post("/customers")
        def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()