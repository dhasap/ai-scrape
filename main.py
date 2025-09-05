# main.py (Remote Control v9.0 - Edisi JSON Output)
# Tampilan hasil diubah total untuk menampilkan JSON mentah.
import os
import sys
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
import requests
import json
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
import pyfiglet

# --- Inisialisasi & Konfigurasi Global ---
load_dotenv()

API_URLS = [os.getenv(f"VERCEL_API_URL_{i}") for i in range(1, 10) if os.getenv(f"VERCEL_API_URL_{i}")]
if not API_URLS:
    print(json.dumps({"status": "error", "message": "VERCEL_API_URL_1 tidak ditemukan di file .env"}, indent=2, ensure_ascii=False))
    sys.exit(1)

# Rich Console masih digunakan untuk Spinner dan header
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
            # Spinner masih digunakan untuk memberikan feedback saat menunggu
            spinner_text = f"Menghubungi CognitoScraper [Server {i}/{len(API_URLS)}]..."
            with Live(Spinner("dots", text=spinner_text), console=console, transient=True, refresh_per_second=20):
                response = session.post(api_endpoint, json=payload, timeout=180)
                response.raise_for_status()
                return response.json()
        except requests.exceptions.RequestException as e:
            # Pesan error koneksi tetap ditampilkan di stderr agar tidak mengganggu output JSON
            console.print(f"[bold red]Koneksi ke server {i} gagal: {e}[/bold red]", style="stderr")
            if i < len(API_URLS):
                console.print("[yellow]Mencoba server cadangan...[/yellow]", style="stderr")
            else:
                console.print("[bold red]Semua server gagal dihubungi.[/bold red]", style="stderr")
                return None
    return None

# ==============================================================================
# === FUNGSI TAMPILAN HASIL (DIUBAH TOTAL MENJADI JSON MENTAH) ===
# ==============================================================================
def display_results(response_data: dict):
    """Tampilkan hasil scrape sebagai JSON mentah."""
    if not response_data:
        print(json.dumps({"status": "error", "message": "Tidak ada respons dari server"}, indent=2, ensure_ascii=False))
        return

    print(json.dumps(response_data, indent=2, ensure_ascii=False))


def print_header():
    """Mencetak banner aplikasi."""
    console.clear()
    ascii_art = pyfiglet.figlet_format("CognitoScraper", font="slant")
    console.print(f"[bold green]{ascii_art}[/bold green]")
    console.print("Mode Output JSON. Masukkan URL dan instruksi. Ketik 'exit' atau 'quit' untuk keluar.")
    console.print("-" * 60)


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
    
    while True:
        try:
            domain = urlparse(target_url).netloc
            current_instruction = console.input(f"[bold yellow]✍️ PERINTAH ([/bold yellow][cyan]{domain}[/cyan][bold yellow]) > [/bold yellow]")
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
        
        # Garis pemisah sebelum output JSON
        console.print("-" * 60)
        display_results(response)
        # Garis pemisah setelah output JSON
        console.print("-" * 60)
        
        # Riwayat percakapan tetap dipertahankan untuk konteks AI
        if response and response.get("status") == "success":
            human_turn = {"human": current_instruction}
            # Mengambil data relevan dari respons untuk AI
            ai_comment = response.get("commentary", "")
            ai_data_summary = f"Data terstruktur berisi {len(response.get('structured_data', []))} item." if 'structured_data' in response else "Tidak ada data terstruktur."
            ai_turn = {"ai": f"{ai_comment} {ai_data_summary}"}

            conversation_history.extend([human_turn, ai_turn])
            conversation_history = conversation_history[-10:]
        
        # Logika navigasi tetap ada, URL target akan diperbarui
        if response and response.get("action") == "navigate":
            new_url = response.get("url")
            if new_url:
                target_url = urljoin(target_url, new_url)
                # Notifikasi navigasi ditampilkan di stderr
                console.print(f"✈️ NAVIGASI OTOMATIS. Target baru: {target_url}", style="bold green stderr")


if __name__ == "__main__":
    interactive_session()

