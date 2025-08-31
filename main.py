# main.py (v11.7 - Dual Brain AI)
import os
import json
import sys
from urllib.parse import urljoin, urlparse, urlencode
import math
import time
import re

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
API_URLS = [os.environ.get(f"VERCEL_API_URL_{i}") for i in range(1, 10) if os.environ.get(f"VERCEL_API_URL_{i}")]

if not API_URLS:
    console.print(Panel("[bold red]❌ Error Konfigurasi: URL Backend tidak ditemukan.[/bold red]", title="Kesalahan Konfigurasi"))
    sys.exit(1)

# --- Komponen Tampilan & Logika API ---
def print_header():
    ascii_art = pyfiglet.figlet_format('AI SCRAPE', font='slant')
    console.print(Panel(f"[bold cyan]{ascii_art}[/bold cyan]", title="Universal AI Comic Scraper", subtitle="v11.7 - Dual Brain AI"))

def call_api(endpoint, payload):
    for i, base_url in enumerate(API_URLS):
        server_name = "utama" if i == 0 else f"cadangan {i}"
        if not base_url.endswith('/'): base_url += '/'
        with console.status(f"🤖 Menghubungi server {server_name}...", spinner="dots"):
            try:
                full_url = urljoin(base_url, endpoint.lstrip('/'))
                response = requests.post(full_url, json=payload, timeout=120)
                if 500 <= response.status_code < 600:
                    console.print(f"[yellow]⚠️ Server {server_name} bermasalah. Mencoba berikutnya...[/yellow]")
                    continue
                response.raise_for_status()
                return response.json().get("data")
            except requests.exceptions.RequestException:
                if i < len(API_URLS) - 1: continue
    return None

# --- ALUR KERJA: Halaman Chapter & Post-Scrape ---
# (Tidak ada perubahan di kedua fungsi ini, sudah stabil)
def chapter_session(chapter_url, detail_url, last_search_url, start_url):
    current_chapter_url = chapter_url
    while True:
        chapter_data = call_api("/api/scrape_chapter", {"url": current_chapter_url})
        if not chapter_data: return "exit_session"
        console.print(Panel(f"📖 Anda sedang melihat chapter di:\n[cyan]{current_chapter_url}[/cyan]", title="[bold blue]Mode Baca Chapter[/bold blue]"))
        choices = [questionary.Choice(f"🖼️ Tampilkan Link Gambar ({len(chapter_data.get('images', []))} gambar)", "scrape_images")]
        if chapter_data.get('next_chapter_url'): choices.append(questionary.Choice("➡️ Buka Chapter Berikutnya", "next_chapter"))
        if chapter_data.get('prev_chapter_url'): choices.append(questionary.Choice("⬅️ Buka Chapter Sebelumnya", "prev_chapter"))
        choices.extend([questionary.Separator(), questionary.Choice("🔙 Kembali ke Halaman Detail Komik", "back_to_detail")])
        if last_search_url: choices.append(questionary.Choice("🔍 Kembali ke Hasil Pencarian", "back_to_search"))
        choices.append(questionary.Choice("🔄 Kembali ke Halaman Awal Sesi", "go_to_start"))
        choice = questionary.select("Pilih aksi:", choices=choices).ask()
        if not choice: return "exit_session"
        if choice == 'back_to_detail': return detail_url
        if choice == 'back_to_search': return last_search_url
        if choice == 'go_to_start': return start_url
        if choice == 'scrape_images':
            console.print(Panel("[bold green]🖼️ Link Gambar Chapter:[/bold green]", border_style="green"))
            for img_url in chapter_data.get('images', []): console.print(f"- [cyan]{img_url}[/cyan]")
            input("\nTekan Enter untuk melanjutkan...")
        if choice == 'next_chapter': current_chapter_url = chapter_data.get('next_chapter_url')
        if choice == 'prev_chapter': current_chapter_url = chapter_data.get('prev_chapter_url')

def post_scrape_session(scraped_data, detail_url, last_search_url, start_url):
    while True:
        console.print(Panel("[bold green]✅ Scraping Detail Selesai![/bold green]", border_style="green"))
        console.print(Syntax(json.dumps(scraped_data, indent=2, ensure_ascii=False), "json", theme="monokai"))
        choices = []
        if scraped_data.get("chapters"): choices.append(questionary.Choice("📖 Buka/Scrape Chapter Tertentu", "open_chapter"))
        if last_search_url: choices.append(questionary.Choice("🔙 Kembali ke Hasil Pencarian", "back_to_search"))
        choices.append(questionary.Choice("🔄 Kembali ke Halaman Awal Sesi", "go_to_start"))
        choice = questionary.select("Pilih aksi selanjutnya:", choices=choices).ask()
        if not choice: return "exit_session"
        if choice == 'back_to_search': return last_search_url
        if choice == 'go_to_start': return start_url
        if choice == 'open_chapter':
            chapter_list = scraped_data.get("chapters", [])
            if not chapter_list: continue
            chapter_num_str = questionary.text(f"Masukkan nomor chapter (tersedia {len(chapter_list)} chapter):").ask()
            target_chapter = next((ch for ch in chapter_list if chapter_num_str in re.findall(r'\d+', ch.get("chapter_title", ""))), None)
            if target_chapter:
                next_url = chapter_session(target_chapter['url'], detail_url, last_search_url, start_url)
                if next_url == "exit_session": return "exit_session"
                return next_url
            else:
                console.print(f"[bold red]❌ Chapter '{chapter_num_str}' tidak ditemukan.[/bold red]")

# --- Alur Kerja Utama (CLI) ---
def interactive_session():
    start_url = questionary.text("🔗 Masukkan URL awal:", validate=lambda t: t.startswith("http")).ask()
    if not start_url: return

    current_url, goal, last_search_url, page_num = start_url, None, None, 1
    results_per_page = 6
    # --- PERUBAHAN: Menambahkan state untuk mode AI ---
    is_exploration_mode = True # Awalnya selalu mode penjelajahan

    while True:
        # --- PERUBAHAN: Mengirim konteks ke backend ---
        payload = {
            "url": current_url,
            "context": {
                "mode": "exploration" if is_exploration_mode else "navigation"
            }
        }
        page_data = call_api("/api/navigate", payload)
        if not page_data: break
        
        current_url = page_data['current_url']
        search_results = page_data.get('search_results', [])
        other_elements = page_data.get('other_elements', [])
        contextual_suggestion = page_data.get('contextual_suggestion')
        
        console.print(Panel(f"Lokasi: [cyan]{current_url}[/cyan]\nJudul Halaman: [yellow]{page_data['title']}[/yellow]", title="Dashboard Sesi"))
        
        # --- PERUBAHAN: Menampilkan saran AI yang sesuai mode ---
        
        # Mode 1: "Co-pilot Penjelajah"
        if is_exploration_mode and contextual_suggestion:
             console.print(f"[italic magenta]🤖 [Co-pilot] Saran: {contextual_suggestion.get('suggestion_text', 'N/A')}[/italic magenta]")

        # Mode 2: "GPS Pemburu"
        elif not is_exploration_mode and goal:
            console.print(f"🎯 Tujuan saat ini: [bold yellow]{goal}[/bold yellow]")
            navigation_suggestion = call_api("/api/suggest_action", {"goal": goal, "current_url": current_url, "elements": other_elements})
            if navigation_suggestion: 
                console.print(f"[italic magenta]🤖 [GPS] Saran: {navigation_suggestion.get('action', 'N/A')}[/italic magenta]")
        
        choices = []
        
        if search_results:
            last_search_url = current_url
            choices.append(questionary.Separator("--- Hasil Pencarian ---"))
            # ... logika paginasi tidak berubah ...
            for item in search_results: choices.append(questionary.Choice(f"📖 {item['title']:.60}", {"action": "navigate", "details": {"url": item['url']}}))

        elif goal and not search_results:
            choices.append(questionary.Separator("--- Aksi Halaman Detail ---"))
            choices.append(questionary.Choice("📄 Scrape Detail Komik Ini", {"action": "scrape"}))
            if last_search_url: choices.append(questionary.Choice("🔙 Kembali ke Hasil Pencarian", {"action": "go_back_to_search"}))
        
        # --- PERUBAHAN: Menampilkan Saran AI di Menu ---
        if contextual_suggestion:
            choices.insert(0, questionary.Choice(f"✅ [AI] {contextual_suggestion.get('suggestion_text')}", value={"action": "contextual_scrape"}))
        
        if not (goal and not search_results): 
            choices.insert(0, questionary.Choice("🔎 Cari Komik di Situs Ini", {"action": "search"}))
        
        if not search_results and not (goal and not search_results):
            link_choices = [el for el in other_elements if el.get('text')][:5]
            if link_choices:
                choices.append(questionary.Separator("--- Navigasi ---"))
                for link in link_choices:
                    choices.append(questionary.Choice(f"  -> {link['text']:.50}", {"action": "navigate_explore", "details": {"url": link['href']}})) # Aksi baru

        # Menampilkan tombol kembali yang sesuai konteks
        choices.append(questionary.Separator())
        is_deep_level = bool(goal or search_results)
        if is_deep_level:
            choices.append(questionary.Choice("🔄 Kembali ke Halaman Awal Sesi", {"action": "go_to_start"}))
        else:
            choices.append(questionary.Choice("🚪 Keluar dari Sesi Ini", {"action": "exit_session"}))

        user_choice = questionary.select("Pilih aksi selanjutnya:", choices=choices).ask()
        
        if not user_choice or user_choice.get('action') == 'exit_session':
            console.print("[bold cyan]✓ Sesi selesai. Kembali ke menu utama...[/bold cyan]")
            time.sleep(1)
            break 

        action = user_choice.get('action')
        
        # Mengatur mode AI berdasarkan aksi pengguna
        if action == 'search' or action == 'navigate':
            is_exploration_mode = False
        elif action == 'navigate_explore' or action == 'go_to_start' or action == 'go_back_to_search':
            is_exploration_mode = True

        if action == 'go_to_start':
            current_url, goal, last_search_url, page_num = start_url, None, None, 1
            continue
        
        if action == 'search':
            goal = questionary.text("Masukkan judul komik:").ask()
            if goal: current_url = f"{urlparse(current_url).scheme}://{urlparse(current_url).netloc}?{urlencode({'s': goal})}"
        elif action == 'go_back_to_search': current_url = last_search_url
        elif action == 'navigate' or action == 'navigate_explore': current_url = user_choice['details']['url']
        elif action == 'scrape' or action == 'contextual_scrape':
            # Jika scrape kontekstual, gunakan saran AI sebagai tujuan
            if action == 'contextual_scrape' and contextual_suggestion:
                goal = contextual_suggestion.get('suggestion_text', 'Data dari halaman ' + page_data['title'])

            if not goal: goal = questionary.text("🎯 Apa tujuan scraping Anda?").ask()
            if not goal: continue

            scraped_data = call_api("/api/scrape", {"html_content": page_data['html'], "goal": goal})
            if scraped_data:
                next_action_url = post_scrape_session(scraped_data, current_url, last_search_url, start_url)
                if next_action_url == "exit_session": break
                current_url = next_action_url
        
        if current_url: continue
        else: break

def main():
    while True:
        print_header()
        choice = questionary.select("Pilih menu utama:", choices=["🚀 Mulai Sesi Scraping Baru", "退出 Keluar"]).ask()
        if choice == "start": interactive_session()
        else: break
    console.print("[bold yellow]👋 Sampai jumpa![/bold yellow]")

if __name__ == "__main__":
    main()

