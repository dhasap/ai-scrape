# main.py (Remote Control v6.0 - Edisi Terstruktur)
# Diperbarui untuk menangani dan menampilkan data objek terstruktur dari backend.
import os
import sys
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
import requests
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich.markdown import Markdown
from rich.padding import Padding
from rich import box
import pyfiglet

# --- Inisialisasi & Konfigurasi Global ---
load_dotenv()

# Mengambil semua URL API yang tersedia dari .env (VERCEL_API_URL_1, dst.)
API_URLS = [os.getenv(f"VERCEL_API_URL_{i}") for i in range(1, 10) if os.getenv(f"VERCEL_API_URL_{i}")]
if not API_URLS:
    print("Error Kritis: VERCEL_API_URL_1 tidak ditemukan di file .env. Program tidak dapat berjalan.")
    sys.exit(1)

console = Console()
session = requests.Session()

def is_valid_url(url: str) -> bool:
    """
    Memvalidasi format URL menggunakan urlparse.
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except (ValueError, AttributeError):
        return False

def call_api_with_failover(payload: dict) -> dict | None:
    """
    Mengirim request ke API dengan failover otomatis ke server cadangan.
    """
    for i, base_url in enumerate(API_URLS, 1):
        api_endpoint = urljoin(base_url, "/api/scrape")
        try:
            spinner_text = f"[cyan]Menghubungi CognitoScraper [Server {i}/{len(API_URLS)}]... Menganalisis target...[/cyan]"
            with Live(Spinner("dots", text=spinner_text), console=console, transient=True, refresh_per_second=20):
                response = session.post(api_endpoint, json=payload, timeout=180) # Timeout diperpanjang
                response.raise_for_status()
                return response.json()
        except requests.exceptions.RequestException as e:
            console.print(f"[bold red] koneksi ke server {i} gagal:[/bold red] {e}")
            if i < len(API_URLS):
                console.print("[yellow]Mencoba server cadangan...[/yellow]")
            else:
                console.print("[bold red]Semua server gagal dihubungi. Periksa koneksi internet atau status server Vercel.[/bold red]")
                return None
    return None

# ==============================================================================
# === FUNGSI TAMPILAN HASIL (DIROMBAK TOTAL UNTUK DATA TERSTRUKTUR) ===
# ==============================================================================
def display_results(response_data: dict):
    """
    Menampilkan data dari API dengan format visual yang terstruktur.
    Kini mendukung 'extract_structured' untuk menampilkan objek data.
    """
    if not response_data:
        console.print(Panel("[bold red]KEGAGALAN SISTEM[/bold red]\nTidak ada respons valid dari server.", title="[ERROR]", border_style="red"))
        return

    # Menampilkan 'reasoning' (pemikiran AI) jika ada.
    reasoning = response_data.get("reasoning")
    if reasoning:
        console.print(Panel(f"[italic yellow]{reasoning}[/italic yellow]", title="[bold yellow]🧠 PENALARAN AI[/bold yellow]", border_style="yellow", expand=False))

    # Menampilkan 'commentary' (komentar AI) jika ada.
    commentary = response_data.get("commentary")
    if commentary:
        console.print(Panel(Markdown(commentary), title="[bold magenta]💬 KOMENTAR AI[/bold magenta]", border_style="magenta", expand=False))

    status = response_data.get("status")
    if status == "error":
        error_message = response_data.get('message', 'Tidak ada detail kesalahan.')
        console.print(Panel(f"[bold red]PESAN ERROR DARI BACKEND[/bold red]\n{error_message}", title="[ERROR]", border_style="red"))
        return

    action = response_data.get("action")

    # --- LOGIKA BARU: Menangani hasil ekstraksi terstruktur ---
    if action == "extract_structured":
        structured_data = response_data.get("structured_data", [])
        if not structured_data:
            console.print(Panel("[yellow]AI melaporkan tidak ada data terstruktur yang bisa diekstrak.[/yellow]", title="Info", border_style="yellow"))
            return

        console.print(Panel("[bold green]📊 HASIL EKSTRAKSI TERSTRUKTUR[/bold green]", expand=False, border_style="green"))
        
        # Batasi tampilan hingga 5 item pertama untuk keterbacaan
        display_limit = 5
        for index, item in enumerate(structured_data[:display_limit]):
            # Membuat tabel untuk setiap item agar rapi
            item_table = Table(box=box.ROUNDED, show_header=False, title=f"[cyan]Item #{index + 1}[/cyan]")
            item_table.add_column("Key", style="dim", width=15)
            item_table.add_column("Value", style="bright_white")

            if item.get('title'):
                item_table.add_row("Judul", item['title'])
            if item.get('url'):
                item_table.add_row("URL", f"[link={item['url']}]{item['url']}[/link]")
            if item.get('thumbnail'):
                item_table.add_row("Thumbnail", f"[link={item['thumbnail']}]{item['thumbnail']}[/link]")

            # Menangani objek chapter yang bersarang
            if isinstance(item.get('latest_chapter'), dict):
                chapter = item['latest_chapter']
                chapter_title = chapter.get('title', 'N/A')
                chapter_url = chapter.get('url')
                display_chapter = f"{chapter_title}"
                if chapter_url:
                    display_chapter += f" ([link={chapter_url}]link[/link])"
                item_table.add_row("Chapter", display_chapter)
            
            console.print(item_table)

        if len(structured_data) > display_limit:
            console.print(f"[italic]...dan {len(structured_data) - display_limit} item lainnya.[/italic]")

    # --- LOGIKA LAMA: Menangani 'extract' (sebagai fallback) ---
    elif action == "extract":
        data = response_data.get("data", {})
        if not data:
            console.print(Panel("[yellow]AI melaporkan tidak ada data (flat) yang bisa diekstrak.[/yellow]", title="Info", border_style="yellow"))
            return
        
        table = Table(title="[bold green]📊 HASIL EKSTRAKSI DATA (FLAT)[/bold green]", show_header=True, header_style="bold cyan")
        table.add_column("Nama Data", style="dim", width=25)
        table.add_column("Hasil (Maks. 10 item)")

        for key, values in data.items():
            display_value = "\n".join(map(str, values[:10]))
            if len(values) > 10:
                display_value += f"\n[italic]...dan {len(values) - 10} item lainnya.[/italic]"
            
            table.add_row(key, Padding(display_value, (1, 2)))
        
        console.print(table)

    elif action == "respond":
        response_text = response_data.get("response", "AI tidak memberikan respons verbal.")
        console.print(Panel(Markdown(response_text), title="[bold blue]🗣️ RESPON AI[/bold blue]", border_style="blue"))


def print_header():
    """Mencetak banner aplikasi dengan gaya 'hacker'."""
    console.clear()
    ascii_art = pyfiglet.figlet_format("CognitoScraper", font="slant")
    console.print(f"[bold green]{ascii_art}[/bold green]")
    console.print(Panel("Selamat datang di [bold]Remote Control v6.0[/bold]. Terhubung dengan agen AI. Ketik 'exit' atau 'quit' untuk keluar.", expand=False, border_style="blue"))

def interactive_session():
    """Fungsi utama yang menjalankan loop interaktif sesi CLI."""
    print_header()
    
    while True:
        target_url = console.input("[bold yellow]🔗 MASUKKAN TARGET URL > [/bold yellow]")
        if is_valid_url(target_url):
            break
        console.print("[bold red]URL tidak valid. Harap masukkan URL lengkap (contoh: https://www.example.com)[/bold red]")

    conversation_history = []
    current_instruction = "analisa halaman ini, berikan ringkasan, dan ekstrak daftar komik terbaru sebagai objek terstruktur berisi judul, url, thumbnail, dan chapter terbaru."
    
    while True:
        payload = {
            "url": target_url, 
            "instruction": current_instruction,
            "conversation_history": conversation_history
        }
        
        response = call_api_with_failover(payload)
        display_results(response)
        
        if response and response.get("status") == "success":
            human_turn = {"human": current_instruction}
            ai_turn = {"ai": response.get("commentary", "")}
            conversation_history.extend([human_turn, ai_turn])
            conversation_history = conversation_history[-10:]
        
        if response and response.get("action") == "navigate":
            new_url = response.get("url")
            target_url = urljoin(target_url, new_url)
            current_instruction = response.get("instruction", "Lanjutkan analisis di halaman baru ini.")
            console.print(Panel(f"✈️ [bold]NAVIGASI OTOMATIS.[/bold] Target baru: [cyan]{target_url}[/cyan]", expand=False, border_style="green"))
        
        try:
            domain = urlparse(target_url).netloc
            next_instruction = console.input(f"\n[bold yellow]✍️ PERINTAH ([/bold yellow][cyan]{domain}[/cyan][bold yellow]) > [/bold yellow]")
        except KeyboardInterrupt:
            console.print("\n\n[bold cyan]Sesi diakhiri oleh pengguna.[/bold cyan]")
            break

        if not next_instruction.strip() or next_instruction.lower() in ['exit', 'quit', 'keluar']:
            console.print("[bold cyan]Terima kasih telah menggunakan CognitoScraper. Sampai jumpa![/bold cyan]")
            break
        
        current_instruction = next_instruction

if __name__ == "__main__":
    interactive_session()
