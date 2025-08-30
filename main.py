# main.py (v10.1 - Peningkatan Konfigurasi & Stabilitas)
import os
import json
import sys
from urllib.parse import urljoin


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

VERCEL_API_URL = os.environ.get("VERCEL_API_URL")

# Pengecekan Konfigurasi yang Lebih Baik
if not VERCEL_API_URL or not VERCEL_API_URL.startswith("http"):
    console.print(
        Panel(
            "[bold red]❌ Error Konfigurasi: VERCEL_API_URL tidak valid atau tidak ditemukan.[/bold red]\n\n"
            "[yellow]Pastikan file bernama `.env` sudah ada di direktori yang sama dengan `main.py` dan isinya benar, contoh:\n\n"
            '[cyan]VERCEL_API_URL="https://api-scrape-alpha.vercel.app"[/cyan]',
            title="[bold]Kesalahan Konfigurasi[/bold]",
            border_style="red"
        )
    )
    sys.exit(1)

# Memastikan URL selalu punya trailing slash agar urljoin bekerja dengan benar
if not VERCEL_API_URL.endswith('/'):
    VERCEL_API_URL += '/'


# --- Komponen Tampilan ---

def print_header():
    """Menampilkan header program menggunakan pyfiglet dan rich."""
    ascii_art = pyfiglet.figlet_format('AI SCRAPE', font='slant')
    console.print(Panel(
        f"[bold cyan]{ascii_art}[/bold cyan]",
        title="[white]Universal AI Comic Scraper[/white]",
        subtitle="[green]v10.1 - CLI Client[/green]",
        border_style="blue"
    ))

# --- Logika Interaksi Backend & AI ---

def call_api(endpoint, payload):
    """Membuat panggilan ke backend API dengan spinner."""
    spinner_text = "[cyan]🤖 Menghubungi server scraping...[/cyan]"
    if "suggest_action" in endpoint:
        spinner_text = "[cyan]🧠 AI sedang berpikir via backend...[/cyan]"

    with console.status(spinner_text, spinner="dots"):
        try:
            # Menghapus slash di awal endpoint untuk menghindari URL ganda
            api_endpoint = endpoint.lstrip('/')
            full_url = urljoin(VERCEL_API_URL, api_endpoint)

            response = requests.post(full_url, json=payload, timeout=120)
            response.raise_for_status()
            res_json = response.json()

            if res_json.get("status") == "error":
                console.print(f"[bold red]❌ Error dari API: {res_json.get('message')}[/bold red]")
                return None
            return res_json.get("data")
        except requests.exceptions.MissingSchema as e:
            console.print(f"[bold red]❌ Gagal terhubung ke server: URL tidak valid.[/bold red]")
            console.print(f"[yellow]Detail: {e}[/yellow]")
            console.print(f"[yellow]Pastikan VERCEL_API_URL di file .env Anda sudah benar.[/yellow]")
            return None
        except requests.exceptions.Timeout:
            console.print("[bold red]❌ Gagal terhubung ke server: Request timeout.[/bold red]")
            console.print("[yellow]Server mungkin sedang sibuk. Coba lagi.[/yellow]")
            return None
        except requests.exceptions.RequestException as e:
            console.print(f"[bold red]❌ Gagal terhubung ke server: {e}[/bold red]")
            return None



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
    page_data = None

    while True:
        new_page_data = call_api("/api/navigate", {"url": current_url})
        if not new_page_data:
            break
        page_data = new_page_data

        current_url = page_data['current_url']
        elements = page_data['elements']

        ai_suggestion = call_api("/api/suggest_action", {
            "goal": goal,
            "current_url": current_url,
            "elements": elements
        })

        if not ai_suggestion:
            ai_suggestion = {}

        console.print(Panel(
            f"[bold]Lokasi:[/bold] [cyan]{current_url}[/cyan]\n[bold]Judul Halaman:[/bold] [yellow]{page_data['title']}[/yellow]",
            title="[bold blue]Dashboard Sesi[/bold blue]",
            border_style="blue"
        ))
        console.print(f"[italic magenta]🤖 Saran AI: {ai_suggestion.get('action', 'N/A')}[/italic magenta]")

        choices = []
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
        if action == 'navigate':
            current_url = user_choice['details']['url']
            continue

        if action == 'scrape':
            if not page_data or 'html' not in page_data:
                console.print("[bold yellow]⚠️ HTML tidak ditemukan, meminta ulang dari server...[/bold yellow]")
                page_data = call_api("/api/navigate", {"url": current_url})
                if not page_data or 'html' not in page_data:
                    console.print("[bold red]❌ Gagal mendapatkan HTML untuk scraping.[/bold red]")
                    break

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

