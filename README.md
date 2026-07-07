# Etiqa Motor Vehicle Insurance Web App

Technical assessment project untuk **Etiqa Insurance Indonesia** — aplikasi
web simulasi pengajuan asuransi kendaraan bermotor (mobil & motor), mulai
dari data diri pelanggan, data kendaraan, pemilihan coverage, kalkulasi
premi otomatis berdasarkan tarif resmi OJK, proses underwriting sederhana,
hingga penerbitan polis yang bisa dicetak.

> **Catatan:** Project ini dibangun murni untuk keperluan technical
> assessment/simulasi. Lihat bagian **[8. Out of Scope & Future Work](#8-out-of-scope--future-work)**
> untuk batasan-batasan yang disengaja tidak diimplementasikan.

---

## Daftar Isi

1. [Overview Alur Aplikasi](#1-overview-alur-aplikasi)
2. [Tech Stack](#2-tech-stack)
3. [Arsitektur Sistem](#3-arsitektur-sistem)
4. [Struktur Folder](#4-struktur-folder)
5. [Skema Database (PostgreSQL)](#5-skema-database-postgresql)
6. [Tarif Premi — OJK SEOJK No. 6/SEOJK.05/2017](#6-tarif-premi--ojk-seojk-no-6seojk052017)
7. [Endpoint FastAPI (Ringkasan)](#7-endpoint-fastapi-ringkasan)
8. [Out of Scope & Future Work](#8-out-of-scope--future-work)
9. [Menjalankan Backend & Frontend Secara Lokal](#9-menjalankan-backend--frontend-secara-lokal)
10. [Deploy ke Railway (Backend) & Vercel (Frontend)](#10-deploy-backend-ke-railway)
11. [Ringkasan Checklist Deployment](#11-ringkasan-checklist-deployment)

---

## 1. Overview Alur Aplikasi

```
Landing (index.html)
        │
        ▼
Customer Info (nama, email, telepon)
        │
        ▼
Vehicle Info (tipe: car/motorcycle, brand, model, tahun,
               nilai pasar, region: Region I/II/III)
        │
        ▼
Coverage (Comprehensive / TLO)
        │
        ▼
Kalkulasi Premi (mengikuti SEOJK No. 6/SEOJK.05/2017)
        │
        ▼
Quote Summary (quote.html)
        │
        ▼  [tombol "Purchase Insurance"]
        │
Underwriting (underwriting.html)
3 pertanyaan Yes/No:
  - Pernah kecelakaan besar?
  - Ada modifikasi dari standar pabrik?
  - Dipakai untuk keperluan komersial?
        │
        ├── Semua jawaban "Tidak" ──► Accepted
        │                                  │
        │                                  ▼
        │                         Policy Issued (policy.html)
        │                         - generate nomor polisi ETQ-2026-000001
        │                         - tampilkan detail lengkap
        │                         - bisa di-print
        │
        └── Salah satu jawaban "Ya" ──► Manual Review (tidak lanjut ke polis)
```

Alur ini terdiri dari 6 langkah utama yang direpresentasikan sebagai
**progress stepper** di setiap halaman: **Data Diri → Kendaraan →
Coverage → Quote → Underwriting → Polis**.

---

## 2. Tech Stack

| Layer      | Teknologi                                                          |
|------------|---------------------------------------------------------------------|
| Frontend   | HTML5, CSS3, Vanilla JavaScript (ES6) — tanpa framework/build step |
| Backend    | Python 3.12, FastAPI, SQLAlchemy (ORM), Pydantic (validasi), Uvicorn (ASGI server) |
| Database   | PostgreSQL, di-hosting via **Supabase**                             |
| Deployment | Frontend → **Vercel** · Backend → **Railway** · Database → **Supabase** |

---

## 3. Arsitektur Sistem

```
┌───────────────────────┐        HTTPS / JSON        ┌───────────────────────┐
│   Frontend (Vercel)   │  ────────────────────────►  │   Backend (Railway)  │
│   HTML + CSS + JS     │  ◄────────────────────────  │   FastAPI + Uvicorn  │
│   (Vanilla, no build) │                              │                       │
└───────────────────────┘                              └───────────┬───────────┘
                                                                     │ SQLAlchemy
                                                                     │ (psycopg2)
                                                                     ▼
                                                          ┌───────────────────────┐
                                                          │     PostgreSQL        │
                                                          │     (Supabase)        │
                                                          └───────────────────────┘
```

- **Frontend** murni statis (HTML/CSS/JS tanpa build step) sehingga bisa
  langsung di-deploy ke Vercel sebagai static site.
- **Backend** REST API menggunakan FastAPI; seluruh business logic
  (kalkulasi premi, underwriting, generate nomor polis) berada di layer
  backend — frontend hanya mengonsumsi API dan menampilkan hasil.
- **Database** menggunakan PostgreSQL yang di-hosting Supabase; backend
  terhubung menggunakan connection string standar PostgreSQL (bukan
  Supabase client SDK), sehingga SQLAlchemy dapat digunakan seperti pada
  PostgreSQL biasa.
- State sementara antar halaman (misalnya `customer_id`, `vehicle_id`,
  `quote_id`) disimpan di `localStorage` browser (key: `etiqa_mvi_state`)
  karena aplikasi ini tidak menggunakan session/authentication server-side.

---

## 4. Struktur Folder

```
project/
├── frontend/
│   ├── index.html            # Landing + form Customer & Vehicle Info
│   ├── quote.html             # Quote Summary + tombol Purchase Insurance
│   ├── underwriting.html      # 3 pertanyaan underwriting
│   ├── policy.html            # Halaman Policy Issued (printable)
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── api.js             # Layer terpusat pemanggilan backend
│   │   ├── index.js
│   │   ├── quote.js
│   │   ├── underwriting.js
│   │   └── policy.js
│   └── assets/
│
├── backend/
│   ├── app/
│   │   ├── main.py            # Entry point FastAPI, CORS, router registration
│   │   ├── database.py        # SQLAlchemy engine, session, Base
│   │   ├── models.py          # SQLAlchemy ORM models (5 tabel)
│   │   ├── schemas.py         # Pydantic request/response schemas
│   │   ├── crud.py            # Fungsi akses database (create/read)
│   │   ├── config.py          # Pydantic Settings (env variables)
│   │   ├── utils.py           # Business logic murni (kategori, tarif, premi, underwriting, nomor polis)
│   │   ├── tariff_data.py     # Konstanta tarif OJK (midpoint dari range resmi)
│   │   └── routes/
│   │       ├── customer.py     # POST /customers
│   │       ├── vehicle.py      # POST /vehicles
│   │       ├── premium.py      # POST /calculate-premium, POST /purchase
│   │       ├── underwriting.py # POST /underwriting
│   │       └── policy.py       # POST /issue-policy, GET /policy/{policy_number}
│   ├── requirements.txt
│   ├── .env.example
│   ├── Procfile                # Start command untuk Railway
│   └── railway.json            # Konfigurasi Nixpacks + start command Railway
│
└── README.md
```

---

## 5. Skema Database (PostgreSQL)

Lima tabel utama, mengikuti urutan alur aplikasi:

### `customers`

| Kolom       | Tipe        | Keterangan                        |
|-------------|-------------|------------------------------------|
| id          | Integer, PK | Auto increment                    |
| name        | String      | Nama lengkap pelanggan             |
| email       | String      | Divalidasi format email           |
| phone       | String      | Divalidasi format nomor telepon   |
| created_at  | Timestamp   | Default: waktu insert              |

### `vehicles`

| Kolom          | Tipe               | Keterangan                                        |
|----------------|--------------------|------------------------------------------------------|
| id             | Integer, PK        | Auto increment                                        |
| customer_id    | Integer, FK        | Referensi ke `customers.id`                           |
| vehicle_type   | String             | `"car"` atau `"motorcycle"`                           |
| brand          | String             | Merek kendaraan                                       |
| model          | String             | Model kendaraan                                       |
| year           | Integer            | Tahun kendaraan (divalidasi rentang wajar)             |
| market_value   | Float              | Nilai pasar kendaraan (Rupiah)                         |
| region         | String             | `"Region I"`, `"Region II"`, atau `"Region III"`       |
| category       | Integer, nullable  | 1–5, khusus mobil (lihat bagian 6); `NULL` untuk motor |
| created_at     | Timestamp          | Default: waktu insert                                  |

### `quotes`

| Kolom          | Tipe        | Keterangan                                              |
|----------------|-------------|------------------------------------------------------------|
| id             | Integer, PK | Auto increment                                              |
| vehicle_id     | Integer, FK | Referensi ke `vehicles.id`                                  |
| coverage_type  | String      | `"Comprehensive"` atau `"TLO"`                              |
| rate_used      | Float       | Rate midpoint (%) yang dipakai dalam kalkulasi              |
| premium        | Float       | Hasil kalkulasi premi (Rupiah)                              |
| is_purchased   | Boolean     | Default `false`, menjadi `true` setelah `POST /purchase`   |
| created_at     | Timestamp   | Default: waktu insert                                        |

### `underwriting`

| Kolom               | Tipe        | Keterangan                                                       |
|---------------------|-------------|---------------------------------------------------------------------|
| id                  | Integer, PK | Auto increment                                                      |
| quote_id            | Integer, FK | Referensi ke `quotes.id` (unique — satu quote satu underwriting)    |
| has_major_accident  | Boolean     | Jawaban pertanyaan 1                                                |
| has_modification    | Boolean     | Jawaban pertanyaan 2                                                |
| is_commercial_use   | Boolean     | Jawaban pertanyaan 3                                                |
| decision            | String      | `"Accepted"` atau `"Manual Review"`                                 |
| created_at          | Timestamp   | Default: waktu insert                                                |

### `policies`

| Kolom          | Tipe        | Keterangan                                              |
|----------------|-------------|--------------------------------------------------------------|
| id             | Integer, PK | Auto increment                                                |
| quote_id       | Integer, FK | Referensi ke `quotes.id` (unique — satu quote satu polis)    |
| policy_number  | String      | Format `ETQ-2026-000001`, unique, auto-generated             |
| issued_at      | Timestamp   | Default: waktu insert                                          |

**Relasi:** `customers (1) → (N) vehicles → (N) quotes → (1) underwriting`,
`quotes (1) → (1) policies`.

---

## 6. Tarif Premi — OJK SEOJK No. 6/SEOJK.05/2017

Seluruh tarif resmi OJK berbentuk **range** (batas bawah – batas atas),
bukan angka tunggal. Aplikasi ini menggunakan **midpoint** (nilai tengah)
dari setiap range sebagai `rate_used` dalam kalkulasi premi.

### Kenapa Midpoint?

1. **Netral, tidak bias.** OJK memberi range agar perusahaan asuransi
   punya fleksibilitas menetapkan tarif final sesuai risk appetite
   masing-masing. Karena aplikasi ini adalah simulasi tanpa proses
   underwriting risk-based yang kompleks, midpoint adalah pendekatan
   paling netral — tidak condong ke batas bawah (terlalu murah, tidak
   sustainable secara bisnis) maupun batas atas (terlalu mahal, tidak
   kompetitif).
2. **Mudah dipertanggungjawabkan.** Midpoint merepresentasikan estimasi
   premi yang wajar dan bisa dijelaskan secara bisnis maupun akademis,
   dibandingkan memilih ujung range secara sepihak tanpa justifikasi.
3. **Konsisten.** Pendekatan yang sama diterapkan ke seluruh kombinasi
   kategori, region, dan jenis coverage — tidak ada perlakuan khusus.

**Formula:**

```
Premium = Vehicle Value × Rate Terpilih (midpoint) / 100
```

Konstanta rate (hasil midpoint) disimpan di `backend/app/tariff_data.py`.

### 6.1 Penentuan Kategori Mobil (khusus `vehicle_type = "car"`)

SEOJK tidak menetapkan batas nilai pasar per kategori secara baku untuk
semua jenis kendaraan, sehingga aplikasi ini menggunakan pembagian
rentang nilai pasar berikut sebagai **asumsi bisnis** yang wajar dan
konsisten untuk keperluan simulasi (lihat `backend/app/utils.py`,
fungsi `determine_car_category`):

| Kategori | Rentang Nilai Pasar               |
|----------|-------------------------------------|
| 1        | > Rp 800.000.000                    |
| 2        | Rp 400.000.000 – Rp 800.000.000      |
| 3        | Rp 200.000.000 – Rp 400.000.000      |
| 4        | Rp 100.000.000 – Rp 200.000.000      |
| 5        | < Rp 100.000.000                    |

Motor **tidak** memiliki kategori 1–5 (kategori tunggal).

### 6.2 Tabel Tarif CAR — Comprehensive (%)

| Kategori | Region I    | Region II   | Region III  | Midpoint I | Midpoint II | Midpoint III |
|----------|-------------|-------------|-------------|------------|-------------|--------------|
| 1        | 3.82–4.20   | 3.26–3.59   | 2.53–2.78   | 4.01       | 3.425       | 2.655        |
| 2        | 2.67–2.94   | 2.47–2.72   | 2.69–2.96   | 2.805      | 2.595       | 2.825        |
| 3        | 2.18–2.40   | 2.08–2.29   | 1.79–1.97   | 2.29       | 2.185       | 1.88         |
| 4        | 1.20–1.32   | 1.20–1.32   | 1.14–1.25   | 1.26       | 1.26        | 1.195        |
| 5        | 1.05–1.16   | 1.05–1.16   | 1.05–1.16   | 1.105      | 1.105       | 1.105        |

### 6.3 Tabel Tarif CAR — TLO (Total Loss Only) (%)

| Kategori | Region I    | Region II   | Region III  | Midpoint I | Midpoint II | Midpoint III |
|----------|-------------|-------------|-------------|------------|-------------|--------------|
| 1        | 0.47–0.56   | 0.65–0.78   | 0.51–0.56   | 0.515      | 0.715       | 0.535        |
| 2        | 0.63–0.69   | 0.44–0.53   | 0.44–0.48   | 0.66       | 0.485       | 0.46         |
| 3        | 0.41–0.46   | 0.38–0.42   | 0.29–0.35   | 0.435      | 0.40        | 0.32         |
| 4        | 0.25–0.30   | 0.25–0.30   | 0.23–0.27   | 0.275      | 0.275       | 0.25         |
| 5        | 0.20–0.24   | 0.20–0.24   | 0.20–0.24   | 0.22       | 0.22        | 0.22         |

### 6.4 Tabel Tarif MOTORCYCLE (%)

| Coverage      | Region I                        | Region II                       | Region III                      |
|---------------|----------------------------------|-----------------------------------|-----------------------------------|
| Comprehensive | 3.18–3.50 → midpoint **3.34** (sama semua region) | idem | idem |
| TLO           | 1.76–2.11 → midpoint **1.935**  | 1.80–2.16 → midpoint **1.98**    | 0.67–0.80 → midpoint **0.735**   |

> Motor tidak memiliki kategori 1–5; comprehensive motor memiliki rate
> yang sama untuk seluruh region.

---

## 7. Endpoint FastAPI (Ringkasan)

| Method | Endpoint                  | Deskripsi                                                          |
|--------|-----------------------------|------------------------------------------------------------------------|
| POST   | `/customers`               | Membuat data pelanggan baru                                            |
| POST   | `/vehicles`                | Membuat data kendaraan baru                                            |
| POST   | `/calculate-premium`       | Menghitung premi (return `category`, `region`, `coverage`, `rate_used`, `premium`) |
| POST   | `/purchase`                 | Menandai quote sebagai dibeli                                          |
| POST   | `/underwriting`             | Mengirim jawaban underwriting, mengembalikan `decision`                |
| POST   | `/issue-policy`             | Menerbitkan polis (hanya jika underwriting `Accepted`)                 |
| GET    | `/policy/{policy_number}`   | Mengambil detail lengkap polis                                          |

Detail request/response lengkap ada di `backend/app/schemas.py` dan
dokumentasi interaktif otomatis FastAPI di `/docs` setelah backend
dijalankan.

---

## 8. Out of Scope & Future Work

Fitur berikut **sengaja tidak diimplementasikan** dalam technical
assessment ini, namun dicatat sebagai *future work* jika project ini
dikembangkan lebih lanjut untuk kebutuhan produksi:

- **Payment gateway asli** — pembelian saat ini hanya menandai status
  `is_purchased = true` tanpa integrasi payment gateway (Midtrans, Xendit, dll).
- **Authentication multi-user** — tidak ada sistem login/registrasi;
  aplikasi bersifat single-session per browser (menggunakan `localStorage`).
- **Kendaraan komersial/truk/bus** — tarif dan kalkulasi hanya mencakup
  mobil pribadi dan motor sesuai SEOJK yang dirujuk.
- **Add-on coverage** — perluasan jaminan seperti banjir, gempa bumi,
  Third Party Liability (TPL), dan Personal Accident belum tersedia;
  saat ini hanya Comprehensive dan TLO dasar.

---

## 9. Menjalankan Backend & Frontend Secara Lokal

### 9.1 Prasyarat

- Python **3.12** atau lebih baru
- `pip` (atau `pip3`)
- Akun [Supabase](https://supabase.com) (gratis) untuk database PostgreSQL
- Git (opsional, untuk clone repository)

### 9.2 Setup Database di Supabase

1. Buka [supabase.com](https://supabase.com) dan login/daftar.
2. Klik **New Project**, isi nama project (misalnya `etiqa-mvi`), buat
   password database yang kuat (**catat password ini**, hanya muncul
   sekali), pilih region terdekat (misalnya Singapore), lalu klik
   **Create new project**. Tunggu beberapa menit hingga project selesai
   diprovisi.
3. Setelah project aktif, buka **Project Settings** (ikon gear) →
   **Database**.
4. Pada bagian **Connection string**, pilih tab **URI**. Salin
   connection string yang formatnya seperti berikut:

   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxx.supabase.co:5432/postgres
   ```

5. Ganti `[YOUR-PASSWORD]` dengan password yang dibuat di langkah 2.
   Connection string inilah yang akan diisi ke variabel `DATABASE_URL`.

> **Catatan:** Aplikasi ini terhubung ke Supabase menggunakan connection
> string PostgreSQL standar melalui SQLAlchemy + `psycopg2`, **bukan**
> melalui Supabase client SDK (`supabase-py`). Tabel akan otomatis dibuat
> oleh backend saat pertama kali dijalankan (lihat bagian 9.6), sehingga
> **tidak perlu** membuat tabel manual lewat Supabase Table Editor atau
> SQL Editor.

### 9.3 Clone / Buka Folder Project

```bash
cd project/backend
```

### 9.4 Buat Virtual Environment & Install Dependencies

```bash
# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install seluruh dependencies
pip install -r requirements.txt
```

Daftar dependencies utama (`requirements.txt`):

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
sqlalchemy==2.0.30
pydantic==2.7.1
pydantic-settings==2.2.1
email-validator==2.1.1
psycopg2-binary==2.9.9
python-dotenv==1.0.1
```

### 9.5 Konfigurasi Environment Variables

1. Salin `.env.example` menjadi `.env`:

   ```bash
   # macOS/Linux
   cp .env.example .env

   # Windows (Command Prompt)
   copy .env.example .env
   ```

2. Buka file `.env` dan isi `DATABASE_URL` dengan connection string
   Supabase dari langkah 9.2:

   ```env
   DATABASE_URL=postgresql://postgres:password_anda@db.xxxxxxxxxxxx.supabase.co:5432/postgres
   ```

3. Variabel lain (`APP_NAME`, `CORS_ORIGINS`, `POLICY_NUMBER_PREFIX`, dst)
   sudah memiliki nilai default yang sesuai untuk local development —
   tidak wajib diubah kecuali diperlukan. Lihat penjelasan tiap variabel
   di `backend/.env.example`.

### 9.6 Menjalankan Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Flag `--reload` membuat server otomatis restart saat ada perubahan kode
  (berguna untuk development, **jangan** dipakai di production).
- Saat pertama kali dijalankan, backend akan otomatis membuat seluruh
  tabel (`customers`, `vehicles`, `quotes`, `underwriting`, `policies`)
  di database Supabase melalui `Base.metadata.create_all()` — proses ini
  bersifat idempotent (aman dijalankan berkali-kali, tidak akan
  menduplikasi tabel yang sudah ada).

### 9.7 Verifikasi Backend Berjalan

Buka browser ke:

- **Root check:** `http://127.0.0.1:8000/` — harus menampilkan pesan
  status aplikasi.
- **Dokumentasi interaktif (Swagger UI):** `http://127.0.0.1:8000/docs`
  — di sini seluruh endpoint (`/customers`, `/vehicles`,
  `/calculate-premium`, `/purchase`, `/underwriting`, `/issue-policy`,
  `/policy/{policy_number}`) bisa dicoba langsung dari browser tanpa
  perlu frontend.

Jika halaman `/docs` berhasil menampilkan seluruh endpoint di atas,
berarti backend sudah terhubung dengan benar ke database Supabase dan
siap digunakan.

### 9.8 Menjalankan Frontend Secara Lokal

Karena frontend adalah HTML/CSS/JS statis tanpa build step, cukup buka
file `frontend/index.html` langsung di browser, **atau** gunakan live
server sederhana agar path relatif (CSS/JS) lebih konsisten:

```bash
cd project/frontend

# Menggunakan Python (built-in, tidak perlu install apapun)
python -m http.server 5500
```

Lalu buka `http://127.0.0.1:5500/index.html` di browser.

> **Penting:** Pastikan `API_BASE_URL` di `frontend/js/api.js` mengarah
> ke `http://127.0.0.1:8000` (default) saat development lokal, dan origin
> yang dipakai (misalnya `http://127.0.0.1:5500`) sudah terdaftar di
> `CORS_ORIGINS` pada `.env` backend — default `.env.example` sudah
> mencakup port-port umum ini.

### 9.9 Troubleshooting Umum

| Masalah                                               | Solusi                                                                          |
|----------------------------------------------------------|--------------------------------------------------------------------------------|
| `could not connect to server` / connection timeout       | Pastikan `DATABASE_URL` benar dan password tidak mengandung karakter yang perlu di-escape; cek status project di dashboard Supabase |
| `CORS policy` error di browser console                    | Tambahkan origin frontend (misal `http://127.0.0.1:5500`) ke `CORS_ORIGINS` di `.env`, lalu restart server |
| `psycopg2.OperationalError: SSL connection required`      | Supabase mewajibkan SSL; tambahkan `?sslmode=require` di akhir `DATABASE_URL` jika error ini muncul |
| Perubahan `.env` tidak terbaca                              | Restart proses `uvicorn` — environment variable hanya dibaca saat startup      |

---

## 10. Deploy Backend ke Railway

### 10.1 Persiapan

Pastikan `backend/Procfile` dan `backend/railway.json` sudah ada di
repository (keduanya sudah disiapkan di project ini):

**`backend/Procfile`**

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**`backend/railway.json`**

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

Railway menggunakan **Nixpacks** sebagai builder otomatis yang mendeteksi
`requirements.txt` dan menjalankan `pip install` tanpa konfigurasi
tambahan. Variabel `$PORT` disediakan otomatis oleh Railway saat runtime
— **jangan** di-hardcode ke port tertentu (misalnya `8000`) di
Procfile/railway.json.

### 10.2 Push Project ke GitHub

Jika project belum ada di GitHub:

```bash
cd project
git init
git add .
git commit -m "Initial commit - Etiqa MVI project"
git branch -M main
git remote add origin https://github.com/username/etiqa-mvi.git
git push -u origin main
```

### 10.3 Connect GitHub ke Railway

1. Buka [railway.app](https://railway.app) dan login (bisa menggunakan
   akun GitHub).
2. Klik **New Project** → pilih **Deploy from GitHub repo**.
3. Pilih repository project ini. Jika repo belum muncul, klik
   **Configure GitHub App** untuk memberi Railway akses ke repository
   tersebut.
4. Karena struktur project ini adalah monorepo (`frontend/` dan
   `backend/` dalam satu repo), setelah project dibuat:
   - Buka tab **Settings** pada service yang dibuat Railway.
   - Cari bagian **Root Directory**, isi dengan `backend` — ini
     memberi tahu Railway bahwa seluruh build & deploy hanya
     mengacu ke folder `backend/`, bukan root repo.

### 10.4 Konfigurasi Environment Variables di Railway

1. Pada service backend di Railway, buka tab **Variables**.
2. Tambahkan seluruh environment variable berikut (nilai sama seperti
   `.env` lokal, tapi `DATABASE_URL` dan `CORS_ORIGINS` disesuaikan untuk
   production):

   | Key                              | Value                                                          |
   |-----------------------------------|-----------------------------------------------------------------|
   | `DATABASE_URL`                    | Connection string Supabase (sama seperti bagian 9.2)            |
   | `APP_NAME`                        | `Etiqa Motor Vehicle Insurance API`                              |
   | `APP_VERSION`                     | `1.0.0`                                                          |
   | `DEBUG`                           | `False`                                                          |
   | `CORS_ORIGINS`                    | `["https://nama-project-anda.vercel.app"]` (isi setelah frontend di-deploy ke Vercel, lihat bagian 10.6) |
   | `POLICY_NUMBER_PREFIX`            | `ETQ`                                                            |
   | `POLICY_NUMBER_YEAR`              | `2026`                                                           |
   | `POLICY_NUMBER_SEQUENCE_DIGITS`   | `6`                                                               |

3. Klik **Deploy** (atau Railway akan otomatis redeploy setiap kali ada
   perubahan pada `Variables`).

### 10.5 Mendapatkan URL Railway

1. Setelah deployment sukses (cek tab **Deployments**, status harus
   **Success**), buka tab **Settings** pada service.
2. Pada bagian **Networking**, klik **Generate Domain** untuk
   mendapatkan URL publik, formatnya seperti:

   ```
   https://etiqa-mvi-backend-production.up.railway.app
   ```

3. Verifikasi backend berjalan dengan membuka:

   ```
   https://etiqa-mvi-backend-production.up.railway.app/docs
   ```

   Halaman Swagger UI harus muncul dengan seluruh endpoint yang sama
   seperti saat local development.

### 10.6 Menghubungkan Frontend (Vercel) ke Backend (Railway)

1. Buka `frontend/js/api.js`.
2. Ubah nilai `API_BASE_URL` dari URL lokal menjadi URL Railway dari
   langkah 10.5:

   ```javascript
   // Sebelum (local development):
   const API_BASE_URL = "http://127.0.0.1:8000";

   // Sesudah (production):
   const API_BASE_URL = "https://etiqa-mvi-backend-production.up.railway.app";
   ```

3. Commit & push perubahan ini ke GitHub — jika frontend sudah
   terhubung ke Vercel (lihat bagian 10.7), Vercel akan otomatis
   redeploy dengan `API_BASE_URL` yang baru.

### 10.7 Deploy Frontend ke Vercel

1. Buka [vercel.com](https://vercel.com) dan login (bisa menggunakan
   akun GitHub).
2. Klik **Add New** → **Project**, pilih repository project ini.
3. Pada konfigurasi project:
   - **Root Directory**: pilih/isi `frontend` (karena frontend berada
     di subfolder, bukan root repo).
   - **Framework Preset**: pilih **Other** (karena ini static
     HTML/CSS/JS tanpa framework/build step).
   - **Build Command**: kosongkan (tidak diperlukan).
   - **Output Directory**: kosongkan atau isi `.` (root dari
     `frontend/`).
4. Klik **Deploy**. Setelah selesai, Vercel akan memberikan URL seperti:

   ```
   https://etiqa-mvi-frontend.vercel.app
   ```

### 10.8 Konfigurasi CORS (Langkah Terakhir)

Setelah frontend memiliki URL Vercel yang final:

1. Kembali ke dashboard **Railway** → tab **Variables** pada service
   backend.
2. Update `CORS_ORIGINS` dengan URL Vercel yang sebenarnya:

   ```
   CORS_ORIGINS=["https://etiqa-mvi-frontend.vercel.app"]
   ```

   Jika ada custom domain atau preview deployment Vercel tambahan yang
   perlu diizinkan, tambahkan sebagai array multi-value:

   ```
   CORS_ORIGINS=["https://etiqa-mvi-frontend.vercel.app","https://etiqa-mvi-frontend-git-main-username.vercel.app"]
   ```

3. Railway akan otomatis redeploy backend dengan konfigurasi CORS baru.
4. Buka aplikasi di URL Vercel dan lakukan test alur penuh (Customer →
   Vehicle → Coverage → Quote → Purchase → Underwriting → Policy) untuk
   memastikan tidak ada error CORS di browser console.

### 10.9 Troubleshooting Deployment

| Masalah                                                | Solusi                                                                          |
|------------------------------------------------------------|--------------------------------------------------------------------------------|
| `Access to fetch ... has been blocked by CORS policy`      | Pastikan URL Vercel di `CORS_ORIGINS` Railway **persis sama** (termasuk `https://`, tanpa trailing slash) dengan origin yang tampil di address bar browser |
| Railway build gagal (`ModuleNotFoundError`)                 | Pastikan **Root Directory** service Railway diset ke `backend`, bukan root repo |
| Frontend memanggil `127.0.0.1:8000` di production           | Pastikan `API_BASE_URL` di `frontend/js/api.js` sudah diubah ke URL Railway sebelum push/deploy |
| Railway deploy sukses tapi `/docs` menampilkan 502          | Cek tab **Logs** di Railway — biasanya karena `DATABASE_URL` salah/tidak bisa diakses dari Railway (pastikan Supabase project aktif dan tidak paused) |
| Endpoint jalan di `/docs` tapi gagal dari frontend           | Buka DevTools → Network tab, cek response error persis apa; error 422 biasanya field request tidak sesuai `schemas.py` |

---

## 11. Ringkasan Checklist Deployment

- [ ] Supabase project dibuat, `DATABASE_URL` didapat
- [ ] Backend berjalan lokal, `/docs` bisa diakses, tabel otomatis terbuat
- [ ] Project di-push ke GitHub
- [ ] Railway project dibuat, Root Directory = `backend`
- [ ] Environment variables diisi di Railway (termasuk `DATABASE_URL`)
- [ ] Domain Railway di-generate, `/docs` production bisa diakses
- [ ] `API_BASE_URL` di `frontend/js/api.js` diubah ke URL Railway
- [ ] Vercel project dibuat, Root Directory = `frontend`
- [ ] `CORS_ORIGINS` di Railway diupdate dengan URL Vercel final
- [ ] Test alur penuh end-to-end di production (Landing → Policy Issued)

---

*Dibangun sebagai Technical Assessment untuk Etiqa Insurance Indonesia — 2026.*
