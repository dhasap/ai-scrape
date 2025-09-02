# main.py (Remote Control v3.1 - Edisi Multi-Server Hacker)
import os
import json
import sys
import time
from urllib.parse import urljoin
from dotenv import load_dotenv
import requests
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
import pyfiglet

# --- Konfigurasi ---
load_dotenv()
# BARU: Membaca semua VERCEL_API_URL dari .env secara dinamis
API_URLS = [os.environ.get(f"VERCEL_API_URL_{i}") for i in range(1, 10) if os.environ.get(f"VERCEL_API_URL_{i}")]
console = Console()

def call_api(payload):
    """Fungsi inti untuk mengirim perintah ke 'Otak AI' dengan dukungan failover multi-server."""
    spinner = Spinner("dots", text=" Menghubungi Otak AI...")
    live = Live(spinner, console=console, transient=True, refresh_per_second=10)
    
    for i, base_url in enumerate(API_URLS):
        server_name = f"Server {i+1}"
        endpoint = f"{base_url.rstrip('/')}/api/scrape"
        live.update(Panel(f"[bold cyan]Menghubungi {server_name}...[/bold cyan]\n[dim]{endpoint}[/dim]", border_style="cyan"))

        try:
            with live:
                response = requests.post(endpoint, json=payload, timeout=180)
                response.raise_for_status()
            console.print(f"[bold green]✅ Koneksi ke {server_name} berhasil.[/bold green]")
            return response.json()
        except requests.exceptions.RequestException as e:
            console.print(f"[bold red]❌ Gagal menghubungi {server_name}: {e}[/bold red]")
            if i < len(API_URLS) - 1:
                 console.print(f"[yellow]Mencoba server berikutnya ({i+2})...[/yellow]")
                 time.sleep(1)
            else:
                return {"status": "error", "message": "Semua server API gagal dihubungi."}
    return {"status": "error", "message": "Tidak ada URL API yang dikonfigurasi."}

def display_results(response_data):
    """Menampilkan hasil dari API dengan gaya hacker."""
    if not response_data:
        console.print(Panel("[bold red]SYSTEM FAILURE: NO RESPONSE FROM SERVER[/bold red]", title="[ERROR]", border_style="red"))
        return

    status = response_data.get("status")
    if status == "error":
        message = response_data.get('message', 'UNKNOWN ANOMALY')
        console.print(Panel(f"[bold red]API ERROR:[/bold red]\n{message}", title="[TRANSMISSION FAILED]", border_style="red"))
        return

    action = response_data.get("action", "UNKNOWN_ACTION")
    
    table = Table(show_header=True, header_style="bold magenta", border_style="bright_black", title="[bold]--=[ AI RESPONSE LOG ]=--[/bold]")
    table.add_column("SYSTEM LOG", style="dim", width=20)
    table.add_column("DETAILS")
    table.add_row("[AI DECISION]", f"[bold green]{action.upper()}[/bold green]")

    if action == "extract":
        data = response_data.get("data", {})
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        table.add_row("[EXTRACTED DATA]", Syntax(json_str, "json", theme="solarized-dark", line_numbers=True))
            
    elif action == "navigate":
        url = response_data.get("url")
        instruction = response_data.get("instruction")
        table.add_row("[NEXT TARGET URL]", f"[link={url}]{url}[/link]")
        table.add_row("[NEW DIRECTIVE]", f"[italic cyan]{instruction}[/italic]")

    elif action == "respond":
        response_text = response_data.get("response", "No text response.")
        table.add_row("[AI RESPONSE]", f"[bright_blue]{response_text}[/bright_blue]")
        
    console.print(table)

def print_header():
    """Mencetak banner utama."""
    ascii_art = pyfiglet.figlet_format('AI-SCRAPE', font='doom')
    console.print(Panel(f"[bold green]{ascii_art}[/bold green]", 
                        title="[v3.1 MULTI-SERVER]", 
                        subtitle="[cyan]READY FOR DIRECTIVES[/cyan]", 
                        border_style="green"))

def interactive_session():
    """Loop utama untuk sesi interaktif dengan Otak AI."""
    print_header()

    try:
        current_url = console.input("[bold yellow]TARGET URL> [/bold yellow]")
        if not current_url:
            console.print("[bold red]FATAL: Target URL tidak boleh kosong. Operasi dibatalkan.[/bold red]")
            return

        current_instruction = "analisa halaman ini dan berikan ringkasan"
        
        while True:
            payload = {"url": current_url, "instruction": current_instruction}
            
            response = call_api(payload)
            display_results(response)
            
            if response.get("action") == "navigate":
                current_url = response.get("url")
                current_instruction = response.get("instruction")
                console.print(Panel(f"STATE UPDATED. NEXT TARGET: [cyan]{current_url}[/cyan]", border_style="yellow"))
            
            next_instruction = console.input(f"[bold yellow]DIRECTIVE ({current_url[:50]}...)> [/bold yellow]")

            if not next_instruction or next_instruction.lower() in ['exit', 'quit', 'keluar']:
                break
            
            current_instruction = next_instruction

    except (KeyboardInterrupt, EOFError):
        console.print("\n[bold red]SHUTDOWN SIGNAL DETECTED.[/bold red]")
    
    console.print("\n[bold yellow]...CONNECTION TERMINATED...[/bold yellow]")


if __name__ == "__main__":
    if not API_URLS:
        console.print(Panel("[bold red]! PERINGATAN KONFIGURASI ![/bold red]\nFile [cyan].env[/cyan] tidak ditemukan atau variabel [cyan]VERCEL_API_URL_1[/cyan] tidak diatur. Silakan periksa file [cyan]README.md[/cyan].", border_style="red"))
        sys.exit(1)
    interactive_session()

