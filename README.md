# 📖 Universal AI Comic Scraper v10.0 🚀

<div align="center">

**Arsitektur Client-Server dengan Backend di Vercel & CLI Modern di Termux**

</div>

---

## ✨ Konsep Arsitektur Baru

Scraper ini telah dirombak total menjadi arsitektur client-server yang tangguh dan modern:

*   **Backend API (di Vercel)**: Sebuah "mesin" scraping yang dibuat dengan **FastAPI** dan **Playwright**. Semua pekerjaan berat seperti menjalankan browser, mengeksekusi JavaScript, dan parsing HTML dilakukan di cloud. Ini membuat prosesnya cepat dan tidak membebani perangkat lokal.

*   **Frontend CLI (di Termux/PC)**: Sebuah "kokpit" atau antarmuka pengguna yang dibuat dengan **Rich** dan **Questionary**. Tugasnya hanya menerima perintah dari pengguna dan berkomunikasi dengan backend. Tampilannya interaktif, modern, dan ramah pengguna.

## 🚀 Alur Instalasi & Setup

Proses setup sekarang dibagi menjadi dua bagian: Backend dan CLI.

### **Bagian 1: Setup Backend di Vercel**

1.  **Clone Repository**
    ```bash
    git clone https://github.com/dhasap/ai-scrape.git
    cd ai-scrape
    ```

2.  **Deploy ke Vercel**
    *   Install Vercel CLI di PC Anda: `npm install -g vercel`
    *   Login ke Vercel: `vercel login`
    *   Dari dalam direktori `ai-scrape`, jalankan perintah `vercel` dan ikuti petunjuknya untuk mendeploy proyek baru.

3.  **Konfigurasi Proyek di Vercel**
    Setelah deploy, buka dashboard proyek Anda di situs Vercel:

    *   **Atur Build Command**:
        *   Buka `Settings > General`.
        *   Di bagian `Build & Development Settings`, override **Build Command** dan masukkan:
        ```bash
        pip install -r api/requirements.txt && playwright install --with-deps chromium
        ```

    *   **Atur Environment Variable**:
        *   Buka `Settings > Environment Variables`.
        *   Tambahkan variabel berikut:
          *   `GEMINI_API_KEY`: Masukkan API Key Google Gemini Anda.

4.  **Dapatkan URL Backend Anda**
    *   Setelah Vercel selesai deploy ulang, salin URL produksi Anda. Contoh: `https://ai-scrape-xxxxx.vercel.app`

---

### **Bagian 2: Setup CLI di Termux (atau PC)**

1.  **Install Dependensi CLI**
    Di dalam direktori `ai-scrape` di Termux, jalankan:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Buat File Konfigurasi (`.env`)**
    *   Buat sebuah file baru bernama `.env` di direktori utama.
    *   Isi file `.env` dengan format berikut:
    ```env
    GEMINI_API_KEY="API_KEY_ANDA_DISINI"
    VERCEL_API_URL="URL_BACKEND_VERCEL_ANDA_DISINI"
    ```
    *   Ganti dengan API Key Anda dan URL yang Anda dapatkan dari Vercel.

---

## ⚙️ Cara Menggunakan

Setelah semua setup selesai, jalankan aplikasi dari Termux atau PC Anda dengan perintah:

```bash
python main.py
```

Anda akan disambut oleh menu interaktif yang modern. Cukup ikuti petunjuk di layar untuk memulai sesi scraping baru.
