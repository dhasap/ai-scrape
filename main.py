# main.py
import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import json
from urllib.parse import urljoin

# --- KONFIGURASI ---
# Pastikan Anda sudah mengatur environment variable bernama 'GEMINI_API_KEY'
# dengan API Key Gemini Anda.
try:
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("API Key Gemini tidak ditemukan. Mohon set environment variable 'GEMINI_API_KEY'")
    genai.configure(api_key=GEMINI_API_KEY)
except ValueError as e:
    print(e)
    exit()

# Model Gemini yang akan digunakan
MODEL = genai.GenerativeModel('gemini-1.5-flash') # Menggunakan Flash untuk kecepatan

# --- FUNGSI UTAMA ---

def get_page_content(url: str) -> str:
    """
    Mengambil konten HTML dari sebuah URL.
    Args:
        url: URL halaman web.
    Returns:
        Konten HTML sebagai string, atau string kosong jika gagal.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()  # Akan raise exception jika status code bukan 2xx
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error saat mengambil konten dari {url}: {e}")
        return ""

def extract_links(base_url: str, html_content: str) -> list[dict]:
    """
    Mengekstrak semua link yang valid dari konten HTML.
    Args:
        base_url: URL dasar untuk mengubah link relatif menjadi absolut.
        html_content: Konten HTML halaman.
    Returns:
        Sebuah list of dictionary, dimana setiap dictionary berisi 'text' dan 'href'.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        text = a_tag.get_text(strip=True)
        
        # Filter link yang tidak relevan dan pastikan ada teksnya
        if text and not href.startswith('#') and not href.startswith('javascript:'):
            full_url = urljoin(base_url, href)
            links.append({'text': text, 'href': full_url})
            
    # Hapus duplikat berdasarkan href
    unique_links = list({link['href']: link for link in links}.values())
    return unique_links

def ask_gemini_to_choose_link(links: list[dict], user_prompt: str) -> str:
    """
    Meminta Gemini untuk memilih link terbaik berdasarkan instruksi user.
    Args:
        links: List dictionary link yang tersedia.
        user_prompt: Instruksi dari user.
    Returns:
        URL yang dipilih oleh Gemini, atau string kosong jika tidak ada yang cocok.
    """
    if not links:
        return ""

    # Membatasi jumlah link agar tidak melebihi batas token
    max_links = 200
    if len(links) > max_links:
        print(f"Peringatan: Jumlah link terlalu banyak ({len(links)}). Dibatasi menjadi {max_links} link pertama.")
        links = links[:max_links]

    prompt_template = f"""
    Anda adalah asisten AI cerdas yang membantu user menavigasi sebuah website komik.
    Tugas Anda adalah memilih SATU URL terbaik dari daftar yang diberikan berdasarkan permintaan user.

    Permintaan User: "{user_prompt}"

    Berikut adalah daftar link yang tersedia dalam format JSON:
    {json.dumps(links, indent=2)}

    Analisis permintaan user dan teks dari setiap link, lalu pilih URL yang paling relevan.
    Hanya berikan jawaban berupa URL lengkap yang Anda pilih. Jangan memberikan penjelasan atau teks tambahan apapun.
    Jika tidak ada link yang cocok sama sekali, jawab dengan "NO_MATCH".
    """
    
    print("\n🤖 Gemini sedang berpikir untuk memilih link terbaik...")
    try:
        response = MODEL.generate_content(prompt_template)
        chosen_url = response.text.strip()
        
        if chosen_url == "NO_MATCH":
            return ""
        
        # Validasi apakah URL yang dikembalikan ada di list awal
        all_hrefs = [link['href'] for link in links]
        if chosen_url in all_hrefs:
            return chosen_url
        else:
            print("Peringatan: Gemini mengembalikan URL yang tidak ada di daftar. Mencoba mencari yang paling mirip.")
            # Fallback: cari kemiripan jika Gemini halusinasi
            from difflib import get_close_matches
            matches = get_close_matches(chosen_url, all_hrefs, n=1, cutoff=0.8)
            return matches[0] if matches else ""

    except Exception as e:
        print(f"Terjadi error saat berkomunikasi dengan Gemini: {e}")
        return ""

def scrape_comic_details(url: str, html_content: str) -> dict:
    """
    Mengekstrak detail lengkap dari halaman komik.
    NOTE: Selector CSS sangat spesifik untuk struktur HTML Komikcast per Agustus 2024.
          Ini mungkin perlu disesuaikan jika website mengubah desainnya.
    """
    print(f"\n🔍 Scraping detail dari {url}...")
    soup = BeautifulSoup(html_content, 'html.parser')
    data = {'url_sumber': url}

    try:
        # Judul
        data['judul'] = soup.select_one('.komik_info-content-body-title').get_text(strip=True)

        # Sinopsis
        data['sinopsis'] = soup.select_one('.komik_info-description-sinopsis p').get_text(strip=True)

        # Detail (Author, Status, dll)
        details = {}
        for item in soup.select('.komik_info-content-native li'):
            key = item.select_one('b').get_text(strip=True).lower().replace(' ', '_')
            value = item.select_one('span').get_text(strip=True)
            details[key] = value
        data['details'] = details

        # Genre
        data['genre'] = [a.get_text(strip=True) for a in soup.select('.komik_info-genre-list a')]
        
        # Rating
        rating_element = soup.select_one('.komik_info-content-rating-avg')
        data['rating'] = rating_element.get_text(strip=True) if rating_element else 'N/A'

        # Daftar Chapter
        chapters = []
        for chapter_item in soup.select('.komik_info-chapters-item'):
            link_tag = chapter_item.find('a')
            time_tag = chapter_item.find(class_='chapter-link-time')
            if link_tag:
                chapters.append({
                    'chapter': link_tag.get_text(strip=True),
                    'url': link_tag['href'],
                    'tanggal_rilis': time_tag.get_text(strip=True) if time_tag else 'N/A'
                })
        data['daftar_chapter'] = chapters
        
        print("✅ Scraping berhasil!")

    except AttributeError as e:
        print(f"❌ Gagal scraping. Struktur HTML mungkin berubah. Error: {e}")
        return {'error': 'Gagal mengambil data, mungkin ini bukan halaman detail komik atau struktur web telah berubah.'}

    return data

def save_to_json(data: dict):
    """Menyimpan data ke file JSON."""
    if 'judul' in data:
        filename = f"{data['judul'].replace(' ', '_').lower()}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"\n💾 Data berhasil disimpan ke file: {filename}")
        except IOError as e:
            print(f"Gagal menyimpan file: {e}")
    else:
        print("Tidak ada judul untuk dijadikan nama file. Data tidak disimpan.")


def main_cli():
    """Fungsi utama untuk menjalankan Command Line Interface."""
    print("=" * 50)
    print("🤖 Selamat Datang di AI Comic Scraper! 🤖")
    print("=" * 50)
    
    base_url = input("Masukkan URL utama website komik (cth: https://komikcast.li): ")
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'https://' + base_url
    
    current_url = base_url

    print("\nPerintah yang tersedia:")
    print("  pergi [instruksi]  - AI akan menavigasi sesuai instruksi Anda.")
    print("                      (Contoh: pergi cari komik solo leveling)")
    print("  scrape              - Ambil semua detail dari halaman komik saat ini.")
    print("  url                 - Tampilkan URL halaman saat ini.")
    print("  keluar              - Keluar dari program.")
    print("-" * 50)

    while True:
        try:
            print(f"\n📍 Lokasi saat ini: {current_url}")
            user_input = input("> ").strip().lower()
            
            if not user_input:
                continue

            if user_input.startswith("pergi "):
                instruction = user_input[6:].strip()
                if not instruction:
                    print("Mohon berikan instruksi. Contoh: pergi ke daftar komik")
                    continue
                
                print(f"Mengambil konten dari {current_url}...")
                html = get_page_content(current_url)
                if not html:
                    continue
                
                print("Mengekstrak semua link dari halaman...")
                links = extract_links(current_url, html)
                if not links:
                    print("Tidak ada link yang bisa ditemukan di halaman ini.")
                    continue
                
                chosen_url = ask_gemini_to_choose_link(links, instruction)
                
                if chosen_url:
                    current_url = chosen_url
                    print(f"✅ Navigasi berhasil ke: {current_url}")
                else:
                    print("❌ AI tidak dapat menemukan link yang cocok dengan instruksi Anda.")

            elif user_input == "scrape":
                html = get_page_content(current_url)
                if not html:
                    continue
                
                comic_data = scrape_comic_details(current_url, html)
                
                if 'error' not in comic_data:
                    # Tampilkan hasil dalam format JSON yang rapi
                    print(json.dumps(comic_data, indent=2, ensure_ascii=False))
                    
                    # Opsi untuk menyimpan
                    save_prompt = input("\nApakah Anda ingin menyimpan hasil ini ke file JSON? (y/n): ").lower()
                    if save_prompt == 'y':
                        save_to_json(comic_data)

            elif user_input == "url":
                print(f"URL saat ini adalah: {current_url}")

            elif user_input == "keluar":
                print("Terima kasih telah menggunakan AI Scraper. Sampai jumpa!")
                break
                
            else:
                print("Perintah tidak dikenali. Gunakan 'pergi', 'scrape', 'url', atau 'keluar'.")

        except KeyboardInterrupt:
            print("\nProgram dihentikan oleh user. Sampai jumpa!")
            break
        except Exception as e:
            print(f"\nTerjadi kesalahan tak terduga: {e}")
            continue


if __name__ == "__main__":
    main_cli()
