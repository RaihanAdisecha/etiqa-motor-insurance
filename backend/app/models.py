"""
SQLAlchemy models untuk Motor Vehicle Insurance Web App - Etiqa Insurance Indonesia.

Tabel:
- customers      : data pelanggan
- vehicles       : data kendaraan milik pelanggan
- quotes         : hasil kalkulasi premi (quote) untuk suatu vehicle
- underwriting   : hasil jawaban underwriting question & keputusan
- policies       : polis yang terbit setelah underwriting Accepted

Relasi (foreign key):
customers (1) -> (N) vehicles
vehicles  (1) -> (N) quotes
quotes    (1) -> (1) underwriting
quotes    (1) -> (1) policies

Menggunakan SQLAlchemy 2.x style (Mapped, mapped_column) untuk
type-safety yang lebih baik.
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Customer(Base):
    """
    Tabel customers.

    Menyimpan data dasar pelanggan yang mengajukan asuransi.
    Satu customer bisa memiliki lebih dari satu vehicle (misal
    mengajukan quote untuk beberapa kendaraan berbeda).
    """
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relasi ke vehicles milik customer ini
    vehicles: Mapped[List["Vehicle"]] = relationship(
        "Vehicle", back_populates="customer", cascade="all, delete-orphan"
    )


class Vehicle(Base):
    """
    Tabel vehicles.

    Menyimpan data kendaraan yang diajukan untuk diasuransikan.
    vehicle_type membedakan antara "car" dan "motorcycle" karena
    keduanya memiliki struktur tarif OJK yang berbeda (mobil
    memiliki 5 kategori, motor hanya kategori tunggal).

    category diisi NULL untuk motorcycle karena motor tidak memiliki
    kategori 1-5 seperti mobil (lihat business rule di utils.py).
    """
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)

    vehicle_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "car" | "motorcycle"
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    market_value: Mapped[float] = mapped_column(Float, nullable=False)
    region: Mapped[str] = mapped_column(String(20), nullable=False)  # "Region I" | "Region II" | "Region III"

    # Kategori kendaraan (1-5) khusus untuk mobil. NULL untuk motorcycle.
    # Ditentukan otomatis oleh backend berdasarkan market_value
    # (lihat determine_car_category() di utils.py).
    category: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relasi
    customer: Mapped["Customer"] = relationship("Customer", back_populates="vehicles")
    quotes: Mapped[List["Quote"]] = relationship(
        "Quote", back_populates="vehicle", cascade="all, delete-orphan"
    )


class Quote(Base):
    """
    Tabel quotes.

    Menyimpan hasil kalkulasi premi untuk suatu vehicle. Rate yang
    dipakai (rate_used) adalah midpoint dari range tarif OJK yang
    sesuai dengan kategori, region, dan coverage kendaraan tersebut
    (lihat tariff_data.py).

    is_purchased menandai apakah quote ini sudah dilanjutkan ke
    tahap underwriting (tombol "Purchase Insurance" ditekan).
    """
    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)

    coverage_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "Comprehensive" | "TLO"
    rate_used: Mapped[float] = mapped_column(Float, nullable=False)  # dalam persen (%)
    premium: Mapped[float] = mapped_column(Float, nullable=False)  # hasil kalkulasi akhir

    is_purchased: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relasi
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="quotes")
    underwriting: Mapped[Optional["Underwriting"]] = relationship(
        "Underwriting", back_populates="quote", uselist=False, cascade="all, delete-orphan"
    )
    policy: Mapped[Optional["Policy"]] = relationship(
        "Policy", back_populates="quote", uselist=False, cascade="all, delete-orphan"
    )


class Underwriting(Base):
    """
    Tabel underwriting.

    Menyimpan jawaban 3 pertanyaan underwriting dan keputusan akhir.

    Business rule keputusan (lihat utils.py -> evaluate_underwriting):
    - Jika has_major_accident, has_modification, dan is_commercial_use
      SEMUA bernilai False -> decision = "Accepted"
    - Jika salah satu saja bernilai True -> decision = "Manual Review"
    """
    __tablename__ = "underwriting"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quote_id: Mapped[int] = mapped_column(ForeignKey("quotes.id"), nullable=False, unique=True)

    has_major_accident: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_modification: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_commercial_use: Mapped[bool] = mapped_column(Boolean, nullable=False)

    decision: Mapped[str] = mapped_column(String(20), nullable=False)  # "Accepted" | "Manual Review"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relasi
    quote: Mapped["Quote"] = relationship("Quote", back_populates="underwriting")


class Policy(Base):
    """
    Tabel policies.

    Menyimpan polis yang terbit setelah underwriting berstatus
    "Accepted". policy_number mengikuti format ETQ-2026-000001
    (lihat generate_policy_number() di utils.py).
    """
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quote_id: Mapped[int] = mapped_column(ForeignKey("quotes.id"), nullable=False, unique=True)

    policy_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relasi
    quote: Mapped["Quote"] = relationship("Quote", back_populates="policy")