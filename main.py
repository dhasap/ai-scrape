# main.py (v7.0 - Natural Language Engine)
import os
import json
import time
import sys
import threading
import re
import csv
from urllib.parse import urljoin

import google.generativeai as genai
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

import pyfiglet
from colorama import init, Fore, Style

# Inisialisasi Colorama
init(autoreset=True)

# --- KONFIGURASI ---
try:
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("API Key Gemini tidak ditemukan. Mohon set environment variable 'GEMINI_API_KEY'")
    genai.configure(api_key=GEMINI_API_KEY)
except ValueError as e:
    print(e)
    exit()

MODEL = genai.GenerativeModel('gemini-1.5-flash')

# --- FUNGSI TAMPILAN & ANIMASI ---
LOADING_EVENT = threading.Event()
UNDERLINE = '\033[4m'

def spinner_animation():
    """Menampilkan animasi loading spinner."""
    spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    while not LOADING_EVENT.is_set():
        for char in spinner_chars:
            sys.stdout.write(f'\r{Fore.CYAN}{char} {Style.RESET_ALL}Memproses... ')
            sys.stdout.flush()
            time.sleep(0.1)
            if LOADING_EVENT.is_set():
                break
    sys.stdout.write('\r' + ' ' * 30 + '\r')
    sys.stdout.flush()

def run_with_loading(target_func, *args, **kwargs):
    """Menjalankan fungsi dengan animasi loading."""
    LOADING_EVENT.clear()
    animation_thread = threading.Thread(target=spinner_animation)
    animation_thread.start()
    result = None
    try:
        result = target_func(*args, **kwargs)
    finally:
        LOADING_EVENT.set()
        animation_thread.join()
    return result

def print_header():
    """Menampilkan header dashboard modern."""
    os.system('cls' if os.name == 'nt' else 'clear')
    ascii_art = pyfiglet.figlet_format('DHANY SCRAPE', font='slant')
    width = max(len(line) for line in ascii_art.strip('\n').split('\n')) + 4
    tagline = "😈 Dhany adalah Raja Iblis 👑"
    version_info = f"{Fore.GREEN}Versi 7.0{Style.RESET_ALL} | {Fore.CYAN}Natural Language Engine{Style.RESET_ALL}"
    
    print(f"{Fore.BLUE}{Style.BRIGHT}╔{'═' * width}╗{Style.RESET_ALL}")
    for line in ascii_art.strip('\n').split('\n'):
        print(f"{Fore.BLUE}{Style.BRIGHT}║ {line.center(width - 2)} ║{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{Style.BRIGHT}║{' ' * width}║{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{Style.BRIGHT}║{Style.NORMAL}{Fore.MAGENTA}{Style.BRIGHT}{tagline.center(width)}{Style.RESET_ALL}{Fore.BLUE}{Style.BRIGHT}║")
    print(f"{Fore.BLUE}{Style.BRIGHT}║{version_info.center(width + 10)}{Fore.BLUE}{Style.BRIGHT}║")
    print(f"{Fore.BLUE}{Style.BRIGHT}╚{'═' * width}╝{Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}Ketik 'keluar' untuk berhenti.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═' * (width + 2)}{Style.RESET_ALL}")

# --- OTAK AI: PARSER PERINTAH ---
def parse_command_with_ai(user_input):
    """Menggunakan AI untuk mengubah bahasa natural menjadi perintah terstruktur."""
    prompt = f"""
    Anda adalah NLU engine untuk CLI tool "DHANY SCRAPE". Analisis perintah user dan ubah menjadi JSON.
    Kunci JSON harus: "action", "target", "source", "output_format", "output_filename".
    - action: scrape, download, search, get, generate_js.
    - output_format: csv, json, txt, database, folder, js_file.
    - Infer output_filename dari target jika tidak disebut.

    Contoh 1:
    User: "scrape semua judul manga dari https://komikcast.io dan simpan ke file csv"
    JSON: {{"action": "scrape", "target": "semua judul manga", "source": "https://komikcast.io", "output_format": "csv", "output_filename": "judul_manga.csv"}}

    Contoh 2:
    User: "download semua gambar dari halaman https://website.com/gallery ke folder images"
    JSON: {{"action": "download", "target": "semua gambar", "source": "https://website.com/gallery", "output_format": "folder", "output_filename": "images"}}

    Contoh 3:
    User: "ambil daftar chapter terbaru One Piece dari komikcast, output JSON"
    JSON: {{"action": "get", "target": "daftar chapter terbaru One Piece", "source": "komikcast", "output_format": "json", "output_filename": "onepiece_chapters.json"}}
    
    Contoh 4:
    User: "buatkan scrape js untuk project aku"
    JSON: {{"action": "generate_js", "target": "scrape.js", "source": "komikcast", "output_format": "js_file", "output_filename": "scrape.js"}}

    ---
    Perintah User Saat Ini: "{user_input}"
    ---
    JSON:
    """
    try:
        response = MODEL.generate_content(prompt)
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_text)
    except Exception:
        return {'error': 'Gagal memahami perintah.'}

# --- EKSEKUTOR AKSI ---
def execute_command(driver, command, proxy_url):
    """Menjalankan aksi scraping berdasarkan perintah yang sudah diparsing."""
    action = command.get('action')
    target = command.get('target')
    source = command.get('source')
    output_format = command.get('output_format')
    output_filename = command.get('output_filename')

    if not all([action, target, source, output_format, output_filename]):
        print(f"{Fore.RED}Perintah tidak lengkap atau tidak dapat dipahami.{Style.RESET_ALL}")
        return

    print(f"{Fore.CYAN}Memulai aksi '{action}' pada target '{target}'...{Style.RESET_ALL}")
    
    if action == "generate_js":
        generate_scrape_js(output_filename, proxy_url)
        return
        
    # Simulasi atau eksekusi sederhana
    if action == "download" and "gambar" in target:
        # Simulasi
        os.makedirs(output_filename, exist_ok=True)
        print(f"{Fore.GREEN}Simulasi: Gambar dari {source} sudah di-download ke folder {output_filename}/{Style.RESET_ALL}")
    
    elif action == "scrape" and "judul manga" in target:
        # Eksekusi nyata
        try:
            driver.get(f"{proxy_url}?url={source}")
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            # Selector umum untuk judul
            titles = [h.get_text(strip=True) for h in soup.select('h3 a, h4 a, .title a')]
            
            if not titles:
                print(f"{Fore.YELLOW}Tidak ada judul yang ditemukan di {source}.{Style.RESET_ALL}")
                return

            if output_format == 'csv':
                with open(output_filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['judul'])
                    for title in titles:
                        writer.writerow([title])
                print(f"{Fore.GREEN}Judul manga berhasil disimpan ke file {output_filename}{Style.RESET_ALL}")
            elif output_format == 'json':
                 with open(output_filename, 'w', encoding='utf-8') as f:
                    json.dump({'judul_manga': titles}, f, ensure_ascii=False, indent=4)
                 print(f"{Fore.GREEN}Judul manga berhasil disimpan ke file {output_filename}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}Format output '{output_format}' belum didukung untuk aksi ini.{Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}Gagal melakukan scraping: {e}{Style.RESET_ALL}")

    elif action == "get" and "chapter" in target:
        # Simulasi
        print(f"{Fore.GREEN}Simulasi: Chapter terbaru {target} dari {source} di-export ke {output_filename}{Style.RESET_ALL}")
    
    else:
        print(f"{Fore.YELLOW}Aksi '{action}' untuk target '{target}' belum diimplementasikan sepenuhnya.{Style.RESET_ALL}")

def generate_scrape_js(filename, proxy_url):
    """Membuat file scrape.js dengan proxy yang diberikan."""
    js_code = f"""
class KomikcastScraper {{
    constructor() {{
        this.proxy = '{proxy_url}';
        this.baseUrl = 'https://komikcast.li'; // Updated base URL
    }}

    async fetchAndParse(url) {{
        try {{
            const response = await fetch(`${{this.proxy}}?url=${{encodeURIComponent(url)}}`);
            if (!response.ok) {{
                throw new Error(`HTTP error! status: ${{response.status}}`);
            }}
            const htmlString = await response.text();
            const parser = new DOMParser();
            return parser.parseFromString(htmlString, 'text/html');
        }} catch (error) {{
            console.error(`Error fetching or parsing ${{url}}:`, error);
            throw error;
        }}
    }}

    async getPopular(page = 1) {{
        const url = `${{this.baseUrl}}/daftar-komik/page/${{page}}/?status&type&orderby=popular`;
        const doc = await this.fetchAndParse(url);
        
        const comics = [];
        const elements = doc.querySelectorAll('div.list-update_item');
        
        elements.forEach(el => {{
            const title = el.querySelector('h3.title')?.innerText.trim();
            const fullUrl = el.querySelector('a')?.href;
            const cover = el.querySelector('.list-update_item-image img')?.src;
            const chapter = el.querySelector('.chapter')?.innerText.trim();
            const endpoint = fullUrl?.split('/').filter(Boolean).pop();

            if (title && endpoint) {{
                comics.push({{
                    title,
                    chapter,
                    image: `${{this.proxy}}?url=${{encodeURIComponent(cover)}}`,
                    url: `${{this.baseUrl}}/komik/${{endpoint}}`
                }});
            }}
        }});
        
        return comics;
    }}

    async search(query) {{
        const url = `${{this.baseUrl}}/?s=${{query}}`;
        const doc = await this.fetchAndParse(url);

        const comics = [];
        const elements = doc.querySelectorAll('div.listupd .bs');

        elements.forEach(el => {{
            const title = el.querySelector('.tt')?.innerText.trim();
            const fullUrl = el.querySelector('a')?.href;
            const cover = el.querySelector('img')?.src;
            const endpoint = fullUrl?.split('/')[4];

            if (title && endpoint) {{
                comics.push({{
                    title,
                    image: `${{this.proxy}}?url=${{encodeURIComponent(cover)}}`,
                    url: `${{this.baseUrl}}/komik/${{endpoint}}`
                }});
            }}
        }});

        return comics;
    }}

    async getGenres() {{
        const url = `${{this.baseUrl}}/daftar-komik/`;
        const doc = await this.fetchAndParse(url);

        const genres = [];
        const elements = doc.querySelectorAll('.komiklist_dropdown-menu.c4.genrez li');

        elements.forEach(el => {{
            const name = el.querySelector('label').innerText.trim();
            const id = el.querySelector('input').value;
            genres.push({{ id, name }});
        }});

        return genres;
    }}

    async getMangaDetails(mangaUrl) {{
        const doc = await this.fetchAndParse(mangaUrl);

        const title = doc.querySelector('h1.komik_info-content-body-title')?.innerText.trim();
        const synopsis = doc.querySelector('.komik_info-description-sinopsis p')?.innerText.trim();
        const genres = Array.from(doc.querySelectorAll('.komik_info-content-genre a')).map(el => el.innerText.trim());
        const author = doc.querySelector('.komik_info-content-info:nth-child(2)')?.innerText.replace('Author:', '').trim();
        const status = doc.querySelector('.komik_info-content-info:nth-child(3)')?.innerText.replace('Status:', '').trim();
        const type = doc.querySelector('.komik_info-content-info-type a')?.innerText.trim();
        const updated = doc.querySelector('.komik_info-content-update time')?.innerText.trim();
        const cover = doc.querySelector('.komik_info-cover-image img')?.src;

        return {{
            title,
            synopsis,
            genres,
            author,
            status,
            type,
            updated,
            image: `${{this.proxy}}?url=${{encodeURIComponent(cover)}}`
        }};
    }}

    async getChapters(mangaUrl) {{
        const doc = await this.fetchAndParse(mangaUrl);

        const chapters = [];
        const elements = doc.querySelectorAll('li.komik_info-chapters-item');

        elements.forEach(el => {{
            const title = el.querySelector('a.chapter-link-item')?.innerText.trim();
            const url = el.querySelector('a.chapter-link-item')?.href;
            const date = el.querySelector('div.chapter-link-time')?.innerText.trim();

            if (title && url) {{
                const endpoint = url.split('/').filter(Boolean).pop();
                chapters.push({{
                    title,
                    url,
                    date,
                    endpoint
                }});
            }}
        }});

        const mangaTitle = doc.querySelector('h1.komik_info-content-body-title')?.innerText.trim();
        const mangaEndpoint = mangaUrl.split('/').filter(Boolean).pop();
        localStorage.setItem(`chapters_komikcast_${{mangaEndpoint}}`, JSON.stringify({{ mangaTitle, chapters }}));

        if (typeof setupNavigation === 'function') {{
            setupNavigation('komikcast');
        }}

        return chapters;
    }}

    async getImages(chapterUrl) {{
        const doc = await this.fetchAndParse(chapterUrl);

        const images = [];
        const elements = doc.querySelectorAll('.main-reading-area img');

        elements.forEach(el => {{
            const url = el.src || el.dataset.src;
            if (url) {{
                images.push(`${{this.proxy}}?url=${{encodeURIComponent(url)}}`);
            }}
        }});

        return images;
    }}
}}

export default {{
    id: 'komikcast',
    name: 'Komikcast',
    scraper: new KomikcastScraper()
}};
"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(js_code)
        print(f"{Fore.GREEN}File {filename} berhasil dibuat.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Gagal membuat file: {e}{Style.RESET_ALL}")

# --- FUNGSI UTAMA (MAIN LOOP) ---
def main():
    driver = None
    proxy_url = ""
    try:
        print_header()
        driver = run_with_loading(setup_driver)
        if not driver: exit()
        
        while True:
            print("") # Spasi
            user_input = input(f"{Style.BRIGHT}{Fore.MAGENTA}DHANY SCRAPE > {Style.RESET_ALL}")
            if user_input.lower() in ['keluar', 'exit', 'quit']:
                break
            if not user_input:
                continue

            command = run_with_loading(parse_command_with_ai, user_input)
            
            if 'error' in command:
                print(f"{Fore.RED}Error: {command['error']}{Style.RESET_ALL}")
            else:
                if command.get('action') == 'generate_js' and not proxy_url:
                    proxy_url = input(f"{Fore.YELLOW}Masukkan URL proxy kamu (contoh: https://proxy-bacayomi.vercel.app/api/proxy): {Style.RESET_ALL}")
                run_with_loading(execute_command, driver, command, proxy_url)

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Program dihentikan oleh user.{Style.RESET_ALL}")
    finally:
        if driver:
            driver.quit()
        print(f"{Fore.CYAN}DHANY SCRAPE terminated.{Style.RESET_ALL}")

def setup_driver():
    """Menyiapkan instance browser Chrome (disembunyikan)."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    try:
        service = Service(executable_path='/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception:
        return None

if __name__ == "__main__":
    main()
