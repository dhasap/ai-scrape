# main.py (Remote Control v8.0 - Edisi Adaptif)
# Tampilan hasil dirombak untuk beradaptasi: panel tunggal untuk data tunggal, tabel untuk data ganda.
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
from rich.syntax import Syntax
from rich import box
import pyfiglet

# --- Inisialisasi & Konfigurasi Global ---
load_dotenv()

API_URLS = [os.getenv(f"VERCEL_API_URL_{i}") for i in range(1, 10) if os.getenv(f"VERCEL_API_URL_{i}")]
if not API_URLS:
    print("Error Kritis: VERCEL_API_URL_1 tidak ditemukan di file .env. Program tidak dapat berjalan.")
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
            spinner_text = f"[cyan]Menghubungi CognitoScraper [Server {i}/{len(API_URLS)}]... Menganalisis target...[/cyan]"
            with Live(Spinner("dots", text=spinner_text), console=console, transient=True, refresh_per_second=20):
                response = session.post(api_endpoint, json=payload, timeout=180)
                response.raise_for_status()
                return response.json()
        except requests.exceptions.RequestException as e:
            console.print(f"[bold red] koneksi ke server {i} gagal:[/bold red] {e}")
            if i < len(API_URLS):
                console.print("[yellow]Mencoba server cadangan...[/yellow]")
            else:
                console.print("[bold red]Semua server gagal dihubungi.[/bold red]")
                return None
    return None

# ==============================================================================
# === FUNGSI TAMPILAN HASIL (DIROMBAK DENGAN LOGIKA ADAPTIF) ===
# ==============================================================================
def display_results(response_data: dict):
    """
    Menampilkan data secara adaptif.
    - Panel tunggal jika hasil item hanya punya satu kunci data (misal: hanya HTML).
    - Tabel jika hasil item punya banyak kunci data (misal: judul, url, dll).
    """
    if not response_data:
        console.print(Panel("[bold red]KEGAGALAN SISTEM[/bold red]\nTidak ada respons valid dari server.", title="[ERROR]", border_style="red"))
        return

    reasoning = response_data.get("reasoning")
    if reasoning:
        console.print(Panel(f"[italic yellow]{reasoning}[/italic yellow]", title="[bold yellow]🧠 PENALARAN AI[/bold yellow]", border_style="yellow", expand=False))

    commentary = response_data.get("commentary")
    if commentary:
        console.print(Panel(Markdown(commentary), title="[bold magenta]💬 KOMENTAR AI[/bold magenta]", border_style="magenta", expand=False))

    status = response_data.get("status")
    if status == "error":
        error_message = response_data.get('message', 'Tidak ada detail kesalahan.')
        console.print(Panel(f"[bold red]PESAN ERROR DARI BACKEND[/bold red]\n{error_message}", title="[ERROR]", border_style="red"))
        return

    action = response_data.get("action")

    if action == "extract_structured":
        structured_data = response_data.get("structured_data", [])
        if not structured_data:
            console.print(Panel("[yellow]AI melaporkan tidak ada data terstruktur yang bisa diekstrak.[/yellow]", title="Info", border_style="yellow"))
            return

        console.print(Panel("[bold green]📊 HASIL EKSTRAKSI ADAPTIF[/bold green]", expand=False, border_style="green"))
        
        display_limit = 5
        for index, item in enumerate(structured_data[:display_limit]):
            # --- LOGIKA ADAPTIF BARU ---
            # Jika item hanya memiliki satu kunci (misalnya, hanya 'raw_html')
            if len(item) == 1:
                key, value = next(iter(item.items()))
                display_key = key.replace('_', ' ').title()
                
                # Menyiapkan konten untuk ditampilkan
                content_display = ""
                if value is not None:
                    # Jika kuncinya mengandung 'html', gunakan penyorotan sintaks
                    if 'html' in key.lower():
                        content_display = Syntax(str(value), "html", theme="monokai", line_numbers=True)
                    else:
                        content_display = str(value)
                else:
                    content_display = "[italic]N/A[/italic]"

                # Tampilkan dalam satu panel besar
                console.print(
                    Panel(
                        content_display,
                        title=f"[cyan]Item #{index + 1}: {display_key}[/cyan]",
                        border_style="magenta",
                        expand=True
                    )
                )
            # Jika item memiliki banyak kunci, gunakan format tabel
            else:
                item_table = Table(box=box.ROUNDED, show_header=False, title=f"[cyan]Item #{index + 1}[/cyan]")
                item_table.add_column("Key", style="dim", width=20)
                item_table.add_column("Value", style="bright_white", overflow="fold")

                for key, value in item.items():
                    display_value = ""
                    if isinstance(value, dict):
                        nested_parts = [f"{sub_key.title()}: {sub_value}" for sub_key, sub_value in value.items() if sub_value]
                        display_value = ", ".join(nested_parts)
                    elif value is not None:
                        display_value = str(value)
                    else:
                        display_value = "[italic]N/A[/italic]"
                    
                    display_key = key.replace('_', ' ').title()
                    item_table.add_row(display_key, display_value)
                
                console.print(item_table)

        if len(structured_data) > display_limit:
            console.print(f"[italic]...dan {len(structured_data) - display_limit} item lainnya.[/italic]")

    elif action == "extract":
        # ... (logika fallback tidak diubah)
        pass

    elif action == "respond":
        response_text = response_data.get("response", "AI tidak memberikan respons verbal.")
        console.print(Panel(Markdown(response_text), title="[bold blue]🗣️ RESPON AI[/bold blue]", border_style="blue"))


def print_header():
    """Mencetak banner aplikasi."""
    console.clear()
    ascii_art = pyfiglet.figlet_format("CognitoScraper", font="slant")
    console.print(f"[bold green]{ascii_art}[/bold green]")
    console.print(Panel("Selamat datang di [bold]Remote Control v8.0 (Adaptif)[/bold]. Terhubung dengan agen AI.", expand=False, border_style="blue"))

def interactive_session():
    """Fungsi utama yang menjalankan loop interaktif sesi CLI."""
    print_header()
    
    while True:
        target_url = console.input("[bold yellow]🔗 MASUKKAN TARGET URL > [/bold yellow]")
        if is_valid_url(target_url):
            break
        console.print("[bold red]URL tidak valid. Harap masukkan URL lengkap.[/bold red]")

    conversation_history = []
    current_instruction = "analisa halaman ini dan ekstrak daftar 5 komik teratas. Untuk setiap komik, berikan judul, url, dan thumbnail."
    
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
            console.print("[bold cyan]Terima kasih telah menggunakan CognitoScraper.[/bold cyan]")
            break
        
        current_instruction = next_instruction

if __name__ == "__main__":
    interactive_session()

