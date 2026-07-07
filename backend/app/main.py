"""
Entry point utama FastAPI untuk Motor Vehicle Insurance Web App -
Etiqa Insurance Indonesia.

File ini bertanggung jawab untuk:
- Membuat instance FastAPI
- Mengatur CORS agar frontend (Vercel) bisa mengakses backend (Railway)
- Membuat seluruh tabel database saat startup (via Base.metadata.create_all)
- Mendaftarkan seluruh router dari routes/
- Menyediakan endpoint root (health check) untuk memastikan API berjalan
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base

# Import seluruh model agar terdaftar di Base.metadata sebelum
# create_all() dipanggil. Tanpa import ini, SQLAlchemy tidak akan
# tahu tabel apa saja yang perlu dibuat.
from app import models  # noqa: F401

from app.routes import customer, vehicle, premium, underwriting, policy


# ----------------------------------------------------------------------
# Inisialisasi FastAPI
# ----------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "REST API untuk Motor Vehicle Insurance Web App Etiqa Insurance "
        "Indonesia. Menyediakan alur lengkap mulai dari data customer, "
        "data kendaraan, kalkulasi premi berdasarkan tarif OJK SEOJK "
        "No. 6/SEOJK.05/2017, underwriting, hingga penerbitan polis."
    ),
)


# ----------------------------------------------------------------------
# CORS Middleware
# ----------------------------------------------------------------------
# Mengizinkan frontend yang di-deploy di Vercel untuk mengakses API
# ini yang di-deploy di Railway. Daftar origin yang diizinkan diatur
# melalui environment variable CORS_ORIGINS (lihat config.py).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------------
# Startup Event: membuat seluruh tabel jika belum ada
# ----------------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    """
    Membuat seluruh tabel (customers, vehicles, quotes, underwriting,
    policies) di database PostgreSQL (Supabase) jika belum ada.

    Menggunakan create_all() yang bersifat idempotent (tidak akan
    menimpa/menghapus tabel yang sudah ada), sehingga aman dipanggil
    setiap kali aplikasi start di Railway.
    """
    Base.metadata.create_all(bind=engine)


# ----------------------------------------------------------------------
# Root / Health Check
# ----------------------------------------------------------------------
@app.get("/", tags=["Health Check"], summary="Health check endpoint")
def read_root():
    """
    Endpoint sederhana untuk memastikan API berjalan, biasa dipakai
    untuk health check dari Railway maupun pengecekan manual.
    """
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# ----------------------------------------------------------------------
# Registrasi Routers
# ----------------------------------------------------------------------
app.include_router(customer.router)
app.include_router(vehicle.router)
app.include_router(premium.router)
app.include_router(underwriting.router)
app.include_router(policy.router)