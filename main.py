# main.py (v6.0 - Dashboard UI)
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
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

# --- KODE WARNA & GAYA TAMPILAN ---
class Style:
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# --- FUNGSI TAMPILAN & ANIMASI ---
LOADING_EVENT = threading.Event()

def clear_screen():
    """Membersihkan layar terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def spinner_animation():
    """Menampilkan animasi loading spinner."""
    spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    while not LOADING_EVENT.is_set():
        for char in spinner_chars:
            sys.stdout.write(f'\r{Style.CYAN}{char} {Style.END}Sedang memproses... ')
            sys.stdout.flush()
            time.sleep(0.1)
            if LOADING_EVENT.is_set():
                break
    sys.stdout.write('\r' + ' ' * 30 + '\r') # Hapus baris spinner
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

def print_header(driver):
    """Menampilkan header dashboard."""
    clear_screen()
    header = f"""
{Style.BLUE}╔══════════════════════════════════════════════════════════════════════════════╗
║{Style.BOLD} ____  _   _    _    _   ___   __  ____   ____ ____     _    ____  _____ {Style.END}{Style.BLUE}║
║{Style.BOLD}|  _ \| | | |  / \  | \ | \ \ / / / ___| / ___|  _ \   / \  |  _ \| ____|{Style.END}{Style.BLUE}║
║{Style.BOLD}| | | | |_| | / _ \ |  \| |\ V /  \___ \| |   | |_) | / _ \ | |_) |  _|  {Style.END}{Style.BLUE}║
║{Style.BOLD}| |_| |  _  |/ ___ \| |\  | | |    ___) | |___|  _ < / ___ \|  __/| |___ {Style.END}{Style.BLUE}║
║{Style.BOLD}|____/|_| |_/_/   \_|_| \_| |_|   |____/ \____|_| \_/_/   \_|_|   |_____|{Style.END}{Style.BLUE}║
║                                                                              ║
║{' ' * 21}{Style.PURPLE}{Style.BOLD}😈 Dhany adalah Raja Iblis 👑{Style.END}{Style.BLUE}{' ' * 22}║
╚══════════════════════════════════════════════════════════════════════════════╝{Style.END}
    """
    print(header)
    if driver:
        print(f"{Style.BOLD}📍 Lokasi Saat Ini:{Style.END} {Style.UNDERLINE}{driver.current_url}{Style.END}")
    print(f"{Style.CYAN}{'═'*74}{Style.END}")

# --- FUNGSI INTI (Logika tidak berubah, hanya ditambah pewarnaan) ---
def setup_driver():
    """Menyiapkan instance browser Chrome."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    try:
        service = Service(executable_path='/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        print(f"{Style.RED}❌ Gagal memulai Selenium WebDriver: {e}{Style.END}")
        exit()

def extract_links(base_url, html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        text = a_tag.get_text(strip=True)
        if text and not href.startswith(('#', 'javascript:')):
            full_url = urljoin(base_url, href)
            links.append({'text': text, 'href': full_url})
    return list({link['href']: link for link in links}.values())

def ask_gemini_to_choose_link(links, user_prompt):
    if not links: return ""
    max_links = 350
    if len(links) > max_links:
        print(f"{Style.YELLOW}⚠️ Peringatan: Jumlah link terlalu banyak, dibatasi {max_links} pertama.{Style.END}")
        links = links[:max_links]
    prompt = f"Permintaan: '{user_prompt}'. Pilih SATU URL paling relevan dari JSON ini. Jawab HANYA URL-nya. Jika tidak ada, jawab 'NO_MATCH'.\n{json.dumps(links)}"
    try:
        response = MODEL.generate_content(prompt)
        return "" if response.text.strip() == "NO_MATCH" else response.text.strip()
    except Exception:
        return ""

def scrape_comic_details_with_ai(url, html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in soup(['script', 'style', 'header', 'footer', 'nav', 'form']):
        tag.decompose()
    clean_html = soup.get_text(separator='\n', strip=True)[:25000]
    prompt = f"Anda adalah ahli scraping. Analisis HTML ini dan ekstrak: judul, sinopsis, genre, details (objek), rating, dan daftar_chapter (array objek). Jawab HANYA dalam format JSON valid.\nHTML:\n{clean_html}"
    try:
        response = MODEL.generate_content(prompt)
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(json_text)
        data['url_sumber'] = url
        return data
    except Exception as e:
        return {'error': f'AI gagal memproses halaman ini. Detail: {e}'}

def save_to_json(data):
    if 'judul' in data and data['judul']:
        filename = f"{data['judul'].replace(' ', '_').lower()}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"\n{Style.GREEN}💾 Data berhasil disimpan ke: {filename}{Style.END}")

def perform_search(driver, query):
    try:
        wait = WebDriverWait(driver, 10)
        search_input_selector = "input[type='search'], input[type='text'][name*='s'], input.cari, .search-form .search-field"
        try:
            search_button = driver.find_element(By.CSS_SELECTOR, "a.search_button, button.search-button")
            search_button.click()
            time.sleep(0.5)
        except NoSuchElementException:
            pass
        search_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, search_input_selector)))
        search_input.clear()
        search_input.send_keys(query)
        search_input.send_keys(Keys.RETURN)
        time.sleep(2)
        return True
    except Exception:
        return False

def scrape_search_results(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    results = []
    items = soup.select('.list-update_item, .bge')
    for item in items:
        link_tag = item.find('a', href=True)
        title_tag = item.find(['h3', 'h4'])
        if link_tag and title_tag:
            results.append({'title': title_tag.get_text(strip=True), 'href': urljoin(driver.current_url, link_tag['href'])})
    return results

def display_search_results(results, index):
    if index >= len(results):
        print(f"\n{Style.YELLOW}-- Tidak ada judul lain untuk ditampilkan --{Style.END}")
        return index, False
    print(f"\n{Style.GREEN}📖 Berikut adalah hasil pencarian:{Style.END}")
    end_index = min(index + 5, len(results))
    for i in range(index, end_index):
        print(f"  {Style.BOLD}{i + 1}.{Style.END} {results[i]['title']}")
    has_more = end_index < len(results)
    if has_more:
        print(f"\n{Style.CYAN}Pilih nomor atau ketik '6' untuk melihat 5 berikutnya.{Style.END}")
    else:
        print(f"\n{Style.YELLOW}-- Akhir dari hasil pencarian --{Style.END}")
    return end_index, has_more

# --- FUNGSI UTAMA (MAIN LOOP) ---
def main_cli():
    driver = run_with_loading(setup_driver)
    if not driver: exit()
    
    print_header(None)
    base_url = input(f"{Style.YELLOW}🔗 Masukkan URL utama website komik: {Style.END}")
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'https://' + base_url
    run_with_loading(driver.get, base_url)

    search_results, search_results_index, has_more_results = [], 0, False

    while True:
        print_header(driver)
        
        # Tampilkan menu dinamis berdasarkan konteks pencarian
        if search_results:
            print(f"{Style.BOLD}🔎 Opsi Hasil Pencarian:{Style.END}")
            for i in range(search_results_index - 5, search_results_index):
                if i < len(search_results):
                    print(f"  {Style.GREEN}[{i + 1}] {search_results[i]['title'][:60]}{Style.END}")
            if has_more_results:
                print(f"  {Style.CYAN}[6] Lihat 5 berikutnya...{Style.END}")
            print(f"  {Style.YELLOW}[7] Lakukan pencarian baru{Style.END}")
            print(f"  {Style.RED}[8] Keluar{Style.END}")
        else:
            print(f"{Style.BOLD}MENU UTAMA:{Style.END}")
            print(f"  {Style.CYAN}[1] 🔍 Cari Komik (dan tampilkan hasil){Style.END}")
            print(f"  {Style.CYAN}[2] 🚀 Langsung ke Judul Komik{Style.END}")
            print(f"  {Style.CYAN}[3] 🧭 Navigasi Menu (e.g., daftar komik){Style.END}")
            print(f"  {Style.GREEN}[4] 📊 Scrape Halaman Saat Ini{Style.END}")
            print(f"  {Style.RED}[5] 🚪 Keluar{Style.END}")

        print(f"{Style.CYAN}{'═'*74}{Style.END}")
        choice = input(f"{Style.BOLD}{Style.YELLOW}Pilih Opsi: {Style.END}")

        # Logika berdasarkan pilihan
        if search_results: # Konteks hasil pencarian
            if choice == '6' and has_more_results:
                search_results_index, has_more_results = display_search_results(search_results, search_results_index)
            elif choice == '7':
                search_results, search_results_index, has_more_results = [], 0, False
            elif choice == '8':
                break
            elif choice.isdigit() and 1 <= int(choice) <= search_results_index:
                run_with_loading(driver.get, search_results[int(choice) - 1]['href'])
                search_results, search_results_index, has_more_results = [], 0, False
            else:
                print(f"{Style.RED}Pilihan tidak valid.{Style.END}"); time.sleep(1)
        else: # Konteks menu utama
            if choice == '1':
                query = input(f"{Style.YELLOW}   ╚═► Judul yang dicari: {Style.END}")
                if run_with_loading(perform_search, driver, query):
                    search_results = run_with_loading(scrape_search_results, driver)
                    search_results_index, has_more_results = display_search_results(search_results, 0)
            elif choice == '2':
                query = input(f"{Style.YELLOW}   ╚═► Judul yang dituju: {Style.END}")
                if run_with_loading(perform_search, driver, query):
                    html = driver.page_source
                    links = extract_links(driver.current_url, html)
                    prompt = f"Pilih link untuk '{query}'"
                    chosen_url = run_with_loading(ask_gemini_to_choose_link, links, prompt)
                    if chosen_url: run_with_loading(driver.get, chosen_url)
                    else: print(f"{Style.RED}AI tidak bisa menentukan hasil terbaik.{Style.END}"); time.sleep(2)
            elif choice == '3':
                query = input(f"{Style.YELLOW}   ╚═► Menu yang dituju (e.g., daftar komik): {Style.END}")
                html = driver.page_source
                links = extract_links(driver.current_url, html)
                chosen_url = run_with_loading(ask_gemini_to_choose_link, links, query)
                if chosen_url: run_with_loading(driver.get, chosen_url)
                else: print(f"{Style.RED}AI tidak dapat menemukan link yang cocok.{Style.END}"); time.sleep(2)
            elif choice == '4':
                data = run_with_loading(scrape_comic_details_with_ai, driver.current_url, driver.page_source)
                if 'error' in data:
                    print(f"{Style.RED}❌ {data['error']}{Style.END}")
                else:
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    if input(f"{Style.YELLOW}Simpan ke file JSON? (y/n): {Style.END}").lower() == 'y':
                        save_to_json(data)
                input("\nTekan Enter untuk kembali ke menu...")
            elif choice == '5':
                break
            else:
                print(f"{Style.RED}Pilihan tidak valid.{Style.END}"); time.sleep(1)

    print(f"\n{Style.CYAN}Menutup browser virtual... Sampai jumpa!{Style.END}")
    driver.quit()

if __name__ == "__main__":
    main_cli()
