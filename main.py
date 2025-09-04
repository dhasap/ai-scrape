# main.py (Remote Control v5.1 - Edisi Hacker)
# Disesuaikan untuk backend D.1 dengan tampilan CLI yang disempurnakan.
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

def display_results(response_data: dict):
    """
    Menampilkan data dari API dengan format visual yang terstruktur.
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
    
    if action == "extract":
        data = response_data.get("structured_data", {})
        if not data:
            console.print(Panel("[yellow]AI melaporkan tidak ada data yang bisa diekstrak sesuai instruksi.[/yellow]", title="Info", border_style="yellow"))
            return
        
        table = Table(title="[bold green]📊 HASIL EKSTRAKSI DATA[/bold green]", show_header=True, header_style="bold cyan")
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
    console.print(Panel("Selamat datang di [bold]Remote Control v5.1[/bold]. Terhubung dengan agen AI. Ketik 'exit' atau 'quit' untuk keluar.", expand=False, border_style="blue"))

def interactive_session():
    """Fungsi utama yang menjalankan loop interaktif sesi CLI."""
    print_header()
    
    while True:
        target_url = console.input("[bold yellow]🔗 MASUKKAN TARGET URL > [/bold yellow]")
        if is_valid_url(target_url):
            break
        console.print("[bold red]URL tidak valid. Harap masukkan URL lengkap (contoh: https://www.example.com)[/bold red]")

    conversation_history = []
    current_instruction = "analisa halaman ini secara menyeluruh, berikan ringkasan, dan sarankan 2-3 hal spesifik yang bisa diekstrak dari sini."
    
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
            conversation_history = conversation_history[-10:] # Batasi 6 percakapan terakhir
        
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
