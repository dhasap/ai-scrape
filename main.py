# main.py (v10.4 - Multi-Server Failover)
import os
import json
import sys
from urllib.parse import urljoin, urlparse, urlencode

import requests
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.status import Status
from dotenv import load_dotenv
import pyfiglet

# --- Konfigurasi ---
load_dotenv()
console = Console()

# --- PERUBAHAN: Membaca semua URL server dari .env ---
api_urls_dict = {}
for key, value in os.environ.items():
    if key.startswith("VERCEL_API_URL_"):
        try:
            # Mengambil nomor dari nama variabel (misal: VERCEL_API_URL_1 -> 1)
            index = int(key.split('_')[-1])
            if value and value.startswith("http"):
                api_urls_dict[index] = value
        except (ValueError, IndexError):
            continue # Abaikan jika formatnya salah

# Mengurutkan URL berdasarkan nomornya
API_URLS = [api_urls_dict[key] for key in sorted(api_urls_dict.keys())]


if not API_URLS:
    console.print(
        Panel(
            "[bold red]❌ Error Konfigurasi: URL Backend tidak ditemukan.[/bold red]\n\n"
            "[yellow]Pastikan file `.env` sudah ada dan berisi variabel seperti:\n\n"
            '[cyan]VERCEL_API_URL_1="https://url-utama-anda.vercel.app"\n'
            'VERCEL_API_URL_2="https://url-cadangan-anda.vercel.app"[/cyan]',
            title="[bold]Kesalahan Konfigurasi[/bold]",
            border_style="red"
        )
    )
    sys.exit(1)

# --- Komponen Tampilan ---

def print_header():
    """Menampilkan header program menggunakan pyfiglet dan rich."""
    ascii_art = pyfiglet.figlet_format('AI SCRAPE', font='slant')
    console.print(Panel(
        f"[bold cyan]{ascii_art}[/bold cyan]",
        title="[white]Universal AI Comic Scraper[/white]",
        subtitle="[green]v10.4 - Multi-Server Failover[/green]",
        border_style="blue"
    ))

# --- Logika Interaksi Backend & AI (Dengan Failover) ---

def call_api(endpoint, payload):
    """Membuat panggilan ke backend API dengan logika failover untuk banyak server."""
    spinner_text = "[cyan]🤖 Menghubungi server...[/cyan]"
    
    for i, base_url in enumerate(API_URLS):
        server_name = "utama" if i == 0 else f"cadangan {i}"
        
        if not base_url.endswith('/'):
            base_url += '/'
        
        with console.status(f"{spinner_text} (Server {server_name})", spinner="dots"):
            try:
                api_endpoint = endpoint.lstrip('/')
                full_url = urljoin(base_url, api_endpoint)

                response = requests.post(full_url, json=payload, timeout=120)
                
                if 500 <= response.status_code < 600:
                    console.print(f"[bold yellow]⚠️ Server {server_name} mengalami masalah (Status: {response.status_code}).[/bold yellow]")
                    if i < len(API_URLS) - 1:
                        console.print("[yellow]Mencoba beralih ke server berikutnya...[/yellow]")
                        continue
                    else:
                        console.print("[bold red]❌ Semua server cadangan juga gagal.[/bold red]")
                        return None

                response.raise_for_status()
                res_json = response.json()

                if res_json.get("status") == "error":
                    console.print(f"[bold red]❌ Error dari API: {res_json.get('message')}[/bold red]")
                    return None
                
                return res_json.get("data")

            except requests.exceptions.RequestException as e:
                console.print(f"[bold red]❌ Gagal terhubung ke server {server_name}: {e}[/bold red]")
                if i < len(API_URLS) - 1:
                    console.print("[yellow]Mencoba beralih ke server berikutnya...[/yellow]")
                    continue
                else:
                    return None
    
    console.print("[bold red]❌ Semua server backend gagal dihubungi.[/bold red]")
    return None

# --- Alur Kerja Utama (CLI) ---
# (Tidak ada perubahan di bawah sini, logika failover sudah ditangani)
def interactive_session():
    """Memulai dan mengelola sesi scraping interaktif."""
    console.print("\n[bold green]🚀 Memulai Sesi Scraping Baru...[/bold green]")
    start_url = questionary.text(
        "🔗 Masukkan URL awal (misal: https://komikcast.li):",
        validate=lambda text: text.startswith("http") or "URL tidak valid",
    ).ask()

    if not start_url: return

    current_url = start_url
    goal = None 

    while True:
        page_data = call_api("/api/navigate", {"url": current_url})
        if not page_data:
            break

        current_url = page_data['current_url']
        elements = page_data['elements']

        console.print(Panel(
            f"[bold]Lokasi:[/bold] [cyan]{current_url}[/cyan]\n[bold]Judul Halaman:[/bold] [yellow]{page_data['title']}[/yellow]",
            title="[bold blue]Dashboard Sesi[/bold blue]",
            border_style="blue"
        ))

        ai_suggestion = None
        if goal:
            console.print(f"🎯 Tujuan saat ini: [bold yellow]{goal}[/bold yellow]")
            ai_suggestion = call_api("/api/suggest_action", {
                "goal": goal,
                "current_url": current_url,
                "elements": elements
            })
            if ai_suggestion:
                 console.print(f"[italic magenta]🤖 Saran AI: {ai_suggestion.get('action', 'N/A')}[/italic magenta]")

        choices = []
        choices.append(questionary.Choice(title="🔎 Cari Komik di Situs Ini", value={"action": "search"}))

        if ai_suggestion and ai_suggestion.get('action') != 'fail':
            choices.append(questionary.Choice(title=f"✅ [AI] {ai_suggestion['action']}", value=ai_suggestion))

        choices.append(questionary.Choice(title="📄 Lakukan Scrape Halaman Ini", value={"action": "scrape"}))
        
        link_choices = [el for el in elements if el['tag'] == 'a' and el.get('text')][:5]
        if link_choices:
            choices.append(questionary.Separator("--- Klik Link Lain ---"))
            for link in link_choices:
                choices.append(questionary.Choice(
                    title=f"  -> {link['text']:.50}", 
                    value={"action": "navigate", "details": {"url": link['href']}}
                ))

        choices.append(questionary.Separator())
        choices.append(questionary.Choice(title="🔙 Kembali ke Menu Utama", value={"action": "exit"}))

        user_choice = questionary.select("Pilih aksi selanjutnya:", choices=choices).ask()

        if not user_choice or user_choice['action'] == 'exit':
            break

        action = user_choice['action']
        
        if action == 'search':
            search_query = questionary.text("Masukkan judul komik yang ingin dicari:").ask()
            if search_query:
                goal = search_query
                parsed_url = urlparse(current_url)
                query_params = {'s': goal}
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                search_url = f"{base_url}?{urlencode(query_params)}"
                current_url = search_url
                console.print(f"🔎 Mencari di: [cyan]{current_url}[/cyan]")
            continue

        if action == 'navigate':
            current_url = user_choice['details']['url']
            continue
        
        if action == 'scrape':
            if not goal:
                goal = questionary.text("🎯 Apa tujuan scraping Anda untuk halaman ini?").ask()
                if not goal:
                    console.print("[bold red]Tujuan scraping dibutuhkan untuk melanjutkan.[/bold red]")
                    continue

            console.print("[bold green]🤖 Mengirim HTML ke AI untuk diekstrak...[/bold green]")
            scraped_data = call_api("/api/scrape", {"html_content": page_data['html'], "goal": goal})
            
            if scraped_data:
                console.print(Panel("[bold green]✅ Scraping Selesai![/bold green]", border_style="green"))
                json_str = json.dumps(scraped_data, indent=2, ensure_ascii=False)
                console.print(Syntax(json_str, "json", theme="monokai", line_numbers=True))
            break

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

