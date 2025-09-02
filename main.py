# main.py (Remote Control v3.2 - Edisi Konversasional)
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
from rich.markdown import Markdown
import pyfiglet

# --- Konfigurasi ---
load_dotenv()
API_URLS = [os.environ.get(f"VERCEL_API_URL_{i}") for i in range(1, 10) if os.environ.get(f"VERCEL_API_URL_{i}")]
console = Console()

def call_api(payload):
    # ... (Fungsi ini tidak berubah)
    # Ia akan mengirim payload yang kini berisi 'conversation_history'
    pass

def display_results(response_data):
    if not response_data:
        console.print(Panel("[bold red]SYSTEM FAILURE[/bold red]", title="[ERROR]"))
        return

    # ================== BARU: Menampilkan Komentar AI ==================
    commentary = response_data.get("commentary")
    if commentary:
        console.print(Panel(Markdown(commentary), title="[bold magenta]ScrapeMind[/bold magenta]", border_style="magenta"))
    # =================================================================

    status = response_data.get("status")
    if status == "error":
        # ... (Penanganan error tidak berubah)
        return

    action = response_data.get("action", "UNKNOWN_ACTION")
    
    # ... (Logika menampilkan tabel hasil tidak berubah)

def print_header():
    # ... (Tidak berubah)
    pass

def interactive_session():
    print_header()
    
    # ... (Logika validasi URL tidak berubah)
    current_url = console.input("[bold yellow]TARGET URL> [/bold yellow]")
    
    # ================== BARU: Inisialisasi Riwayat Percakapan ==================
    conversation_history = []
    # =========================================================================

    current_instruction = "analisa halaman ini dan berikan ringkasan"
    
    while True:
        # PERUBAHAN: Mengirim riwayat percakapan di dalam payload
        payload = {
            "url": current_url, 
            "instruction": current_instruction,
            "conversation_history": conversation_history
        }
        
        response = call_api(payload)
        display_results(response)
        
        # Menambahkan percakapan saat ini ke riwayat
        human_turn = {"human": current_instruction}
        ai_turn = {"ai": response.get("commentary", "")}
        conversation_history.extend([human_turn, ai_turn])
        # Batasi riwayat agar tidak terlalu panjang (misal, 5 percakapan terakhir)
        conversation_history = conversation_history[-10:] 
        
        if response.get("action") == "navigate":
            current_url = response.get("url")
            current_instruction = response.get("instruction")
            console.print(Panel(f"STATE UPDATED. NEXT TARGET: [cyan]{current_url}[/cyan]"))
        
        next_instruction = console.input(f"[bold yellow]DIRECTIVE ({current_url[:50]}...)> [/bold yellow]")

        if not next_instruction or next_instruction.lower() in ['exit', 'quit', 'keluar']:
            break
        
        current_instruction = next_instruction

    # ... (Sisa kode tidak berubah)

if __name__ == "__main__":
    interactive_session()

