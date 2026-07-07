"""
Konfigurasi aplikasi untuk Motor Vehicle Insurance Web App - Etiqa Insurance Indonesia.

File ini bertanggung jawab untuk:
- Membaca environment variables (database URL, CORS origins, dsb)
- Menyediakan objek Settings yang dipakai di seluruh aplikasi (database.py, main.py, dsb)

Menggunakan pydantic-settings agar validasi environment variable otomatis
dan mudah di-override saat deployment di Railway.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """
    Kelas konfigurasi utama aplikasi.

    Semua nilai default di sini adalah nilai untuk local development.
    Saat deploy ke Railway, nilai-nilai ini WAJIB di-override melalui
    environment variables yang diset di dashboard Railway.
    """

    # ------------------------------------------------------------------
    # Database (Supabase PostgreSQL)
    # ------------------------------------------------------------------
    # Format koneksi Supabase Postgres:
    # postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/postgres
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/postgres"

    # ------------------------------------------------------------------
    # Aplikasi
    # ------------------------------------------------------------------
    APP_NAME: str = "Etiqa Motor Vehicle Insurance API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    # Daftar origin yang diizinkan mengakses backend.
    # Saat production, isi dengan URL frontend Vercel, contoh:
    # "https://etiqa-mvi-frontend.vercel.app"
    # Untuk local development, default sudah mencakup localhost umum
    # yang dipakai saat membuka file frontend secara langsung atau via
    # live server.
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:3000",
    ]

    # ------------------------------------------------------------------
    # Business Rule: Format Nomor Polisi
    # ------------------------------------------------------------------
    # Prefix dan tahun dipisah agar mudah diubah tiap tahun tanpa
    # mengubah logic generator nomor polisi di utils.py
    POLICY_NUMBER_PREFIX: str = "ETQ"
    POLICY_NUMBER_YEAR: str = "2026"
    # Jumlah digit sequence pada nomor polisi (contoh: 000001 -> 6 digit)
    POLICY_NUMBER_SEQUENCE_DIGITS: int = 6

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Instance settings tunggal (singleton) yang diimpor di seluruh aplikasi.
# Contoh pemakaian di file lain:
#   from app.config import settings
#   settings.DATABASE_URL
settings = Settings()