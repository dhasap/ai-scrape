# main.py (Remote Control v11.0 - Edisi Power User)
# Menampilkan ringkasan dalam satu panel, diikuti oleh JSON hasil scrape murni.
import os
import sys
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
import requests
import json
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.panel import Panel
from rich.markdown import Markdown
import pyfiglet

# --- Inisialisasi & Konfigurasi Global ---
load_dotenv()

API_URLS = [os.getenv(f"VERCEL_API_URL_{i}") for i in range(1, 10) if os.getenv(f"VERCEL_API_URL_{i}")]
if not API_URLS:
    print(json.dumps({"status": "error", "message": "VERCEL_API_URL_1 tidak ditemukan di file .env"}, indent=2, ensure_ascii=False))
    sys.exit(1)

console = Console()
session = requests.Session()

def is_valid_url(url: str) -> bool:
    """Memvalidasi format URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except (ValueError, AttributeError):
        return False

def call_api_with_failover(payload: dict) -> dict | None:
    """Mengirim request ke API dengan failover otomatis."""
    for i, base_url in enumerate(API_URLS, 1):
        api_endpoint = urljoin(base_url, "/api/scrape")
        try:
            spinner_text = f"Menghubungi CognitoScraper [Server {i}/{len(API_URLS)}]..."
            with Live(Spinner("dots", text=spinner_text), console=console, transient=True, refresh_per_second=20):
                response = session.post(api_endpoint, json=payload, timeout=180)
                response.raise_for_status()
                return response.json()
        except requests.exceptions.RequestException as e:
            console.print(f"[bold red]Koneksi ke server {i} gagal: {e}[/bold red]", style="stderr")
            if i < len(API_URLS):
                console.print("[yellow]Mencoba server cadangan...[/yellow]", style="stderr")
            else:
                console.print("[bold red]Semua server gagal dihubungi.[/bold red]", style="stderr")
                return None
    return None

# ==============================================================================
# === FUNGSI TAMPILAN HASIL (DIUBAH KE MODE POWER USER) ===
# ==============================================================================
def display_results(response_data: dict):
    """
    Menampilkan ringkasan dalam satu Panel, diikuti oleh JSON hasil scrape murni.
    """
    console.print("-" * 80)
    if not response_data:
        response_data = {"status": "error", "message": "Tidak ada respons valid dari server"}

    # 1. Tampilkan Ringkasan dalam Satu Panel
    status = response_data.get("status", "unknown")
    status_color = "green" if status == "success" else "red"
    
    summary_content_parts = []
    summary_content_parts.append(f"[bold]Status:[/bold] [{status_color}]{status}[/{status_color}]")

    if "reasoning" in response_data:
        summary_content_parts.append(f"\n\n[bold yellow]Penalaran AI:[/bold]\n[italic yellow]{response_data['reasoning']}[/italic yellow]")

    if "commentary" in response_data:
        # Gunakan Markdown untuk komentar agar formatnya bagus
        summary_content_parts.append(f"\n\n[bold magenta]Komentar AI:[/bold]\n" + response_data['commentary'])

    # Gabungkan semua bagian dan tampilkan di dalam Panel
    console.print(Panel(
        Markdown("\n".join(summary_content_parts)),
        title="[bold]Ringkasan Respons AI[/bold]", 
        border_style="cyan", 
        expand=True
    ))
    console.print("-" * 80)

    # 2. Tampilkan HANYA JSON Hasil Scrape
    scraped_data = response_data.get("structured_data")
    if scraped_data is not None:
        console.print("[bold]Scraped Data (JSON):[/bold]")
        print(json.dumps(scraped_data, indent=2, ensure_ascii=False))
        console.print("-" * 80)


def print_header():
    """Mencetak banner aplikasi."""
    console.clear()
    ascii_art = pyfiglet.figlet_format("CognitoScraper", font="slant")
    console.print(f"[bold green]{ascii_art}[/bold green]")
    console.print("Mode: Power User. [italic]Hint: Beri instruksi detail untuk hasil scrape yang lengkap.[/italic]")


def interactive_session():
    """Fungsi utama yang menjalankan loop interaktif sesi CLI."""
    print_header()
    
    target_url = ""
    while not target_url:
        try:
            raw_input_url = console.input("[bold yellow]🔗 MASUKKAN TARGET URL > [/bold yellow]")
            if is_valid_url(raw_input_url):
                target_url = raw_input_url
            else:
                console.print("[bold red]URL tidak valid.[/bold red]")
        except (KeyboardInterrupt, EOFError):
            console.print("\nKeluar.")
            sys.exit(0)
            
    conversation_history = []
    current_instruction = "analisa halaman ini dan berikan saran scrape"
    
    while True:
        try:
            domain = urlparse(target_url).netloc
            current_instruction = console.input(f"\n[bold yellow]✍️ PERINTAH ([/bold yellow][cyan]{domain}[/cyan][bold yellow]) > [/bold yellow]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n\n[bold cyan]Sesi diakhiri oleh pengguna.[/bold cyan]")
            break

        if not current_instruction.strip() or current_instruction.lower() in ['exit', 'quit', 'keluar']:
            console.print("[bold cyan]Terima kasih telah menggunakan CognitoScraper.[/bold cyan]")
            break

        payload = {
            "url": target_url, 
            "instruction": current_instruction,
            "conversation_history": conversation_history
        }
        
        response = call_api_with_failover(payload)
        
        display_results(response)
        
        # Riwayat percakapan tetap dipertahankan untuk konteks AI
        if response and response.get("status") == "success":
            human_turn = {"human": current_instruction}
            ai_comment = response.get("commentary", "")
            ai_data_summary = f"Data terstruktur berisi {len(response.get('structured_data', []))} item." if 'structured_data' in response else ""
            ai_turn = {"ai": f"{ai_comment} {ai_data_summary}".strip()}

            conversation_history.extend([human_turn, ai_turn])
            conversation_history = conversation_history[-10:]
        
        # Logika navigasi tetap ada
        if response and response.get("action") == "navigate":
            new_url = response.get("url")
            if new_url:
                target_url = urljoin(target_url, new_url)
                console.print(f"✈️ [bold green]NAVIGASI OTOMATIS.[/bold green] Target baru: [cyan]{target_url}[/cyan]")

if __name__ == "__main__":
    interactive_session()

