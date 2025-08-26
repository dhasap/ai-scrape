<div align="center">

# 📖 Universal AI Comic Scraper v5.0 🤖

**CLI Scraper Modern dengan Kecerdasan AI + Otomatisasi Browser**

🚀 Powered by Google Gemini & Selenium 🚀

</div>

---

## ✨ Fitur Unggulan

* 🌐 **Scraping Universal**
  Tidak lagi terbatas pada satu website! AI mampu menganalisis struktur HTML dari hampir semua halaman detail komik dan mengekstrak data secara otomatis.

* 🧠 **Pencarian Interaktif**
  Lakukan pencarian dengan bahasa natural dan dapatkan daftar hasil yang bisa ditelusuri. AI akan menampilkan **5 judul teratas**, dan Anda dapat meminta lebih banyak dengan perintah `lagi`.

* 🎯 **Navigasi Cerdas**
  Gunakan perintah natural seperti:

  * `pergi cari [judul]` → melakukan pencarian
  * `pergi ke [nomor]` → langsung ke detail komik dari hasil pencarian
  * `pergi ke daftar komik` → navigasi ke menu atau halaman tertentu

* 📄 **Output JSON Modern**
  Data hasil scraping ditampilkan dalam format **JSON terstruktur, bersih, dan siap diolah**.

* ⚡ **CLI Ringan & Elegan**
  Dijalankan sepenuhnya lewat CLI dengan dukungan warna & tampilan modern.

---

## 🚀 Instalasi & Setup

Ikuti langkah-langkah berikut untuk menjalankan proyek ini di mesin lokal Anda.

### 1. Clone Repository

```bash
git clone https://github.com/dhasap/ai-scrape.git
cd ai-scrape
```

### 2. Instalasi Dependensi

Pastikan Anda memiliki **Python 3.8+**. Buat virtual environment agar lebih terisolasi.

```bash
# Buat dan aktifkan virtual environment
python3 -m venv venv
source venv/bin/activate

# Instal library
pip install -r requirements.txt
```

### 3. Setup Browser Driver (untuk Selenium)

Untuk Chromebook/Debian/Ubuntu:

```bash
sudo apt install chromium-driver
```

Untuk OS Lain: pastikan Anda memiliki **Google Chrome** + **ChromeDriver** dengan versi yang sesuai.

### 4. Setup API Key Gemini

Dapatkan API Key Anda dari **Google AI Studio**.

Atur API Key sebagai environment variable:

**Windows (Command Prompt):**

```bash
setx GEMINI_API_KEY "API_KEY_ANDA_DISINI"
```

**macOS / Linux:**

```bash
export GEMINI_API_KEY="API_KEY_ANDA_DISINI"
```

Tambahkan ke `~/.bashrc` atau `~/.zshrc` agar permanen.

---

## ⚙️ Cara Menggunakan

Setelah instalasi selesai, jalankan aplikasi dengan perintah:

```bash
python3 main.py
```

---

## 🕹️ Contoh Sesi Penggunaan

### 🔍 Mencari Komik & Menampilkan Hasil

```bash
> pergi cari magic
```

Hasil:

```
1. Magic Emperor
2. The Beginning After The End
3. Return of the 8th Class Magician
4. I Am The Sorcerer King
5. A Returner's Magic Should Be Special
```

Ketik `lagi` untuk 5 berikutnya, atau `pergi ke [nomor]` untuk memilih.

---

### ⏭️ Melihat Hasil Berikutnya

```bash
> lagi
```

### 🎯 Memilih dari Hasil Pencarian

```bash
> pergi ke 3
```

AI akan membuka detail **Return of the 8th Class Magician**.

---

### ⚡ Langsung ke Detail Komik

```bash
> pergi ke solo leveling
```

AI akan langsung mencari dan membuka halaman detail **Solo Leveling**.

---

### 📄 Melakukan Scraping Universal

```bash
> scrape
```

AI akan menganalisis halaman detail dan mengekstrak data ke format JSON terstruktur.
