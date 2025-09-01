# 📖 AI Scrape v12 - Agen Scraping Cerdas (Dokumentasi Lengkap) 🚀

<div align="center">
  <strong>🚀 Sistem agen scraping semi-autonom dengan arsitektur client-server 🚀</strong><br>
  <em>💡 Otak AI di Vercel + Remote Control di Termux 💡</em>
</div>

---

## ✨ 1. Konsep & Arsitektur

**AI Scrape v12** bukan sekadar scraper biasa. Ini adalah **agen cerdas** dengan arsitektur client-server modern untuk mencapai **stabilitas, kekuatan, dan kecerdasan maksimal**.

### 🔹 Backend API ("Otak" di Vercel)

* ⚡ Dibangun dengan **Node.js (Express) + Playwright**
* 🧠 Menjalankan browser headless, analisa HTML kompleks, komunikasi dengan **Google Gemini AI**
* ☁️ Semua kerja berat dilakukan di cloud, jadi perangkat lokal tetap ringan

### 🔹 Frontend CLI ("Remote Control" di Termux/PC)

* 🐍 Dibangun dengan **Python (rich & questionary)**
* 🎮 Jadi kokpit interaktif buat user sebagai **pilot**
* 🔄 Mengirim perintah ke Otak AI, terima hasil JSON, tampilkan dengan UI modern

```
+---------------------------------+      +--------------------------------+
|       REMOTE CONTROL (Termux)   |      |        OTAK AI (Vercel)        |
|---------------------------------|      |--------------------------------|
| - main.py (Python)              |      | - index.js (Node.js)           |
| - Input pengguna                |      | - Browser Headless (Playwright)|
| - Menu interaktif               |----->| - Analisa HTML + Gemini AI     |
| - Kirim perintah via HTTP       |<-----| - Scraping Data JSON           |
+---------------------------------+      +--------------------------------+
```

---

## 🌟 2. Fitur Unggulan

✅ **Failover Otomatis Multi-Server** → auto-switch jika server utama down
✅ **AI dengan Dua Mode Otak**:

* 🛸 **Co-pilot Penjelajah** → kasih insight saat browsing umum
* 🎯 **GPS Pemburu** → bantu navigasi langsung ke target spesifik

✅ **Menu Kontekstual Cerdas** → UI adaptif sesuai halaman (home, pencarian, detail, chapter)
✅ **Scraping Multi-Lapis**:

* 📚 Scrape **Daftar** → ambil list item (misalnya daftar komik terbaru)
* 📖 Scrape **Detail** → info lengkap (sinopsis, genre, author, daftar chapter)
* 🖼️ Scrape **Chapter** → ambil semua link gambar panel komik

✅ **Pengalaman Pengguna Mulus** → workflow natural: cari komik → pilih hasil → scrape detail → buka chapter, semua dalam satu sesi dengan tombol back yang cerdas

---

## 🚀 3. Alur Instalasi & Setup

### 🖥️ Bagian 1: Setup Backend ("Otak") di Vercel

1. **Clone Repository**

   ```bash
   git clone https://github.com/dhasap/api-scrape.git
   cd api-scrape
   ```

2. **Deploy ke Vercel**

   * Buka [vercel.com](https://vercel.com) dan login
   * Klik **Add New > Project**
   * Pilih repository `api-scrape` dari GitHub
   * Vercel auto-deteksi Node.js → klik **Deploy**

3. **Konfigurasi Project di Vercel**

   * **Atur Versi Node.js** → Settings > General > Build Settings > Node.js Version: `18.x`
   * **Tambahkan Environment Variables**:

     ```env
     GEMINI_API_KEY=API_KEY_GEMINI_ANDA
     AWS_LAMBDA_JS_RUNTIME=nodejs18.x   # Opsional
     ```
   * Simpan → Vercel auto-redeploy → tunggu status **Ready**

4. **Dapatkan URL Backend**

   * Salin URL produksi (contoh: `https://api-scrape-alpha.vercel.app`)
   * Ulangi langkah di atas untuk semua server cadangan

---

### 📱 Bagian 2: Setup CLI ("Remote Control") di Termux

1. **Install Tools Wajib**

   ```bash
   pkg install rust build-essential clang pkg-config libffi openssl
   ```

2. **Install Dependensi Python**

   ```bash
   pip install -r requirements.txt
   ```

3. **Buat File Konfigurasi .env**

   ```env
   # Server utama
   VERCEL_API_URL_1="https://URL_SERVER_UTAMA.vercel.app"

   # Server cadangan (opsional)
   VERCEL_API_URL_2="https://URL_SERVER_CADANGAN_1.vercel.app"
   VERCEL_API_URL_3="https://URL_SERVER_CADANGAN_2.vercel.app"
   ```

---

## ⚙️ 4. Cara Menggunakan

Jalankan dari direktori `ai-scrape` di Termux:

```bash
python main.py
```

🎉 Selamat! Sekarang lo bisa berinteraksi dengan **AI Scrape v12** layaknya punya **co-pilot AI pribadi** 🚀
