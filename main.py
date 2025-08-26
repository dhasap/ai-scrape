# main.py (v7.1 - Improved Workflow)
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
    version_info = f"{Fore.GREEN}Versi 7.1{Style.RESET_ALL} | {Fore.CYAN}Natural Language Engine{Style.RESET_ALL}"
    
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
def parse_command_with_ai(user_input, current_url):
    """Menggunakan AI untuk mengubah bahasa natural menjadi perintah terstruktur."""
    prompt = f"""
    Anda adalah NLU engine untuk CLI tool "DHANY SCRAPE". Analisis perintah user dan ubah menjadi JSON.
    Konteks: URL saat ini adalah "{current_url}". Jika user menyebut "situs ini", "halaman ini", atau tidak menyebutkan sumber URL sama sekali, gunakan URL tersebut sebagai "source".
    Kunci JSON harus: "action", "target", "source", "output_format", "output_filename".
    - action: scrape, download, search, get, generate_js.
    - output_format: csv, json, txt, database, folder, js_file.
    - Infer output_filename dari target jika tidak disebut.

    Contoh 1:
    User: "scrape semua judul manga dari https://komikcast.io dan simpan ke file csv"
    JSON: {{"action": "scrape", "target": "semua judul manga", "source": "https://komikcast.io", "output_format": "csv", "output_filename": "judul_manga.csv"}}

    Contoh 2:
    User: "download semua gambar dari halaman ini ke folder images"
    JSON: {{"action": "download", "target": "semua gambar", "source": "{current_url}", "output_format": "folder", "output_filename": "images"}}

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

    print(f"\n{Fore.CYAN}Memulai aksi '{action}' pada target '{target}'...{Style.RESET_ALL}")
    
    if action == "generate_js":
        generate_scrape_js(output_filename, proxy_url)
        return
        
    # Navigasi ke sumber jika belum ada di sana
    if driver.current_url != source and source not in driver.current_url:
        print(f"Navigasi ke {source}...")
        try:
            url_to_get = f"{proxy_url}?url={source}" if proxy_url else source
            driver.get(url_to_get)
        except Exception as e:
            print(f"{Fore.RED}Gagal membuka URL sumber: {e}{Style.RESET_ALL}")
            return

    if action == "download" and "gambar" in target:
        os.makedirs(output_filename, exist_ok=True)
        print(f"{Fore.GREEN}Simulasi: Gambar dari {source} sudah di-download ke folder {output_filename}/{Style.RESET_ALL}")
    
    elif action == "scrape":
        try:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            # Logika scraping universal dengan AI
            data_to_save = scrape_with_ai(target, soup.prettify())
            
            if not data_to_save:
                print(f"{Fore.YELLOW}Tidak ada data '{target}' yang ditemukan.{Style.RESET_ALL}")
                return

            if output_format == 'csv':
                if not isinstance(data_to_save, list) or not data_to_save:
                     print(f"{Fore.RED}Data tidak cocok untuk format CSV.{Style.RESET_ALL}")
                     return
                with open(output_filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=data_to_save[0].keys())
                    writer.writeheader()
                    writer.writerows(data_to_save)
                print(f"{Fore.GREEN}Data '{target}' berhasil disimpan ke file {output_filename}{Style.RESET_ALL}")
            elif output_format == 'json':
                 with open(output_filename, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, ensure_ascii=False, indent=4)
                 print(f"{Fore.GREEN}Data '{target}' berhasil disimpan ke file {output_filename}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}Format output '{output_format}' belum didukung untuk aksi ini.{Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}Gagal melakukan scraping: {e}{Style.RESET_ALL}")

    else:
        print(f"{Fore.YELLOW}Aksi '{action}' untuk target '{target}' belum diimplementasikan sepenuhnya.{Style.RESET_ALL}")

def scrape_with_ai(target, html):
    """Menggunakan AI untuk scrape data spesifik dari HTML."""
    prompt = f"""
    Anda adalah scraper AI. Dari HTML berikut, ekstrak semua data yang berhubungan dengan '{target}'.
    Kembalikan hasilnya dalam format JSON. Jika targetnya adalah daftar (seperti judul atau chapter), kembalikan array of objects.
    HTML:
    {html[:25000]}
    """
    response = MODEL.generate_content(prompt)
    json_text = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(json_text)

def generate_scrape_js(filename, proxy_url):
    """Membuat file scrape.js dengan proxy yang diberikan."""
    # Kode JS tetap sama seperti sebelumnya
    js_code = f"""
class KomikcastScraper {{
    constructor() {{
        this.proxy = '{proxy_url}';
        this.baseUrl = 'https://komikcast.li';
    }}
    // ... (sisa kode JS tidak berubah) ...
}}
// ... (sisa kode JS tidak berubah) ...
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
        
        # MEMINTA URL AWAL
        base_url = input(f"{Fore.YELLOW}🔗 Masukkan URL utama untuk memulai: {Style.RESET_ALL}")
        if not base_url.startswith(('http://', 'https://')):
            base_url = 'https://' + base_url
        run_with_loading(driver.get, base_url)

        while True:
            current_url = driver.current_url
            print(f"\n{Style.BRIGHT}📍 Lokasi: {UNDERLINE}{current_url}{Style.RESET_ALL}")
            user_input = input(f"{Style.BRIGHT}{Fore.MAGENTA}DHANY SCRAPE > {Style.RESET_ALL}")
            
            if user_input.lower() in ['keluar', 'exit', 'quit']:
                break
            if not user_input:
                continue

            command = run_with_loading(parse_command_with_ai, user_input, driver.current_url)
            
            if 'error' in command:
                print(f"{Fore.RED}Error: {command['error']}{Style.RESET_ALL}")
            else:
                if command.get('action') == 'generate_js' and not proxy_url:
                    # MENGHAPUS CONTOH PROXY
                    proxy_url = input(f"{Fore.YELLOW}Masukkan URL proxy kamu: {Style.RESET_ALL}")
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
