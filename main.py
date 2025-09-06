# main.py (Versi 12.0 - Pemilihan User-Agent)
# Menambahkan opsi pemilihan User-Agent di mode interaktif dan otonom.
import os
import sys
import json
import argparse
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
import requests
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich.markdown import Markdown
import pyfiglet
import questionary

# --- Inisialisasi & Konfigurasi Global ---
load_dotenv()

API_URLS = [os.getenv(f"VERCEL_API_URL_{i}") for i in range(1, 10) if os.getenv(f"VERCEL_API_URL_{i}")]
if not API_URLS:
    print("Error Kritis: VERCEL_API_URL_1 tidak ditemukan di file .env.")
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

def call_api_with_failover(payload: dict, endpoint: str = "/api/scrape") -> dict | None:
    """
    Mengirim request ke API dengan failover otomatis.
    Kini mendukung endpoint yang berbeda.
    """
    for i, base_url in enumerate(API_URLS, 1):
        api_endpoint_url = urljoin(base_url, endpoint)
        try:
            spinner_text = f"[cyan]Menghubungi Otak AI [Server {i}/{len(API_URLS)}]... Misi: {payload.get('instruction', '')[:50]}...[/cyan]"
            with Live(Spinner("dots", text=spinner_text), console=console, transient=True, refresh_per_second=20):
                # Timeout diperpanjang untuk misi jangka panjang
                timeout = 300 if endpoint == "/api/chain-scrape" else 180
                response = session.post(api_endpoint_url, json=payload, timeout=timeout)
                response.raise_for_status()
                return response.json()
        except requests.exceptions.RequestException as e:
            console.print(f"[bold red]Koneksi ke server {i} gagal:[/bold red] {e}")
            if i < len(API_URLS):
                console.print("[yellow]Mencoba server cadangan...[/yellow]")
            else:
                console.print("[bold red]Semua server gagal dihubungi.[/bold red]")
                return None
    return None

def display_results(response_data: dict):
    """
    Menampilkan ringkasan respons AI dan JSON data murni.
    (Mode Power User)
    """
    if not response_data:
        error_panel = Panel("[bold red]KEGAGALAN SISTEM[/bold red]\nTidak ada respons valid dari server.", title="[ERROR]", border_style="red", expand=False)
        console.print(error_panel)
        return

    # --- Panel Ringkasan ---
    status = response_data.get("status", "N/A")
    status_color = "green" if status == "success" else "red"
    
    reasoning = response_data.get("reasoning", "Tidak ada penalaran dari AI.")
    commentary = response_data.get("commentary", "Tidak ada komentar dari AI.")

    summary_text = (
        f"[bold]Status:[/] [{status_color}]{status}[/{status_color}]\n\n"
        f"[bold yellow]Penalaran AI:[/] [italic yellow]{reasoning}[/italic yellow]\n\n"
        f"[bold magenta]Komentar AI:[/] [italic magenta]{commentary}[/italic magenta]"
    )
    
    summary_panel = Panel(summary_text, title="Ringkasan Respons AI", expand=False, border_style="cyan")
    console.print(summary_panel)

    # --- JSON Data Murni ---
    scraped_data = response_data.get("structured_data")
    if scraped_data:
        console.print("[bold green]Scraped Data (JSON):[/bold green]")
        console.print(json.dumps(scraped_data, indent=2, ensure_ascii=False))
    elif response_data.get("action") == "navigate":
         console.print("[cyan]Aksi selanjutnya adalah NAVIGASI. Tidak ada data untuk ditampilkan.[/cyan]")
    elif response_data.get("action") == "respond":
         console.print(f"[cyan]AI merespons: {response_data.get('response')}[/cyan]")


def print_header():
    """Mencetak banner aplikasi."""
    console.clear()
    ascii_art = pyfiglet.figlet_format("CognitoScraper", font="slant")
    console.print(f"[bold green]{ascii_art}[/bold green]")

# ==============================================================================
# === MODE INTERAKTIF (DIMODIFIKASI) ===
# ==============================================================================
def interactive_session():
    """Fungsi yang menjalankan loop interaktif sesi CLI."""
    print_header()
    console.print(Panel("Mode Interaktif. Masukkan URL dan instruksi. Hasil lengkap butuh instruksi detail.", expand=False, border_style="blue"))

    target_url = ""
    while not is_valid_url(target_url):
        target_url = console.input("[bold yellow]🔗 MASUKKAN TARGET URL > [/bold yellow]")
        if not is_valid_url(target_url):
            console.print("[bold red]URL tidak valid.[/bold red]")

    # --- BARU: Pemilihan User-Agent ---
    user_agent_choice = questionary.select(
        "Pilih User-Agent untuk misi ini:",
        choices=[
            questionary.Choice("Browser Standar (Untuk situs web umum)", 'default'),
            questionary.Choice("ExoPlayer (Untuk streaming/API media)", 'exoplayer')
        ],
        pointer="»"
    ).ask()

    user_agent_string = None
    if user_agent_choice == 'exoplayer':
        user_agent_string = "ExoPlayerDemo/2.15.1 (Linux; Android 13) ExoPlayerLib/2.15.1"
        console.print(f"[cyan]✓ Mode ExoPlayer diaktifkan.[/cyan]")
    else:
        console.print(f"[cyan]✓ Mode Browser Standar diaktifkan.[/cyan]")
    # --- AKHIR BARU ---

    conversation_history = []
    current_instruction = "analisa halaman ini dan berikan saran scraping"
    
    while True:
        payload = {
            "url": target_url, 
            "instruction": current_instruction, 
            "conversation_history": conversation_history,
            "userAgent": user_agent_string
        }
        
        response = call_api_with_failover(payload, endpoint="/api/scrape")
        
        console.print("-" * 60)
        display_results(response)
        console.print("-" * 60)
        
        if response and response.get("status") == "success":
            human_turn = {"human": current_instruction}
            ai_comment = response.get("commentary", "")
            ai_data_summary = f"Data terstruktur berisi {len(response.get('structured_data', []))} item." if 'structured_data' in response else ""
            ai_turn = {"ai": f"{ai_comment} {ai_data_summary}".strip()}
            conversation_history.extend([human_turn, ai_turn])
            conversation_history = conversation_history[-10:]
        
        if response and response.get("action") == "navigate":
            new_url = response.get("url")
            target_url = urljoin(target_url, new_url)
            current_instruction = response.get("instruction", "Lanjutkan analisis di halaman baru ini.")
            console.print(f"✈️ [bold green]NAVIGASI OTOMATIS.[/bold green] Target baru: [cyan]{target_url}[/cyan]")
        
        try:
            domain = urlparse(target_url).netloc
            next_instruction = console.input(f"\n[bold yellow]✍️ PERINTAH ([/bold yellow][cyan]{domain}[/cyan][bold yellow]) > [/bold yellow]")
        except KeyboardInterrupt:
            console.print("\n\n[bold cyan]Sesi diakhiri oleh pengguna.[/bold cyan]")
            break

        if not next_instruction.strip() or next_instruction.lower() in ['exit', 'quit', 'keluar']:
            console.print("[bold cyan]Terima kasih telah menggunakan CognitoScraper.[/bold cyan]")
            break
        
        current_instruction = next_instruction

# ==============================================================================
# === MODE OTONOM / CRAWLER (DIMODIFIKASI) ===
# ==============================================================================
def run_crawler_session(args):
    """Menjalankan scraper dalam mode otonom non-interaktif."""
    print_header()
    console.print(Panel(f"Mode Otonom. Menjalankan misi dan akan menyimpan hasil ke [cyan]{args.output}[/cyan].", expand=False, border_style="blue"))
    
    instruction = ""
    if args.recipe:
        try:
            with open(args.recipe, 'r', encoding='utf-8') as f:
                instruction = f.read().strip()
            console.print(f"[green]✓ Resep '{args.recipe}' berhasil dimuat.[/green]")
        except FileNotFoundError:
            console.print(f"[bold red]❌ Error: File resep '{args.recipe}' tidak ditemukan.[/bold red]")
            sys.exit(1)
    else:
        instruction = args.instruction

    if not instruction:
        console.print("[bold red]❌ Error: Instruksi atau resep tidak diberikan.[/bold red]")
        sys.exit(1)

    # --- BARU: Pemilihan User-Agent dari argumen ---
    user_agent_string = None
    if args.user_agent == 'exoplayer':
        user_agent_string = "ExoPlayerDemo/2.15.1 (Linux; Android 13) ExoPlayerLib/2.15.1"
        console.print(f"🕵️ [bold]User-Agent:[/bold] [cyan]ExoPlayer (Media Player)[/cyan]")
    else:
        console.print(f"🕵️ [bold]User-Agent:[/bold] [cyan]Browser Standar[/cyan]")
    # --- AKHIR BARU ---

    console.print(f"🎯 [bold]Target:[/bold] {args.url}")
    console.print(f"📝 [bold]Misi:[/bold] {instruction[:120]}...")
    
    payload = {
        "url": args.url, 
        "instruction": instruction,
        "userAgent": user_agent_string
    }
    
    response_data = call_api_with_failover(payload, endpoint="/api/chain-scrape")
    
    if response_data:
        console.print("\n[bold green]✓ Misi Selesai.[/bold green]")
        try:
            # Kita hanya menyimpan hasil akhir dari chain scrape (biasanya data atau error)
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            console.print(f"[green]Hasil lengkap telah disimpan di [cyan]'{args.output}'[/cyan][/green]")
        except Exception as e:
            console.print(f"[bold red]❌ Error: Gagal menyimpan hasil ke file. {e}[/bold red]")
    else:
        console.print("[bold red]❌ Misi Gagal: Tidak ada respons dari server.[/bold red]")

# ==============================================================================
# === PINTU MASUK / DISPATCHER (DIMODIFIKASI) ===
# ==============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CognitoScraper - Agen Scraping Cerdas. Jalankan tanpa argumen untuk mode interaktif."
    )
    
    parser.add_argument('--url', type=str, help='URL target untuk memulai scraping otonom.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--instruction', type=str, help='Instruksi langsung untuk crawler.')
    group.add_argument('--recipe', type=str, help='Path ke file teks yang berisi instruksi.')
    parser.add_argument('--output', type=str, help='Nama file JSON untuk menyimpan hasil output.')
    # --- BARU: Argumen untuk User-Agent ---
    parser.add_argument(
        '--user-agent', 
        type=str, 
        choices=['default', 'exoplayer'], 
        default='default', 
        help="Pilih User-Agent: 'default' untuk browser atau 'exoplayer' untuk media player."
    )
    # --- AKHIR BARU ---

    args = parser.parse_args()

    # Logika "Dispatcher": Memilih mode berdasarkan argumen yang diberikan
    if args.url and (args.instruction or args.recipe) and args.output:
        run_crawler_session(args)
    else:
        # Jika tidak ada argumen (atau tidak lengkap), jalankan mode interaktif
        if len(sys.argv) > 1:
            console.print("[yellow]Argumen tidak lengkap untuk mode otonom. Masuk ke mode interaktif.[/yellow]\n")
        interactive_session()
