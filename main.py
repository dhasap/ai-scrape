# main.py (v10.5 - Smart Display)
import os
import json
import sys
from urllib.parse import urljoin, urlparse, urlencode
import math

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

# Membaca semua URL server dari .env
api_urls_dict = {}
for key, value in os.environ.items():
    if key.startswith("VERCEL_API_URL_"):
        try:
            index = int(key.split('_')[-1])
            if value and value.startswith("http"):
                api_urls_dict[index] = value
        except (ValueError, IndexError):
            continue
API_URLS = [api_urls_dict[key] for key in sorted(api_urls_dict.keys())]

if not API_URLS:
    console.print(Panel("[bold red]❌ Error Konfigurasi: URL Backend tidak ditemukan.[/bold red]", title="[bold]Kesalahan Konfigurasi[/bold]", border_style="red"))
    sys.exit(1)

# --- Komponen Tampilan ---

def print_header():
    ascii_art = pyfiglet.figlet_format('AI SCRAPE', font='slant')
    console.print(Panel(f"[bold cyan]{ascii_art}[/bold cyan]", title="[white]Universal AI Comic Scraper[/white]", subtitle="[green]v10.5 - Smart Display[/green]", border_style="blue"))

# --- Logika Interaksi Backend & AI ---

def call_api(endpoint, payload):
    for i, base_url in enumerate(API_URLS):
        server_name = "utama" if i == 0 else f"cadangan {i}"
        if not base_url.endswith('/'): base_url += '/'
        with console.status(f"🤖 Menghubungi server {server_name}...", spinner="dots"):
            try:
                full_url = urljoin(base_url, endpoint.lstrip('/'))
                response = requests.post(full_url, json=payload, timeout=120)
                if 500 <= response.status_code < 600:
                    console.print(f"[bold yellow]⚠️ Server {server_name} bermasalah (Status: {response.status_code}). Mencoba server berikutnya...[/bold yellow]")
                    continue
                response.raise_for_status()
                res_json = response.json()
                if res_json.get("status") == "error": return None
                return res_json.get("data")
            except requests.exceptions.RequestException:
                if i < len(API_URLS) - 1: continue
                else: return None
    return None

# --- Alur Kerja Utama (CLI) ---

def interactive_session():
    console.print("\n[bold green]🚀 Memulai Sesi Scraping Baru...[/bold green]")
    start_url = questionary.text("🔗 Masukkan URL awal:", validate=lambda text: text.startswith("http")).ask()
    if not start_url: return

    current_url = start_url
    goal = None
    page_num = 1
    results_per_page = 6

    while True:
        page_data = call_api("/api/navigate", {"url": current_url})
        if not page_data: break

        current_url = page_data['current_url']
        search_results = page_data.get('search_results', [])
        pagination = page_data.get('pagination', {})
        other_elements = page_data.get('other_elements', [])
        
        console.print(Panel(f"[bold]Lokasi:[/bold] [cyan]{current_url}[/cyan]\n[bold]Judul Halaman:[/bold] [yellow]{page_data['title']}[/yellow]", title="[bold blue]Dashboard Sesi[/bold blue]"))

        ai_suggestion = None
        if goal:
            console.print(f"🎯 Tujuan saat ini: [bold yellow]{goal}[/bold yellow]")
            ai_suggestion = call_api("/api/suggest_action", {"goal": goal, "current_url": current_url, "elements": other_elements})
            if ai_suggestion: console.print(f"[italic magenta]🤖 Saran AI: {ai_suggestion.get('action', 'N/A')}[/italic magenta]")

        choices = []
        choices.append(questionary.Choice(title="🔎 Cari Komik di Situs Ini", value={"action": "search"}))

        # --- PERUBAHAN: Tampilan menu cerdas ---
        if search_results:
            choices.append(questionary.Separator("--- Hasil Pencarian ---"))
            
            # Logika Paginasi Tampilan
            start_index = (page_num - 1) * results_per_page
            end_index = start_index + results_per_page
            total_pages = math.ceil(len(search_results) / results_per_page)
            
            for item in search_results[start_index:end_index]:
                choices.append(questionary.Choice(title=f"  📖 {item['title']:.60}", value={"action": "navigate", "details": {"url": item['url']}}))

            if total_pages > 1:
                pagination_choices = []
                if page_num > 1:
                    pagination_choices.append(questionary.Choice(title="⬅️ Sebelumnya", value={"action": "prev_page"}))
                if end_index < len(search_results):
                     pagination_choices.append(questionary.Choice(title="➡️ Berikutnya", value={"action": "next_page"}))
                if pagination_choices:
                     choices.append(questionary.Separator(f"Halaman {page_num}/{total_pages}"))
                     choices.extend(pagination_choices)

        if ai_suggestion and ai_suggestion.get('action') != 'fail':
            choices.append(questionary.Choice(title=f"✅ [AI] {ai_suggestion['action']}", value=ai_suggestion))

        choices.append(questionary.Choice(title="📄 Lakukan Scrape Halaman Ini", value={"action": "scrape"}))
        
        # Opsi navigasi fallback jika tidak ada hasil pencarian
        if not search_results:
            link_choices = [el for el in other_elements if el['tag'] == 'a' and el.get('text')][:5]
            if link_choices:
                choices.append(questionary.Separator("--- Klik Link Lain ---"))
                for link in link_choices:
                    choices.append(questionary.Choice(title=f"  -> {link['text']:.50}", value={"action": "navigate", "details": {"url": link['href']}}))

        choices.append(questionary.Separator())
        choices.append(questionary.Choice(title="🔙 Kembali ke Menu Utama", value={"action": "exit"}))

        user_choice = questionary.select("Pilih aksi selanjutnya:", choices=choices).ask()

        if not user_choice or user_choice['action'] == 'exit': break

        action = user_choice['action']
        
        # Reset paginasi jika ada aksi baru
        if action not in ["next_page", "prev_page"]:
            page_num = 1
        
        if action == 'search':
            search_query = questionary.text("Masukkan judul komik:").ask()
            if search_query:
                goal = search_query
                parsed_url = urlparse(current_url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                current_url = f"{base_url}?{urlencode({'s': goal})}"
            continue
        
        if action == 'next_page':
            page_num += 1
            continue
        if action == 'prev_page':
            page_num -= 1
            continue

        if action == 'navigate':
            current_url = user_choice['details']['url']
            continue
        
        if action == 'scrape':
            if not goal:
                goal = questionary.text("🎯 Apa tujuan scraping Anda?").ask()
                if not goal: continue
            scraped_data = call_api("/api/scrape", {"html_content": page_data['html'], "goal": goal})
            if scraped_data:
                console.print(Panel("[bold green]✅ Scraping Selesai![/bold green]", border_style="green"))
                console.print(Syntax(json.dumps(scraped_data, indent=2, ensure_ascii=False), "json", theme="monokai", line_numbers=True))
            break

def main():
    while True:
        print_header()
        choice = questionary.select("Pilih menu utama:", choices=["🚀 Mulai Sesi Scraping Baru", "退出 Keluar"]).ask()
        if choice == "🚀 Mulai Sesi Scraping Baru":
            interactive_session()
        else:
            console.print("[bold yellow]👋 Sampai jumpa![/bold yellow]")
            break

if __name__ == "__main__":
    main()

