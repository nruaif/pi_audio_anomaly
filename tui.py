import time
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .config import memory_info, sse_clients

def generate_layout():
    layout = Layout()
    layout.split_column(Layout(name="header", size=3), Layout(name="main"))
    layout["main"].split_row(Layout(name="live_feed", ratio=1), Layout(name="alerts", ratio=1))
    return layout

def update_ui(layout, status_msg, anomaly_score, warmup, alert_history, sys_messages):
    header_text = Text("mn10 Audio System (DB BLOB + 30s Context)", style="bold white on blue", justify="center")
    header_text.append(f"\nStatus: {status_msg}", style="yellow")
    layout["header"].update(Panel(header_text))

    live_table = Table(expand=True, show_edge=False)
    live_table.add_column("Metric", style="cyan")
    live_table.add_column("Value", justify="right", style="green")

    if warmup:
        live_table.add_row("Anomaly Score", "[dim yellow]Warming up...[/]")
    else:
        live_table.add_row("Anomaly Score",
                           f"[{'bold red' if anomaly_score > 3.0 else 'bold green'}]{anomaly_score:.2f}[/]")

    live_table.add_row("Memory Usage", f"[magenta]{memory_info['mem_mb']:.1f} MB[/]")
    live_table.add_row("Web Clients", f"[yellow]{len(sse_clients)} Connected[/]")
    layout["live_feed"].update(Panel(live_table, title="[bold]Live Analysis Stream[/]", border_style="cyan"))

    alert_table = Table(expand=True, show_edge=False)
    alert_table.add_column("Time", style="dim")
    alert_table.add_column("Event", style="bold red")
    alert_table.add_column("Score", justify="right")
    for alert in reversed(alert_history[-10:]):
        alert_table.add_row(time.strftime("%H:%M:%S", time.localtime(alert['timestamp'])), alert['class_name'],
                            f"{alert['score']:.2f}")

    alert_content = Layout()
    alert_content.split_column(
        Layout(alert_table, ratio=2),
        Layout(Panel("\n".join(sys_messages[-5:]), title="System Logs (Press 'k' to Debug Mic)", border_style="dim"),
               size=7)
    )
    layout["alerts"].update(Panel(alert_content, title="[bold red]Anomaly Alerts[/]", border_style="red"))
