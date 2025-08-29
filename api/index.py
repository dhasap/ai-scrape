# api/index.py
import os
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from bs4 import BeautifulSoup
import google.generativeai as genai
from playwright.async_api import async_playwright
import json

# --- Konfigurasi ---
try:
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("API Key Gemini tidak ditemukan di environment variables.")
    genai.configure(api_key=GEMINI_API_KEY)
except ValueError as e:
    print(e)

app = FastAPI()

# --- Model Data (untuk validasi request) ---
class NavigateRequest(BaseModel):
    url: str

class ScrapeRequest(BaseModel):
    html_content: str
    goal: str

# --- Logika Inti Scraping & AI ---

async def get_page_elements(url: str):
    """Menggunakan Playwright untuk membuka URL dan mengekstrak elemen interaktif."""
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)

            # Scroll down to trigger lazy-loaded content
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight / 2);')
            await asyncio.sleep(1)

            # Inject data-ai-id attributes
            js_script = """
            () => {
                const elements = document.querySelectorAll('a, button, input[type="submit"], input[type="text"], input[type="search"]');
                elements.forEach((el, index) => {
                    el.setAttribute('data-ai-id', `ai-id-${index}`);
                });
                return document.documentElement.outerHTML;
            }
            """
            html_with_ids = await page.evaluate(js_script)
            current_url = page.url

            await browser.close()

            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_with_ids, 'lxml')
            title = soup.title.string if soup.title else 'No Title'
            
            elements = []
            for el in soup.find_all(attrs={"data-ai-id": True}):
                tag = el.name
                text = el.get_text(strip=True)
                ai_id = el['data-ai-id']
                
                element_info = {"ai_id": ai_id, "tag": tag}
                if text:
                    element_info["text"] = text
                if tag == 'a' and el.has_attr('href'):
                    # Membuat URL absolut
                    element_info["href"] = urljoin(current_url, el['href'])
                if tag == 'input' and el.has_attr('placeholder'):
                    element_info["placeholder"] = el['placeholder']
                elements.append(element_info)

            return {"current_url": current_url, "title": title, "elements": elements}

        except Exception as e:
            return {"error": f"Gagal membuka atau memproses URL dengan Playwright: {str(e)}"}


def scrape_details_with_ai(goal: str, html_content: str):
    """AI mengekstrak semua data detail dari halaman final."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Anda adalah ahli scraper yang sangat teliti. Tujuan scraping adalah: "{goal}".
    Dari HTML berikut, ekstrak semua informasi relevan ke dalam format JSON yang VALID dan KONSISTEN.

    --- CONTOH FORMAT JSON YANG DIINGINKAN ---
    {{
      "title": "Judul Komik",
      "author": "Nama Author",
      "genre": ["Genre 1", "Genre 2"],
      "type": "Tipe Komik (e.g., Manhwa)",
      "status": "Status (e.g., Ongoing)",
      "synopsis": "Paragraf sinopsis...",
      "chapters": [
        {{
          "chapter_title": "Chapter 1",
          "release_date": "Tanggal Rilis Chapter",
          "url": "https://url-ke-chapter.com"
        }}
      ]
    }}
    -----------------------------------------

    ATURAN PENTING:
    1. Ikuti format contoh di atas dengan SANGAT TELITI.
    2. Pastikan JSON yang Anda hasilkan 100% valid.
    3. Ekstrak SEMUA chapter yang tersedia dalam HTML.
    4. Jika suatu informasi tidak dapat ditemukan, gunakan `null` sebagai nilainya.

    HTML untuk di-scrape:
    ---
    {html_content[:50000]}
    ---
    """
    try:
        response = model.generate_content(prompt)
        json_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(json_text)
    except Exception as e:
        return {'error': f'AI gagal mengekstrak detail: {str(e)}'}

# --- Endpoint API ---

@app.post("/api/navigate")
async def http_navigate(request: NavigateRequest):
    """Endpoint untuk navigasi ke URL dan mendapatkan elemen halaman."""
    result = await get_page_elements(request.url)
    if "error" in result:
        return {"status": "error", "message": result["error"]}
    return {"status": "success", "data": result}

@app.post("/api/scrape")
async def http_scrape(request: ScrapeRequest):
    """Endpoint untuk melakukan scraping pada konten HTML."""
    # Fungsi ini tidak async, jadi kita jalankan di thread pool default FastAPI
    result = scrape_details_with_ai(request.goal, request.html_content)
    if "error" in result:
        return {"status": "error", "message": result["error"]}
    return {"status": "success", "data": result}

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
