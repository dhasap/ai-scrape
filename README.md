# 📖 AI Scrape v12 - Agen Scraping Cerdas 🚀

<div align="center">
Sebuah sistem agen scraping semi-autonom dengan arsitektur client-server, menampilkan **Otak AI** di Vercel dan **Remote Control Cerdas** di Termux/PC.
</div>

---

## ✨ 1. Konsep & Arsitektur

Scraper ini bukan sekadar tools biasa. Ini adalah sebuah sistem agen cerdas dengan arsitektur **client-server modern** untuk stabilitas, kekuatan, dan kecerdasan maksimal.

### Backend API ("Otak" di Vercel)

* Dibangun dengan **Node.js (Express)** dan **Playwright**.
* Bertugas menjalankan browser headless, menganalisa halaman kompleks, dan berkomunikasi dengan **Google Gemini AI**.
* Semua proses berat dilakukan di **cloud Vercel**, sehingga perangkat lokal tetap ringan.

### Frontend CLI ("Remote Control" di Termux/PC)

* Dibangun dengan **Python (rich & questionary)**.
* Bertugas menerima input dari user, meneruskan ke backend, lalu menampilkan hasil dengan interaktif.
* Dirancang seperti kokpit yang nyaman, seolah-olah Anda sedang kerja bareng co-pilot AI.

```
+---------------------------------+      +--------------------------------+
|       REMOTE CONTROL (Termux)   |      |        OTAK AI (Vercel)        |
|---------------------------------|      |--------------------------------|
| - main.py (Python)              |      | - index.js (Node.js)           |
| - Input & menu interaktif       |      | - Browser Headless (Playwright)|
| - Kirim perintah via HTTP       |----->| - Analisa halaman              |
| - Tampilkan hasil JSON          |<-----| - Koneksi ke Google Gemini     |
+---------------------------------+      +--------------------------------+
```

---

## 🌟 2. Fitur Unggulan

* **Failover Otomatis Multi-Server** → otomatis pindah server cadangan kalau server utama down.
* **AI Dua Mode Otak**:

  * *Co-pilot Penjelajah*: kasih saran scrape yang menarik saat menjelajah umum.
  * *GPS Pemburu*: fokus bantu navigasi cepat ke halaman detail yang dicari.
* **Menu Kontekstual Cerdas** → menu selalu berubah sesuai halaman (utama, pencarian, detail, chapter).
* **Scraping Multi-Lapis** → bisa scrape daftar, detail, dan chapter.
* **User Experience Mulus** → alur kerja natural, tombol kembali cerdas di tiap level.

---

## 🚀 3. Instalasi & Setup Lengkap

Proses setup terbagi jadi 2 bagian:

1. **Backend (Otak AI) di Vercel**
2. **Frontend CLI (Remote Control) di Termux/PC**

---

### Bagian 1: Setup Backend (Vercel)

#### 1. Clone Repository

```bash
git clone https://github.com/dhasap/api-scrape.git
cd api-scrape
```

#### 2. Deploy ke Vercel

1. Buka [vercel.com](https://vercel.com) dan login.
2. Klik **Add New > Project**.
3. Pilih repo `api-scrape` yang barusan di-clone.
4. Vercel otomatis deteksi sebagai project **Node.js**.
5. Klik **Deploy**.

#### 3. Konfigurasi Proyek

* **Atur Node.js Version**:

  * Buka **Settings > General**
  * Scroll ke **Build & Development Settings**
  * Pilih **Node.js 18.x**
  * Klik **Save**

* **Atur Environment Variables**:

  * Masuk ke **Settings > Environment Variables**
  * Tambahkan:

    ```
    Key: GEMINI_API_KEY
    Value: [API Key Google Gemini Anda]
    ```
  * (Opsional) Tambahkan:

    ```
    Key: AWS_LAMBDA_JS_RUNTIME
    Value: nodejs18.x
    ```

* Tunggu Vercel auto-redeploy sampai status **Ready** ✅

#### 4. Ambil URL Backend

* Copy URL project dari dashboard Vercel, contoh:

  ```
  https://api-scrape-alpha.vercel.app
  ```
* Ulangi langkah 2–4 untuk membuat server cadangan (backup).

---

### Bagian 2: Setup Frontend CLI (Termux/PC)

#### 1. Install Tools di Termux

```bash
pkg update && pkg upgrade
pkg install rust build-essential clang pkg-config libffi openssl git python-pip
```

#### 2. Clone Repository

```bash
git clone https://github.com/dhasap/ai-scrape-cli.git
cd ai-scrape-cli
```

#### 3. Install Dependencies Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Buat File Konfigurasi `.env`

Di folder yang sama dengan `main.py`, buat file `.env`:

```ini
# Server utama
VERCEL_API_URL_1="https://URL_SERVER_UTAMA.vercel.app"

# Server cadangan (opsional)
VERCEL_API_URL_2="https://URL_SERVER_CADANGAN_1.vercel.app"
VERCEL_API_URL_3="https://URL_SERVER_CADANGAN_2.vercel.app"
```

#### 5. Jalankan Program

```bash
python main.py
```

Jika berhasil, akan muncul menu interaktif dengan tampilan modern.

---

## ⚙️ 4. Cara Menggunakan

1. Buka CLI dengan `python main.py`
2. Pilih menu sesuai konteks (misal: Cari Komik, Lihat Detail, Baca Chapter).
3. Nikmati pengalaman scraping yang smooth.

---

## 🔥 5. Tips & Trik

* Gunakan lebih dari 1 akun Vercel untuk server cadangan (hindari limit).
* Simpan `.env` dengan aman, jangan di-push ke GitHub.
* Update `requirements.txt` dan `index.js` secara berkala.

---

## 📌 6. Roadmap

* [ ] Mode otomatis (AI memilih scrape terbaik)
* [ ] Support multi-bahasa antarmuka

---

## 📄 Lisensi

MIT License © 2025 - Dhasap
