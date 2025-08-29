# main.py (v10.0 - Modern CLI Client)
import os
import json
import sys
from urllib.parse import urljoin

import google.generativeai as genai
import requests
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.spinner import Spinner
from dotenv import load_dotenv
import pyfiglet

# --- Konfigurasi --- 
load_dotenv()
console = Console()

# PENTING: Ganti dengan URL Vercel Anda setelah deploy!
VERCEL_API_URL = os.environ.get("VERCEL_API_URL", "http://127.0.0.1:8000") 

try:
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("API Key Gemini tidak ditemukan di .env")
    genai.configure(api_key=GEMINI_API_KEY)
    AI_MODEL = genai.GenerativeModel('gemini-1.5-flash')
except ValueError as e:
    console.print(f"[bold red]❌ Error Konfigurasi: {e}[/bold red]")
    sys.exit(1)

# --- Komponen Tampilan ---

def print_header():
    """Menampilkan header program menggunakan pyfiglet dan rich."""
    ascii_art = pyfiglet.figlet_format('AI SCRAPE', font='slant')
    console.print(Panel(
        f"[bold cyan]{ascii_art}[/bold cyan]",
        title="[white]Universal AI Comic Scraper[/white]",
        subtitle="[green]v10.0 - CLI Client[/green]",
        border_style="blue"
    ))

# --- Logika Interaksi Backend & AI ---

def call_api(endpoint, payload):
    """Membuat panggilan ke backend API dengan spinner."""
    with Spinner("dots", text="[cyan]🤖 Menghubungi server scraping...[/cyan]") as spinner:
        try:
            response = requests.post(urljoin(VERCEL_API_URL, endpoint), json=payload, timeout=60)
            response.raise_for_status() # Error jika status code 4xx atau 5xx
            res_json = response.json()
            if res_json.get("status") == "error":
                console.print(f"[bold red]❌ Error dari API: {res_json.get('message')}[/bold red]")
                return None
            return res_json.get("data")
        except requests.exceptions.RequestException as e:
            console.print(f"[bold red]❌ Gagal terhubung ke server: {e}[/bold red]")
            console.print("[yellow]Pastikan backend API sudah berjalan atau URL Vercel sudah benar.[/yellow]")
            return None

def get_ai_suggestion(goal, current_url, element_map):
    """AI menentukan langkah berikutnya berdasarkan 'peta' elemen."""
    prompt = f"""
Anda adalah otak dari agen web scraper. Tujuan Anda: "{goal}". Posisi saat ini: "{current_url}".
Tugas Anda: Pilih SATU aksi dari daftar berikut dalam format JSON: {{ "action": "ACTION_NAME", "details": {{...}} }}

1. `navigate`: Jika Anda perlu mengklik sebuah link. Pilih `ai_id` dan `href` dari link yang paling relevan.
   {{ "action": "navigate", "details": {{ "ai_id": "ID_LINK", "url": "URL_TUJUAN" }} }}
2. `search`: Jika Anda perlu mengetik di kolom pencarian. Pilih `ai_id` dari input yang relevan.
   {{ "action": "search", "details": {{ "ai_id": "ID_INPUT" }} }}
3. `scrape`: HANYA jika Anda YAKIN sudah berada di halaman detail final yang berisi data komik.
   {{ "action": "scrape", "details": {{}} }}
4. `fail`: Jika Anda buntu.
   {{ "action": "fail", "details": {{ "reason": "ALASAN_GAGAL" }} }}

ATURAN:
- Jika halaman ini adalah hasil pencarian, prioritas utama adalah `navigate` ke link yang paling relevan.
- JANGAN memilih `scrape` di halaman daftar.

Peta Elemen Interaktif:
---
{json.dumps(element_map[:100], indent=2)}
---
Tentukan langkah berikutnya.
    """
    try:
        with Spinner("dots", text="[cyan]🧠 AI sedang berpikir...[/cyan]") as spinner:
            response = AI_MODEL.generate_content(prompt)
            json_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(json_text)
    except Exception as e:
        return {{'action': 'fail', 'details': {{'reason': f'Gagal memproses respons AI: {e}'}}}}

# --- Alur Kerja Utama (CLI) ---

def interactive_session():
    """Memulai dan mengelola sesi scraping interaktif."""
    console.print("\n[bold green]🚀 Memulai Sesi Scraping Baru...[/bold green]")
    start_url = questionary.text(
        "🔗 Masukkan URL awal:",
        validate=lambda text: text.startswith("http") or "URL tidak valid",
    ).ask()

    if not start_url: return

    goal = questionary.text("🎯 Apa judul komik yang ingin Anda cari?").ask()
    if not goal: return

    current_url = start_url
    while True:
        page_data = call_api("/api/navigate", {"url": current_url})
        if not page_data: break

        current_url = page_data['current_url']
        elements = page_data['elements']

        ai_suggestion = get_ai_suggestion(goal, current_url, elements)

        console.print(Panel(
            f"[bold]Lokasi:[/bold] [cyan]{current_url}[/cyan]\n[bold]Judul Halaman:[/bold] [yellow]{page_data['title']}[/yellow]",
            title="[bold blue]Dashboard Sesi[/bold blue]",
            border_style="blue"
        ))
        console.print(f"[italic magenta]🤖 Saran AI: {ai_suggestion.get('action', 'N/A')}[/italic magenta]")

        # --- Membangun Menu Aksi ---
        choices = []
        # 1. Tambahkan saran AI sebagai pilihan utama
        if ai_suggestion and ai_suggestion.get('action') != 'fail':
            choices.append(questionary.Choice(title=f"✅ [AI] {ai_suggestion['action']}", value=ai_suggestion))

        # 2. Tambahkan opsi scrape manual
        choices.append(questionary.Choice(title="📄 Lakukan Scrape Halaman Ini", value={"action": "scrape"}))
        
        # 3. Tambahkan opsi navigasi manual
        link_choices = [el for el in elements if el['tag'] == 'a' and el.get('text')][:5]
        if link_choices:
            choices.append(questionary.Separator("--- Klik Link Lain ---"))
            for link in link_choices:
                choices.append(questionary.Choice(
                    title=f"  -> {link['text']:.50}", 
                    value={"action": "navigate", "details": {"url": link['href']}}
                ))

        # 4. Tambahkan opsi keluar
        choices.append(questionary.Separator())
        choices.append(questionary.Choice(title="🔙 Kembali ke Menu Utama", value={"action": "exit"}))

        user_choice = questionary.select("Pilih aksi selanjutnya:", choices=choices).ask()

        if not user_choice or user_choice['action'] == 'exit':
            break

        # --- Eksekusi Aksi Pilihan User ---
        action = user_choice['action']
        if action == 'navigate':
            current_url = user_choice['details']['url']
            continue
        
        if action == 'scrape':
            console.print("[bold green]⏳ Meminta HTML lengkap untuk di-scrape...[/bold green]")
            full_page_data = call_api("/api/navigate", {"url": current_url})
            if not full_page_data: continue

            console.print("[bold green]🤖 Mengirim HTML ke AI untuk diekstrak...[/bold green]")
            scraped_data = call_api("/api/scrape", {"html_content": str(full_page_data), "goal": goal})
            
            if scraped_data:
                console.print(Panel("[bold green]✅ Scraping Selesai![/bold green]", border_style="green"))
                json_str = json.dumps(scraped_data, indent=2, ensure_ascii=False)
                console.print(Syntax(json_str, "json", theme="monokai", line_numbers=True))
            break # Selesai setelah scrape

def main():
    """Menjalankan loop menu utama."""
    while True:
        print_header()
        choice = questionary.select(
            "Pilih menu utama:",
            choices=[
                questionary.Choice("🚀 Mulai Sesi Scraping Baru", value="start"),
                questionary.Choice("退出 Keluar", value="exit"),
            ]
        ).ask()

        if choice == "start":
            interactive_session()
        elif choice == "exit" or not choice:
            console.print("[bold yellow]👋 Sampai jumpa![/bold yellow]")
            break

if __name__ == "__main__":
    main()
