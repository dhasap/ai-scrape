# 📖 AI Scrape v12 - Agen Scraping Cerdas 🚀

<div align="center">
  <strong>🚀 Sistem agen scraping semi-autonom dengan arsitektur client-server 🚀</strong><br>
  <em>💡 Otak AI di Vercel + Remote Control di Termux 💡</em>
</div>

---

## 📌 Daftar Isi

* [✨ Konsep & Arsitektur](#-konsep--arsitektur)
* [🌟 Fitur Unggulan](#-fitur-unggulan)
* [🚀 Instalasi & Setup](#-instalasi--setup)

  * [🖥️ Backend (Otak di Vercel)](#️-backend-otak-di-vercel)
  * [📱 Frontend CLI (Remote Control di Termux)](#-frontend-cli-remote-control-di-termux)
* [⚙️ Cara Menggunakan](#️-cara-menggunakan)
* [📊 Workflow Penggunaan](#-workflow-penggunaan)
* [🛠️ Roadmap](#️-roadmap)
* [❓ FAQ](#-faq)

---

## ✨ Konsep & Arsitektur

**AI Scrape v12** adalah agen scraping cerdas dengan desain **client-server**. Semua kerja berat (rendering, scraping, AI reasoning) dikerjakan oleh **backend di Vercel**, sementara pengguna cukup mengontrol lewat **CLI ringan di Termux/PC**.

### 🔹 Backend API ("Otak" di Vercel)

* Dibangun dengan **Node.js (Express) + Playwright**
* Analisa halaman + komunikasi dengan **Google Gemini AI**
* Headless scraping → hasil dalam format JSON

### 🔹 Frontend CLI ("Remote Control")

* Dibangun dengan **Python (rich & questionary)**
* Tampilan interaktif dengan menu dinamis
* Kirim perintah ke backend, tampilkan hasil dengan UI rapi

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

## 🌟 Fitur Unggulan

* ✅ **Failover Multi-Server** → auto-switch jika server utama down
* ✅ **AI dengan Dua Mode**:

  * 🛸 *Co-pilot Penjelajah* → untuk eksplorasi bebas
  * 🎯 *GPS Pemburu* → navigasi langsung ke target
* ✅ **Menu Kontekstual Cerdas** → UI adaptif sesuai halaman
* ✅ **Scraping Multi-Lapis** (List → Detail → Chapter)
* ✅ **User Experience Natural** → workflow mirip browsing asli

---

## 🚀 Instalasi & Setup

### 🖥️ Backend (Otak di Vercel)

1. **Persiapkan Repository**

   * Clone project backend (misalnya `api-scrape`).
   * Pastikan file `index.js` dan dependensi sudah siap.

2. **Deploy ke Vercel**

   * Login ke [vercel.com](https://vercel.com).
   * Tambahkan project baru dari repo GitHub.
   * Pastikan platform otomatis mendeteksi Node.js.

3. **Atur Konfigurasi Vercel**

   * Pilih Node.js version **18.x** di Build Settings.
   * Tambahkan environment variables (misalnya `GEMINI_API_KEY`).
   * Tunggu hingga status deploy menjadi **Ready**.

4. **Catat URL Backend**

   * Salin URL produksi (misalnya `https://api-scrape.vercel.app`).
   * (Opsional) Deploy ke beberapa project untuk server cadangan.

---

### 📱 Frontend CLI (Remote Control di Termux)

1. **Install Tools Wajib**

   * Install compiler & library dasar (contoh: `clang`, `openssl`).

2. **Install Dependensi Python**

   * Gunakan `requirements.txt` untuk menginstal library yang dibutuhkan.

3. **Buat File `.env`**

   * Masukkan URL backend dari langkah sebelumnya.
   * Bisa tambahkan lebih dari satu server untuk failover.

---

## ⚙️ Cara Menggunakan

1. Jalankan CLI dengan Python.
2. Pilih mode operasi (Co-pilot / GPS).
3. Navigasi menggunakan menu interaktif.
4. Hasil scraping ditampilkan langsung di terminal.

---

## 📊 Workflow Penggunaan

1. **Cari Komik/Item**
2. **Pilih dari daftar hasil**
3. **Scrape detail lengkap**
4. **Buka chapter dan ambil panel gambar**

Semua langkah bisa dilakukan dalam satu sesi tanpa restart.

---

## 🛠️ Roadmap

* [ ] Integrasi penyimpanan hasil ke database (Supabase)
* [ ] Mode offline dengan cache lokal
* [ ] Ekspor hasil scraping ke PDF/EPUB
* [ ] Plugin tambahan untuk berbagai situs

---

## ❓ FAQ

**Q: Bisa dijalankan di Windows/Linux selain Termux?**
A: Ya, CLI berbasis Python jadi fleksibel di semua OS.

**Q: Apakah scraping ini aman?**
A: Gunakan dengan bijak. Ikuti ketentuan situs target.

**Q: Apa keunggulan dibanding scraper biasa?**
A: Integrasi AI + failover server bikin lebih cerdas, stabil, dan fleksibel.

---

🎉 Selamat! Dengan **AI Scrape v12**, lo sekarang punya **agen scraping AI pribadi** yang modern dan siap tempur 🚀
