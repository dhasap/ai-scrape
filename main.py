# main.py (v8.0 - Autonomous Agent)
import os
import json
import time
import sys
import threading
from urllib.parse import urljoin

import google.generativeai as genai
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

import pyfiglet
from colorama import init, Fore, Style

# Inisialisasi Colorama
init(autoreset=True)

# --- KONFIGURASI ---
try:
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("API Key Gemini tidak ditemukan.")
    genai.configure(api_key=GEMINI_API_KEY)
except ValueError as e:
    print(e)
    exit()

MODEL = genai.GenerativeModel('gemini-1.5-flash')

# --- FUNGSI TAMPILAN & ANIMASI ---
LOADING_EVENT = threading.Event()
UNDERLINE = '\033[4m'

def spinner_animation():
    spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    while not LOADING_EVENT.is_set():
        for char in spinner_chars:
            sys.stdout.write(f'\r{Fore.CYAN}{char} {Style.RESET_ALL}AI sedang berpikir... ')
            sys.stdout.flush()
            time.sleep(0.1)
            if LOADING_EVENT.is_set():
                break
    sys.stdout.write('\r' + ' ' * 30 + '\r')
    sys.stdout.flush()

def run_with_loading(target_func, *args, **kwargs):
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
    os.system('cls' if os.name == 'nt' else 'clear')
    ascii_art = pyfiglet.figlet_format('DHANY SCRAPE', font='slant')
    width = max(len(line) for line in ascii_art.strip('\n').split('\n')) + 4
    tagline = "😈 Dhany adalah Raja Iblis 👑"
    version_info = f"{Fore.GREEN}Versi 8.0{Style.RESET_ALL} | {Fore.CYAN}Autonomous Agent{Style.RESET_ALL}"
    
    print(f"{Fore.BLUE}{Style.BRIGHT}╔{'═' * width}╗{Style.RESET_ALL}")
    for line in ascii_art.strip('\n').split('\n'):
        print(f"{Fore.BLUE}{Style.BRIGHT}║ {line.center(width - 2)} ║{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{Style.BRIGHT}║{' ' * width}║{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{Style.BRIGHT}║{Style.NORMAL}{Fore.MAGENTA}{Style.BRIGHT}{tagline.center(width)}{Style.RESET_ALL}{Fore.BLUE}{Style.BRIGHT}║")
    print(f"{Fore.BLUE}{Style.BRIGHT}║{version_info.center(width + 10)}{Fore.BLUE}{Style.BRIGHT}║")
    print(f"{Fore.BLUE}{Style.BRIGHT}╚{'═' * width}╝{Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}Contoh: 'Scrape semua info Solo Leveling di komikcast'{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═' * (width + 2)}{Style.RESET_ALL}")

# --- OTAK AI: PERENCANA AKSI ---
def get_next_action_with_ai(goal, current_url, clean_html):
    """AI menentukan langkah berikutnya untuk mencapai tujuan."""
    prompt = f"""
    Anda adalah otak dari agen web scraper otonom.
    Tujuan akhir Anda: "{goal}"
    Posisi Anda saat ini: "{current_url}"

    Tugas Anda adalah menentukan SATU langkah berikutnya yang paling efisien.
    Pilih salah satu dari aksi berikut dan kembalikan dalam format JSON:
    1. {{ "action": "type", "selector": "CSS_SELECTOR", "text": "TEKS_UNTUK_DIKETIK" }}: Jika Anda perlu mengetik di kolom pencarian.
    2. {{ "action": "click", "selector": "CSS_SELECTOR" }}: Jika Anda perlu mengklik link atau tombol untuk lebih dekat ke tujuan.
    3. {{ "action": "scrape", "target": "DETAIL_TARGET" }}: HANYA jika Anda YAKIN sudah berada di halaman yang berisi semua informasi yang dibutuhkan.
    4. {{ "action": "finish", "data": "Tujuan tercapai." }}: Jika tugas sudah selesai.
    5. {{ "action": "fail", "reason": "ALASAN_GAGAL" }}: Jika Anda buntu atau tidak bisa menemukan informasi.

    Gunakan selector CSS yang umum dan andal.
    HTML halaman saat ini (disederhanakan):
    ---
    {clean_html[:15000]}
    ---
    Berdasarkan tujuan dan HTML di atas, tentukan langkah berikutnya.
    """
    try:
        response = MODEL.generate_content(prompt)
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_text)
    except Exception:
        return {'action': 'fail', 'reason': 'Gagal memproses respons dari AI.'}

def scrape_details_with_ai(goal, html_content):
    """AI mengekstrak semua data detail dari halaman final."""
    prompt = f"""
    Anda adalah ahli scraper. Tujuan scraping adalah: "{goal}".
    Dari HTML berikut, ekstrak semua informasi relevan (judul, author, genre, type, status, tanggal rilis, rating, sinopsis, daftar chapter) ke dalam format JSON yang konsisten.
    HTML:
    ---
    {html_content[:25000]}
    ---
    """
    try:
        response = MODEL.generate_content(prompt)
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_text)
    except Exception as e:
        return {'error': f'AI gagal mengekstrak detail: {e}'}

# --- EKSEKUTOR AKSI ---
def execute_agent_loop(driver, goal):
    """Menjalankan loop agen otonom hingga tujuan tercapai."""
    max_steps = 10  # Mencegah loop tak terbatas
    for step in range(max_steps):
        print(f"\n{Style.BRIGHT}--- Langkah {step + 1}/{max_steps} ---{Style.RESET_ALL}")
        print(f"📍 Lokasi: {driver.current_url}")

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        for tag in soup(['script', 'style', 'header', 'footer', 'nav']):
            tag.decompose()
        clean_html = soup.get_text(separator='\n', strip=True)

        action_plan = run_with_loading(get_next_action_with_ai, goal, driver.current_url, clean_html)
        action = action_plan.get('action')

        if action == "type":
            selector = action_plan.get('selector')
            text = action_plan.get('text')
            print(f"🤖 Aksi: Mengetik '{text}' pada '{selector}'")
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                element.clear()
                element.send_keys(text)
                element.send_keys(Keys.RETURN)
                time.sleep(3)
            except Exception as e:
                print(f"{Fore.RED}Gagal melakukan aksi 'type': {e}{Style.RESET_ALL}")
                break

        elif action == "click":
            selector = action_plan.get('selector')
            print(f"🤖 Aksi: Mengklik elemen '{selector}'")
            try:
                driver.find_element(By.CSS_SELECTOR, selector).click()
                time.sleep(3)
            except Exception as e:
                print(f"{Fore.RED}Gagal melakukan aksi 'click': {e}{Style.RESET_ALL}")
                break

        elif action == "scrape":
            print(f"🤖 Aksi: Scraping detail dari halaman saat ini...")
            final_data = run_with_loading(scrape_details_with_ai, goal, driver.page_source)
            if 'error' in final_data:
                print(f"{Fore.RED}❌ {final_data['error']}{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}✅ Scraping Selesai!{Style.RESET_ALL}")
                print(json.dumps(final_data, indent=2, ensure_ascii=False))
                if input(f"{Fore.YELLOW}Simpan ke file JSON? (y/n): {Style.RESET_ALL}").lower() == 'y':
                    filename = goal.split(' ')[-1].lower() + ".json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(final_data, f, ensure_ascii=False, indent=4)
                    print(f"{Fore.GREEN}💾 Data berhasil disimpan ke: {filename}{Style.RESET_ALL}")
            return # Keluar dari loop setelah scraping

        elif action == "finish":
            print(f"{Fore.GREEN}✅ Tujuan tercapai: {action_plan.get('data')}{Style.RESET_ALL}")
            return

        elif action == "fail":
            print(f"{Fore.RED}❌ Agen gagal: {action_plan.get('reason')}{Style.RESET_ALL}")
            return

        else:
            print(f"{Fore.RED}❌ Aksi tidak dikenali: {action}{Style.RESET_ALL}")
            return
            
    print(f"{Fore.YELLOW}⚠️ Agen mencapai batas langkah maksimum.{Style.RESET_ALL}")


# --- FUNGSI UTAMA ---
def main():
    driver = None
    try:
        print_header()
        driver = setup_driver()
        if not driver: exit()
        
        while True:
            print("")
            user_goal = input(f"{Style.BRIGHT}{Fore.MAGENTA}DHANY SCRAPE > {Style.RESET_ALL}")
            if user_goal.lower() in ['keluar', 'exit', 'quit']:
                break
            if not user_goal:
                continue
            
            # Ekstrak URL awal jika ada, jika tidak, mulai dari halaman default
            match = re.search(r'https?://[^\s]+', user_goal)
            start_url = "https://google.com" # Fallback jika tidak ada URL
            if match:
                start_url = match.group(0)
            
            print(f"Memulai dari: {start_url}")
            driver.get(start_url)
            time.sleep(2)

            execute_agent_loop(driver, user_goal)
            print(f"\n{Fore.CYAN}{'═' * 74}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Tugas selesai. Siap menerima perintah baru.{Style.RESET_ALL}")


    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Program dihentikan.{Style.RESET_ALL}")
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
