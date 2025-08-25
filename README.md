🤖 AI Comic ScraperSebuah tool CLI (Command Line Interface) berbasis Python yang menggunakan AI (Google Gemini) untuk melakukan scraping data dari website komik secara cerdas dan otomatis. Pengguna dapat bernavigasi menggunakan bahasa natural untuk menemukan dan mengekstrak detail komik ke dalam format JSON.✨ Fitur UtamaNavigasi Cerdas: Gunakan perintah dalam bahasa natural (misalnya: "cari one piece") untuk membiarkan AI memilih link yang paling relevan.Ekstraksi Data Lengkap: Ambil semua informasi penting dari halaman detail komik, termasuk judul, sinopsis, genre, status, rating, dan daftar chapter.Output JSON: Semua data yang berhasil di-scrape akan disajikan dalam format JSON yang bersih dan terstruktur.Interaktif: Dijalankan sepenuhnya melalui CLI yang mudah digunakan.🚀 Instalasi & Setup1. Clone RepositoryPertama, clone repository ini ke mesin lokal Anda:git clone https://github.com/NAMA_USER_ANDA/NAMA_REPO_ANDA.git
cd NAMA_REPO_ANDA
2. Instalasi DependensiPastikan Anda memiliki Python 3.8+ terinstal. Kemudian, instal semua library yang dibutuhkan menggunakan requirements.txt:pip install -r requirements.txt
3. Setup API Key GeminiTool ini memerlukan API Key dari Google Gemini.Dapatkan API Key Anda dari Google AI Studio.Set API Key tersebut sebagai environment variable agar aman dan tidak terekspos di dalam kode.Untuk Windows (Command Prompt):setx GEMINI_API_KEY "API_KEY_ANDA_DISINI"
(Anda perlu menutup dan membuka kembali terminal agar variabel ini terbaca)Untuk macOS / Linux:export GEMINI_API_KEY="API_KEY_ANDA_DISINI"
(Untuk membuatnya permanen, tambahkan baris di atas ke dalam file ~/.bashrc atau ~/.zshrc)⚙️ Cara MenjalankanSetelah instalasi dan setup API Key selesai, jalankan aplikasi dengan perintah berikut:python main.py
Aplikasi akan meminta Anda memasukkan URL utama dari website komik yang ingin di-scrape.Contoh PerintahMemulai & Bernavigasi:Masukkan URL utama website komik (cth: https://komikcast.li): https://komikcast.li

📍 Lokasi saat ini: https://komikcast.li
> pergi cari komik solo leveling
AI akan memproses dan memilih link yang paling sesuai dengan "cari komik solo leveling" dan otomatis berpindah ke URL tersebut.Melakukan Scraping:Setelah berada di halaman detail komik yang diinginkan:📍 Lokasi saat ini: https://komikcast.li/komik/solo-leveling/
> scrape
Menyimpan Hasil:Setelah data ditampilkan, Anda akan ditanya apakah ingin menyimpan hasilnya.Apakah Anda ingin menyimpan hasil ini ke file JSON? (y/n): y
📄 Contoh Output JSONBerikut adalah contoh struktur data JSON yang akan dihasilkan setelah proses scraping:{
    "url_sumber": "https://komikcast.li/komik/solo-leveling/",
    "judul": "Solo Leveling",
    "sinopsis": "10 tahun yang lalu, setelah “Gerbang” yang menghubungkan dunia nyata dengan dunia monster terbuka, beberapa orang biasa, setiap hari menerima kekuatan untuk memburu monster di dalam Gerbang. Mereka dikenal sebagai “Hunter”. Namun, tidak semua Hunter kuat. Nama saya Sung Jin-Woo, seorang Hunter peringkat-E. Saya seseorang yang harus mempertaruhkan nyawanya di dungeon paling rendah, “Terlemah di Dunia”. Tidak memiliki keterampilan apa pun untuk ditampilkan, saya hampir tidak mendapatkan uang yang dibutuhkan dengan bertarung di dungeon berlevel rendah… setidaknya sampai saya menemukan dungeon tersembunyi dengan kesulitan tersulit dalam dungeon peringkat-D! Pada akhirnya, saat aku menerima kematian, tiba-tiba aku menerima kekuatan aneh, log pencarian yang hanya bisa kulihat, rahasia untuk naik level yang hanya aku yang tahu! Jika saya berlatih sesuai dengan pencarian saya dan monster yang diburu, level saya akan naik. Berubah dari Hunter terlemah menjadi Hunter peringkat-S terkuat!",
    "details": {
        "status": "Completed",
        "type": "Manhwa",
        "rilis": "2018",
        "author": "Chugong",
        "artist": "DUBU (REDICE STUDIO)",
        "serialization": "KakaoPage",
        "posted_by": "Komikcast",
        "posted_on": "Maret 5, 2020",
        "updated_on": "Januari 1, 2022"
    },
    "genre": [
        "Action",
        "Adventure",
        "Fantasy",
        "Manhwa",
        "Shounen",
        "Webtoons"
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
