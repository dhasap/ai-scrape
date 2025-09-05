# main.py (Remote Control v10.0 - Edisi Ringkasan + JSON)
# Menampilkan ringkasan visual dengan Rich, diikuti oleh output JSON mentah.
import os
import sys
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
import requests
import json
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich.markdown import Markdown
from rich import box
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
# === FUNGSI TAMPILAN HASIL (DIUBAH MENJADI RINGKASAN + JSON MENTAH) ===
# ==============================================================================
def display_results(response_data: dict):
    """
    Menampilkan ringkasan hasil dalam tabel Rich, diikuti oleh JSON mentah.
    """
    console.print("-" * 80)
    if not response_data:
        response_data = {"status": "error", "message": "Tidak ada respons valid dari server"}

    # 1. Tampilkan Tabel Ringkasan
    summary_table = Table(title="[bold]Ringkasan Respons AI[/bold]", box=box.MINIMAL, show_header=False, expand=True)
    summary_table.add_column("Field", style="dim", width=15)
    summary_table.add_column("Value", style="bright_white")

    # Status (dengan warna)
    status = response_data.get("status", "unknown")
    status_color = "green" if status == "success" else "red"
    summary_table.add_row("Status", f"[{status_color}]{status}[/{status_color}]")

    # Penalaran AI
    if "reasoning" in response_data:
        summary_table.add_row("[yellow]Penalaran AI[/yellow]", f"[italic yellow]{response_data['reasoning']}[/italic yellow]")

    # Komentar AI
    if "commentary" in response_data:
        summary_table.add_row("[magenta]Komentar AI[/magenta]", Markdown(response_data['commentary']))

    console.print(summary_table)
    console.print("-" * 80)

    # 2. Tampilkan JSON Mentah
    console.print("[bold]Full Raw JSON Response:[/bold]")
    print(json.dumps(response_data, indent=2, ensure_ascii=False))
    console.print("-" * 80)


def print_header():
    """Mencetak banner aplikasi."""
    console.clear()
    ascii_art = pyfiglet.figlet_format("CognitoScraper", font="slant")
    console.print(f"[bold green]{ascii_art}[/bold green]")
    console.print("Mode: Ringkasan + JSON. Masukkan URL dan instruksi. Ketik 'exit' atau 'quit' untuk keluar.")


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

