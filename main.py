# main.py (v8.5 - Advanced Page Load Detection)
import os
import json
import time
import sys
import threading
import re
from urllib.parse import urljoin

import google.generativeai as genai
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

def print_header(driver):
    os.system('cls' if os.name == 'nt' else 'clear')
    ascii_art = pyfiglet.figlet_format('DHANY SCRAPE', font='slant')
    width = max(len(line) for line in ascii_art.strip('\n').split('\n')) + 4
    tagline = "😈 Dhany adalah Raja Iblis 👑"
    version_info = f"{Fore.GREEN}Versi 8.5{Style.RESET_ALL} | {Fore.CYAN}Autonomous Agent{Style.RESET_ALL}"
    
    print(f"{Fore.BLUE}{Style.BRIGHT}╔{'═' * width}╗{Style.RESET_ALL}")
    for line in ascii_art.strip('\n').split('\n'):
        print(f"{Fore.BLUE}{Style.BRIGHT}║ {line.center(width - 2)} ║{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{Style.BRIGHT}║{' ' * width}║{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{Style.BRIGHT}║{Style.NORMAL}{Fore.MAGENTA}{Style.BRIGHT}{tagline.center(width)}{Style.RESET_ALL}{Fore.BLUE}{Style.BRIGHT}║")
    print(f"{Fore.BLUE}{Style.BRIGHT}║{version_info.center(width + 10)}{Fore.BLUE}{Style.BRIGHT}║")
    print(f"{Fore.BLUE}{Style.BRIGHT}╚{'═' * width}╝{Style.RESET_ALL}")
    if driver:
        print(f"\n{Style.BRIGHT}📍 Lokasi Saat Ini:{Style.RESET_ALL} {UNDERLINE}{driver.current_url}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═' * (width + 2)}{Style.RESET_ALL}")

# --- OTAK AI: PERENCANA AKSI ---
def tag_interactive_elements(driver):
    """Menyuntikkan atribut 'data-ai-id' ke elemen interaktif di halaman."""
    js_script = """
    const elements = document.querySelectorAll('a, button, input[type="submit"], input[type="text"], input[type="search"]');
    elements.forEach((el, index) => {
        el.setAttribute('data-ai-id', `ai-id-${index}`);
    });
    return document.documentElement.outerHTML;
    """
    return driver.execute_script(js_script)

def get_element_map(soup):
    """Mengekstrak 'peta' elemen interaktif yang sudah dilabeli."""
    elements = []
    for el in soup.find_all(attrs={"data-ai-id": True}):
        tag = el.name
        text = el.get_text(strip=True)
        ai_id = el['data-ai-id']
        
        element_info = {"ai_id": ai_id, "tag": tag}
        if text:
            element_info["text"] = text
        
        if tag == 'a' and el.has_attr('href'):
            element_info["href"] = el['href']
        if tag == 'input' and el.has_attr('placeholder'):
            element_info["placeholder"] = el['placeholder']
            
        elements.append(element_info)
    return elements

def get_next_action_with_ai(goal, current_url, element_map):
    """AI menentukan langkah berikutnya berdasarkan 'peta' elemen yang sudah dilabeli."""
    prompt = f"""
    Anda adalah otak dari agen web scraper otonom.
    Tujuan akhir Anda: "{goal}"
    Posisi Anda saat ini: "{current_url}"

    Tugas Anda adalah memilih SATU langkah berikutnya yang paling efisien berdasarkan "peta elemen" di bawah ini.
    Pilih salah satu dari aksi berikut dan kembalikan dalam format JSON:
    1. {{ "action": "type", "ai_id": "ID_ELEMEN", "text": "TEKS_UNTUK_DIKETIK" }}: Jika Anda perlu mengetik di kolom pencarian.
    2. {{ "action": "click", "ai_id": "ID_ELEMEN" }}: Jika Anda perlu mengklik link atau tombol.
    3. {{ "action": "scrape" }}: HANYA jika Anda YAKIN sudah berada di halaman yang berisi semua informasi yang dibutuhkan.
    4. {{ "action": "fail", "reason": "ALASAN_GAGAL" }}: Jika Anda buntu.

    Pilih 'ai_id' dari elemen yang paling relevan di peta. JANGAN BUAT SELECTOR SENDIRI.
    Peta Elemen Interaktif di Halaman Saat Ini:
    ---
    {json.dumps(element_map[:150], indent=2)}
    ---
    Berdasarkan tujuan dan peta elemen di atas, tentukan langkah berikutnya.
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
    max_steps = 10
    for step in range(max_steps):
        print(f"\n{Style.BRIGHT}--- Langkah {step + 1}/{max_steps} ---{Style.RESET_ALL}")
        print(f"📍 Lokasi: {driver.current_url}")

        # Labeli elemen dan buat peta
        html_with_ids = tag_interactive_elements(driver)
        soup = BeautifulSoup(html_with_ids, 'html.parser')
        element_map = get_element_map(soup)

        action_plan = run_with_loading(get_next_action_with_ai, goal, driver.current_url, element_map)
        action = action_plan.get('action')

        try:
            if action in ["type", "click"]:
                ai_id = action_plan.get('ai_id')
                selector = f"[data-ai-id='{ai_id}']"
                
                # Simpan referensi elemen halaman lama untuk mendeteksi perubahan
                old_html_element = driver.find_element(By.TAG_NAME, "html")
                
                element = driver.find_element(By.CSS_SELECTOR, selector)
                
                if action == "type":
                    text = action_plan.get('text')
                    print(f"🤖 Aksi: Mengetik '{text}' pada elemen '{ai_id}'")
                    element.clear()
                    element.send_keys(text)
                    element.send_keys(Keys.RETURN)
                elif action == "click":
                    print(f"🤖 Aksi: Mengklik elemen '{ai_id}'")
                    element.click()
                
                # --- PERBAIKAN KUNCI: ADVANCED SMART WAIT ---
                print("⏳ Menunggu halaman baru dimuat...")
                WebDriverWait(driver, 15).until(
                    EC.staleness_of(old_html_element)
                )
                print("✅ Halaman baru berhasil dimuat.")

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
                return

            elif action == "fail":
                print(f"{Fore.RED}❌ Agen gagal: {action_plan.get('reason')}{Style.RESET_ALL}")
                return

            else:
                print(f"{Fore.RED}❌ Aksi tidak dikenali: {action}{Style.RESET_ALL}")
                return
        except Exception as e:
            print(f"{Fore.RED}Gagal melakukan aksi '{action}': {e}{Style.RESET_ALL}")
            break
            
    print(f"{Fore.YELLOW}⚠️ Agen mencapai batas langkah maksimum.{Style.RESET_ALL}")


# --- FUNGSI UTAMA ---
def main():
    driver = None
    try:
        print_header(None)
        driver = setup_driver()
        if not driver: exit()
        
        start_url = input(f"{Fore.YELLOW}🔗 Masukkan URL awal untuk memulai (e.g., https://komikcast.li): {Style.RESET_ALL}")
        if not start_url.startswith(('http://', 'https://')):
            start_url = 'https://' + start_url
        
        print(f"Memulai dari: {start_url}")
        driver.get(start_url)
        time.sleep(2)

        while True:
            print_header(driver)
            user_goal = input(f"{Style.BRIGHT}{Fore.MAGENTA}DHANY SCRAPE > {Style.RESET_ALL}")
            if user_goal.lower() in ['keluar', 'exit', 'quit']:
                break
            if not user_goal:
                continue
            
            match = re.search(r'https?://[^\s]+', user_goal)
            if match:
                new_url = match.group(0)
                if new_url != driver.current_url:
                    print(f"Mengganti lokasi ke: {new_url}")
                    driver.get(new_url)
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
