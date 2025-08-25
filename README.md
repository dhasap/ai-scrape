# 🤖 AI Comic Scraper

<div align="center">🤖 AI Comic Scraper 📖 Sebuah tool CLI cerdas yang ditenagai oleh Google Gemini untuk menavigasi dan melakukan scraping data dari website komik menggunakan bahasa natural.</div>

---

## ✨ Fitur Utama

* 🧠 **Navigasi Cerdas**: Gunakan perintah bahasa natural (misalnya: "cari one piece") untuk membiarkan AI memilih link yang paling relevan.
* 📋 **Ekstraksi Data Lengkap**: Ambil semua informasi penting dari halaman detail komik, termasuk judul, sinopsis, genre, status, rating, dan daftar chapter.
* 📄 **Output JSON**: Semua data yang berhasil di-scrape akan disajikan dalam format JSON yang bersih dan terstruktur, siap untuk diolah.
* 💻 **Interaktif & Ringan**: Dijalankan sepenuhnya melalui CLI yang mudah digunakan tanpa memerlukan browser.

---

## 🚀 Instalasi & Setup

Ikuti langkah-langkah berikut untuk menjalankan proyek ini di mesin lokal Anda.

### 1. Clone Repository

Pertama, clone repository ini ke komputer Anda:

```bash
git clone https://github.com/NAMA_USER_ANDA/NAMA_REPO_ANDA.git
cd NAMA_REPO_ANDA
```

### 2. Instalasi Dependensi

Pastikan Anda memiliki Python 3.8+. Kemudian, instal semua library yang dibutuhkan:

```bash
pip install -r requirements.txt
```

### 3. Setup API Key Gemini

Tool ini memerlukan API Key dari Google Gemini.

* Dapatkan API Key Anda dari [Google AI Studio](https://makersuite.google.com/).
* Set API Key tersebut sebagai environment variable agar aman.

Untuk **Windows (Command Prompt):**

```bash
setx GEMINI_API_KEY "API_KEY_ANDA_DISINI"
```

(Anda perlu menutup dan membuka kembali terminal agar variabel ini terbaca)

Untuk **macOS / Linux:**

```bash
export GEMINI_API_KEY="API_KEY_ANDA_DISINI"
```

(Untuk membuatnya permanen, tambahkan baris di atas ke dalam file `~/.bashrc` atau `~/.zshrc`)

---

## ⚙️ Cara Menggunakan

Setelah instalasi dan setup API Key selesai, jalankan aplikasi dengan perintah:

```bash
python main.py
```

Aplikasi akan meminta Anda memasukkan URL utama dari website komik yang ingin di-scrape.

---

## 🕹️ Contoh Sesi Penggunaan

### Memulai & Bernavigasi dengan AI

Masukkan URL utama website komik (cth: `https://komikcast.li`):

```
https://komikcast.li

📍 Lokasi saat ini: https://komikcast.li
> pergi ke daftar manga populer
```

AI akan memproses perintah, memilih link yang paling sesuai, dan otomatis berpindah ke URL tersebut.

### Melakukan Scraping Data

Setelah berada di halaman detail komik yang diinginkan:

```
📍 Lokasi saat ini: https://komikcast.li/komik/solo-leveling/
> scrape
```

### Menyimpan Hasil ke File

Setelah data ditampilkan, Anda akan ditanya apakah ingin menyimpan hasilnya.

```
Apakah Anda ingin menyimpan hasil ini ke file JSON? (y/n): y
💾 Data berhasil disimpan ke file: solo_leveling.json
```

---

## 📄 Contoh Output JSON

Berikut adalah contoh struktur data JSON yang akan dihasilkan setelah proses scraping:

```json
{
    "url_sumber": "https://komikcast.li/komik/solo-leveling/",
    "judul": "Solo Leveling",
    "sinopsis": "10 tahun yang lalu, setelah “Gerbang” yang menghubungkan dunia nyata dengan dunia monster terbuka...",
    "details": {
        "status": "Completed",
        "type": "Manhwa",
        "rilis": "2018",
        "author": "Chugong",
        "artist": "DUBU (REDICE STUDIO)"
    },
    "genre": [
        "Action",
        "Adventure",
        "Fantasy",
        "Manhwa"
    ],
    "rating": "9.1",
    "daftar_chapter": [
        {
            "chapter": "Chapter 179 [END]",
            "url": "https://komikcast.li/chapter/solo-leveling-chapter-179-bahasa-indonesia/",
            "tanggal_rilis": "Desember 30, 2021"
        },
        {
            "chapter": "Chapter 178",
            "url": "https://komikcast.li/chapter/solo-leveling-chapter-178-bahasa-indonesia/",
            "tanggal_rilis": "Desember 22, 2021"
        }
    ]
}
```
