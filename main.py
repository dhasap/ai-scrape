# main.py (Selenium Version)
import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import json
from urllib.parse import urljoin
import time

# --- Import Selenium ---
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

# --- KODE WARNA ANSI UNTUK TAMPILAN CLI ---
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# --- FUNGSI BARU: SETUP SELENIUM DRIVER ---
def setup_driver():
    """Menyiapkan instance browser Chrome untuk dikontrol Selenium."""
    print(f"{Colors.OKCYAN}🔧 Menyiapkan browser virtual (Selenium)...{Colors.ENDC}")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    try:
        service = Service() 
        driver = webdriver.Chrome(service=service, options=options)
        print(f"{Colors.OKGREEN}✅ Browser virtual siap.{Colors.ENDC}")
        return driver
    except Exception as e:
        print(f"{Colors.FAIL}❌ Gagal memulai Selenium WebDriver.{Colors.ENDC}")
        print("Pastikan Google Chrome/Chromium dan ChromeDriver sudah terinstal dengan benar.")
        print(f"Error: {e}")
        exit()

# --- FUNGSI LAMA (TETAP DIGUNAKAN) ---
def extract_links(base_url: str, html_content: str) -> list[dict]:
    """Mengekstrak semua link yang valid dari konten HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        text = a_tag.get_text(strip=True)
        if text and not href.startswith('#') and not href.startswith('javascript:'):
            full_url = urljoin(base_url, href)
            links.append({'text': text, 'href': full_url})
    unique_links = list({link['href']: link for link in links}.values())
    return unique_links

def ask_gemini_to_choose_link(links: list[dict], user_prompt: str) -> str:
    """Meminta Gemini untuk memilih link terbaik berdasarkan instruksi user."""
    if not links: return ""
    max_links = 350
    if len(links) > max_links:
        print(f"{Colors.WARNING}Peringatan: Jumlah link terlalu banyak ({len(links)}). Dibatasi menjadi {max_links} link pertama.{Colors.ENDC}")
        links = links[:max_links]

    prompt_template = f"""
    Anda adalah asisten AI navigasi. Tugas Anda adalah memilih SATU URL terbaik dari daftar JSON yang diberikan berdasarkan permintaan user.
    Permintaan User: "{user_prompt}"
    Daftar Link: {json.dumps(links, indent=2)}
    Pilih URL yang paling relevan. Hanya berikan jawaban berupa URL lengkap. Jika tidak ada yang cocok, jawab "NO_MATCH".
    """
    print(f"\n{Colors.OKBLUE}🤖 Gemini sedang memilih link...{Colors.ENDC}")
    try:
        response = MODEL.generate_content(prompt_template)
        chosen_url = response.text.strip()
        return "" if chosen_url == "NO_MATCH" else chosen_url
    except Exception as e:
        print(f"{Colors.FAIL}Terjadi error saat berkomunikasi dengan Gemini: {e}{Colors.ENDC}")
        return ""

# --- FUNGSI SCRAPE UNIVERSAL DENGAN AI ---
def scrape_comic_details_with_ai(url: str, html_content: str) -> dict:
    """
    Menggunakan AI untuk menganalisis HTML dan mengekstrak detail komik secara dinamis.
    """
    print(f"\n{Colors.OKBLUE}🤖 Menganalisis struktur halaman dengan AI... Ini mungkin butuh beberapa saat.{Colors.ENDC}")
    
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in soup(['script', 'style', 'header', 'footer', 'nav', 'form']):
        tag.decompose()
    clean_html = soup.get_text(separator='\n', strip=True)
    
    max_length = 25000 
    if len(clean_html) > max_length:
        clean_html = clean_html[:max_length]

    prompt = f"""
    Anda adalah seorang ahli web scraping. Analisis teks HTML dari halaman detail komik berikut dan ekstrak informasi ini:
    1. 'judul', 2. 'sinopsis', 3. 'genre' (array of strings), 4. 'details' (object key-value seperti Author, Status, dll), 5. 'rating', 6. 'daftar_chapter' (array of objects, setiap object punya 'chapter' dan 'tanggal_rilis').
    Berikan jawaban HANYA dalam format JSON yang valid.
    --- HTML TEXT ---
    {clean_html}
    --- END HTML TEXT ---
    """

    try:
        response = MODEL.generate_content(prompt)
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(json_text)
        data['url_sumber'] = url
        print(f"{Colors.OKGREEN}✅ AI berhasil menganalisis dan mengekstrak data!{Colors.ENDC}")
        return data
    except Exception as e:
        print(f"{Colors.FAIL}❌ Terjadi error saat AI menganalisis halaman: {e}{Colors.ENDC}")
        return {'error': f'AI gagal memproses halaman ini.'}


def save_to_json(data: dict):
    if 'judul' in data and data['judul']:
        filename = f"{data['judul'].replace(' ', '_').lower()}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"\n{Colors.OKGREEN}💾 Data berhasil disimpan ke file: {filename}{Colors.ENDC}")

def perform_search(driver, query: str):
    """Melakukan pencarian dan mengembalikan status keberhasilan."""
    print(f"{Colors.OKBLUE}🤖 Melakukan pencarian untuk: '{query}'...{Colors.ENDC}")
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
        
        print(f"{Colors.OKGREEN}✅ Halaman hasil pencarian dimuat.{Colors.ENDC}")
        time.sleep(2)
        return True
    except Exception:
        print(f"{Colors.FAIL}❌ Gagal melakukan pencarian.{Colors.ENDC}")
        return False

# --- FUNGSI BARU: MENGEkstrak & MENAMPILKAN HASIL PENCARIAN ---
def scrape_search_results(driver):
    """Mengekstrak judul dan link dari halaman hasil pencarian."""
    print(f"{Colors.OKCYAN}🔍 Mengekstrak hasil pencarian...{Colors.ENDC}")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    results = []
    
    # Selector umum yang mencakup Komikcast dan Komiku
    items = soup.select('.list-update_item, .bge')

    if not items:
        print(f"{Colors.WARNING}⚠️ Tidak dapat menemukan item hasil pencarian di halaman ini.{Colors.ENDC}")
        return []

    for item in items:
        link_tag = item.find('a', href=True)
        title_tag = item.find(['h3', 'h4'])
        
        if link_tag and title_tag:
            title = title_tag.get_text(strip=True)
            href = urljoin(driver.current_url, link_tag['href'])
            results.append({'title': title, 'href': href})
            
    return results

def display_search_results(results, index):
    """Menampilkan 5 hasil pencarian dari indeks yang diberikan."""
    if index >= len(results):
        print(f"\n{Colors.WARNING}-- Tidak ada judul lain untuk ditampilkan --{Colors.ENDC}")
        return index

    print(f"\n{Colors.OKGREEN}Berikut adalah hasil pencarian:{Colors.ENDC}")
    end_index = min(index + 5, len(results))
    for i in range(index, end_index):
        print(f"  {Colors.BOLD}{i + 1}.{Colors.ENDC} {results[i]['title']}")
    
    if end_index < len(results):
        print(f"\n{Colors.OKCYAN}Ketik 'lagi' untuk 5 berikutnya, atau 'pergi ke [nomor]' untuk memilih.{Colors.ENDC}")
    else:
        print(f"\n{Colors.WARNING}-- Akhir dari hasil pencarian --{Colors.ENDC}")
        
    return end_index

# --- FUNGSI UTAMA (DENGAN TAMPILAN BARU) ---
def display_banner():
    """Menampilkan banner ASCII art yang keren."""
    banner = f"""
{Colors.OKBLUE}
   _____   ____ ___ ____ _   _ _____   ____ ___  _   _ _____ ____  
  / _ \ \ / / _` | __ ) | | | ____|  / ___/ _ \| | | | ____|  _ \ 
 | | | \ V / (_| |  _ \| | | |  _|   | |  | | | | | | |  _| | |_) |
 | |_| || | (_| | |_) | |_| | |___   | |__| |_| | |_| | |___|  _ < 
  \___/ |_|\__,_|____/ \___/|_____|   \____\___/ \___/|_____|_| \_\
                                                                  
{Colors.ENDC}
{Colors.HEADER}{Colors.BOLD}📖 Universal AI Comic Scraper v5.0 🤖{Colors.ENDC}
{Colors.OKCYAN}Dengan pencarian interaktif!{Colors.ENDC}
    """
    print(banner)

def main_cli():
    display_banner()
    driver = setup_driver()
    base_url = input(f"{Colors.WARNING}Masukkan URL utama website komik (cth: https://komikcast.lol): {Colors.ENDC}")
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'https://' + base_url
    
    try:
        driver.get(base_url)
    except Exception as e:
        print(f"{Colors.FAIL}Gagal membuka URL: {e}{Colors.ENDC}")
        driver.quit()
        exit()

    print("\n" + "="*50)
    print(f"{Colors.BOLD}Perintah yang tersedia:{Colors.ENDC}")
    print(f"  {Colors.OKGREEN}pergi cari [judul]{Colors.ENDC} - Mencari komik & menampilkan hasil.")
    print(f"  {Colors.OKGREEN}pergi ke [judul/no]{Colors.ENDC} - Langsung ke detail komik / pilih dari hasil cari.")
    print(f"  {Colors.OKGREEN}pergi [menu]{Colors.ENDC}      - Navigasi ke menu (e.g., pergi ke daftar komik).")
    print(f"  {Colors.OKGREEN}lagi{Colors.ENDC}                - Tampilkan 5 hasil pencarian berikutnya.")
    print(f"  {Colors.OKGREEN}scrape{Colors.ENDC}              - Ambil detail dari halaman saat ini.")
    print(f"  {Colors.OKGREEN}url{Colors.ENDC}                 - Tampilkan URL halaman saat ini.")
    print(f"  {Colors.OKGREEN}keluar{Colors.ENDC}              - Keluar dari program.")
    print("="*50)

    # State untuk hasil pencarian
    search_results = []
    search_results_index = 0

    while True:
        try:
            current_url = driver.current_url
            prompt = f"\n{Colors.BOLD}📍 Lokasi saat ini:{Colors.ENDC} {Colors.UNDERLINE}{current_url}{Colors.ENDC}\n{Colors.WARNING}> {Colors.ENDC}"
            user_input = input(prompt).strip().lower()
            
            if not user_input: continue

            if user_input.startswith("pergi "):
                instruction = user_input[6:].strip()
                if not instruction:
                    print(f"{Colors.FAIL}Mohon berikan instruksi.{Colors.ENDC}")
                    continue
                
                # Reset state pencarian jika ada navigasi baru
                search_results = []
                search_results_index = 0

                search_keyword = None
                if "cari" in instruction:
                    search_keyword = "cari"
                elif "search" in instruction:
                    search_keyword = "search"

                if search_keyword:
                    query = instruction.split(search_keyword, 1)[1].strip()
                    if perform_search(driver, query):
                        search_results = scrape_search_results(driver)
                        search_results_index = display_search_results(search_results, 0)
                else:
                    target = instruction.replace("ke", "").strip()
                    if target.isdigit() and search_results:
                        index = int(target) - 1
                        if 0 <= index < len(search_results):
                            driver.get(search_results[index]['href'])
                            search_results = [] # Reset setelah memilih
                        else:
                            print(f"{Colors.FAIL}Nomor tidak valid.{Colors.ENDC}")
                    else:
                        common_nav_terms = ["daftar", "list", "proyek", "genre", "home", "beranda", "project"]
                        if any(term in instruction for term in common_nav_terms):
                            html = driver.page_source
                            links = extract_links(current_url, html)
                            chosen_url = ask_gemini_to_choose_link(links, instruction)
                            if chosen_url: driver.get(chosen_url)
                            else: print(f"{Colors.FAIL}❌ AI tidak dapat menemukan link yang cocok.{Colors.ENDC}")
                        else:
                            # Langsung cari dan navigasi
                            if perform_search(driver, target):
                                html = driver.page_source
                                links = extract_links(driver.current_url, html)
                                chosen_url = ask_gemini_to_choose_link(links, f"Pilih link untuk '{target}'")
                                if chosen_url: driver.get(chosen_url)
                                else: print(f"{Colors.FAIL}❌ AI tidak bisa menentukan hasil terbaik.{Colors.ENDC}")
            
            elif user_input == "lagi":
                if not search_results:
                    print(f"{Colors.FAIL}Lakukan pencarian dulu dengan 'pergi cari [judul]'.{Colors.ENDC}")
                else:
                    search_results_index = display_search_results(search_results, search_results_index)

            elif user_input == "scrape":
                comic_data = scrape_comic_details_with_ai(driver.current_url, driver.page_source)
                if 'error' in comic_data:
                    print(f"{Colors.FAIL}❌ {comic_data['error']}{Colors.ENDC}")
                else:
                    print(json.dumps(comic_data, indent=2, ensure_ascii=False))
                    save_prompt = input(f"\n{Colors.WARNING}Simpan ke file JSON? (y/n): {Colors.ENDC}").lower()
                    if save_prompt == 'y':
                        save_to_json(comic_data)

            elif user_input == "url":
                print(f"URL saat ini adalah: {driver.current_url}")

            elif user_input == "keluar":
                break
                
            else:
                print(f"{Colors.FAIL}Perintah tidak dikenali.{Colors.ENDC}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n{Colors.FAIL}Terjadi kesalahan tak terduga: {e}{Colors.ENDC}")
            continue
    
    print(f"\n{Colors.OKCYAN}Menutup browser virtual... Sampai jumpa!{Colors.ENDC}")
    driver.quit()

if __name__ == "__main__":
    main_cli()
