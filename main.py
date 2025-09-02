# main.py (Remote Control v3.0 - Edisi Hacker)
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
API_URL = os.getenv("API_URL_PRIMARY")
API_URL_BACKUP = os.getenv("API_URL_BACKUP")
console = Console()

def call_api(payload):
    """Fungsi inti untuk mengirim perintah ke 'Otak AI' dengan tampilan live status."""
    urls_to_try = [API_URL, API_URL_BACKUP]
    spinner = Spinner("dots", text=" Menghubungi Otak AI...")
    live = Live(spinner, console=console, transient=True, refresh_per_second=10)
    
    for i, url in enumerate(urls_to_try):
        if not url:
            continue
        
        server_name = "utama" if i == 0 else "backup"
        endpoint = f"{url.rstrip('/')}/api/scrape"
        live.update(Panel(f"[bold cyan]Menghubungi server {server_name}...[/bold cyan]\n[dim]{endpoint}[/dim]", border_style="cyan"))

        try:
            with live:
                response = requests.post(endpoint, json=payload, timeout=180)
                response.raise_for_status()
            console.print(f"[bold green]✅ Koneksi ke server {server_name} berhasil.[/bold green]")
            return response.json()
        except requests.exceptions.RequestException as e:
            console.print(f"[bold red]❌ Gagal menghubungi server {server_name}: {e}[/bold red]")
            if i < len(urls_to_try) - 1 and urls_to_try[i+1]:
                 console.print("[yellow]Mencoba server backup dalam 2 detik...[/yellow]")
                 time.sleep(2)
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
    
    table = Table(show_header=True, header_style="bold magenta", border_style="bright_black")
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
                        title="[v3.0 HACKER-EDITION]", 
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
            
            # Jika aksi terakhir adalah navigasi, perbarui state untuk perintah berikutnya
            if response.get("action") == "navigate":
                current_url = response.get("url")
                current_instruction = response.get("instruction")
                console.print(Panel(f"STATE UPDATED. NEXT TARGET: [cyan]{current_url}[/cyan]", border_style="yellow"))
            
            # Meminta perintah berikutnya dari pengguna
            next_instruction = console.input(f"[bold yellow]DIRECTIVE ({current_url[:50]}...)> [/bold yellow]")

            if not next_instruction or next_instruction.lower() in ['exit', 'quit', 'keluar']:
                break
            
            current_instruction = next_instruction

    except (KeyboardInterrupt, EOFError):
        # EOFError untuk Ctrl+D
        console.print("\n[bold red]SHUTDOWN SIGNAL DETECTED.[/bold red]")
    
    console.print("\n[bold yellow]...CONNECTION TERMINATED...[/bold yellow]")


if __name__ == "__main__":
    if not all([API_URL, API_URL_BACKUP]):
        console.print(Panel("[bold red]! PERINGATAN KONFIGURASI ![/bold red]\nFile [cyan].env[/cyan] tidak ditemukan atau [cyan]API_URL_PRIMARY[/cyan] tidak diatur. Silakan periksa file [cyan]README.md[/cyan].", border_style="red"))
        sys.exit(1)
    interactive_session()

