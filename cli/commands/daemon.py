"""Daemon management commands."""
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from backend.app.config import settings
from backend.app.database.session import SessionLocal
from backend.app.models import DaemonConfig, DaemonState
from backend.app.services.logger import DaemonLogger

app = typer.Typer()
console = Console()


@app.command()
def create(
    name: str = typer.Argument(..., help="Configuration name"),
    keywords: str = typer.Option(..., help="Job keywords to search"),
    location: Optional[str] = typer.Option(None, help="Location filter"),
    remote: bool = typer.Option(False, help="Remote jobs only"),
    platforms: str = typer.Option("linkedin,indeed", help="Platforms (comma-separated)"),
    max_daily: int = typer.Option(50, help="Maximum applications per day"),
):
    """Create a new daemon configuration."""
    db = SessionLocal()

    try:
        # Check if name exists
        existing = db.query(DaemonConfig).filter(DaemonConfig.name == name).first()
        if existing:
            console.print(f"[red]Configuration '{name}' already exists[/red]")
            return

        config = DaemonConfig(
            name=name,
            keywords=keywords,
            location=location,
            remote_only=remote,
            platforms=platforms,
            max_applications_per_day=max_daily,
        )

        db.add(config)
        db.commit()

        console.print(f"[green]✅ Created daemon configuration '{name}'[/green]")
        console.print(f"Keywords: {keywords}")
        console.print(f"Platforms: {platforms}")
        console.print(f"Max daily applications: {max_daily}")
        console.print(f"\nStart daemon: [cyan]job-apply daemon start {name}[/cyan]")

    finally:
        db.close()


@app.command()
def list():
    """List all daemon configurations."""
    db = SessionLocal()

    try:
        configs = db.query(DaemonConfig).all()

        if not configs:
            console.print("[yellow]No daemon configurations found.[/yellow]")
            console.print("Create one with: [cyan]job-apply daemon create[/cyan]")
            return

        table = Table(title="Daemon Configurations")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Keywords", style="blue")
        table.add_column("Platforms", style="magenta")
        table.add_column("Max Daily", style="green")
        table.add_column("Active", style="yellow")

        for config in configs:
            table.add_row(
                str(config.id),
                config.name,
                config.keywords[:30] + "..." if len(config.keywords) > 30 else config.keywords,
                config.platforms,
                str(config.max_applications_per_day),
                "✓" if config.is_active else "",
            )

        console.print(table)

    finally:
        db.close()


@app.command()
def start(
    name: str = typer.Argument(..., help="Configuration name"),
    foreground: bool = typer.Option(False, "--foreground", "-f", help="Run in foreground"),
):
    """Start the daemon with specified configuration."""
    db = SessionLocal()

    try:
        config = db.query(DaemonConfig).filter(DaemonConfig.name == name).first()

        if not config:
            console.print(f"[red]Configuration '{name}' not found[/red]")
            return

        # Check if already running
        state = db.query(DaemonState).first()
        if state and state.is_running:
            console.print("[yellow]Daemon is already running![/yellow]")
            console.print(f"PID: {state.pid}")
            console.print("Stop it first: [cyan]job-apply daemon stop[/cyan]")
            return

        config.is_active = True
        db.commit()

        console.print(f"[bold]Starting daemon with configuration: {name}[/bold]")
        console.print(f"Keywords: {config.keywords}")
        console.print(f"Platforms: {config.platforms}")
        console.print(f"Check interval: {config.check_interval_minutes} minutes")
        console.print(f"Max daily applications: {config.max_applications_per_day}")

        if foreground:
            console.print("\n[yellow]Running in foreground (Ctrl+C to stop)...[/yellow]\n")
            # Run in foreground
            from backend.app.automation.daemon import run_daemon
            run_daemon(config.id)
        else:
            # Run in background
            console.print("\n[green]Starting in background...[/green]")

            # Create PID file directory
            pid_dir = settings.data_dir / "daemon"
            pid_dir.mkdir(exist_ok=True)
            pid_file = pid_dir / "daemon.pid"

            # Start daemon as subprocess
            python_exe = sys.executable
            script = f"""
import sys
sys.path.insert(0, '{Path.cwd()}')
from backend.app.automation.daemon import run_daemon
run_daemon({config.id})
"""

            process = subprocess.Popen(
                [python_exe, "-c", script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

            # Save PID
            pid_file.write_text(str(process.pid))

            console.print(f"[green]✅ Daemon started with PID: {process.pid}[/green]")
            console.print(f"\nCheck status: [cyan]job-apply daemon status[/cyan]")
            console.print(f"View logs: [cyan]job-apply daemon logs[/cyan]")
            console.print(f"Stop daemon: [cyan]job-apply daemon stop[/cyan]")

    finally:
        db.close()


@app.command()
def stop():
    """Stop the running daemon."""
    db = SessionLocal()

    try:
        state = db.query(DaemonState).first()

        if not state or not state.is_running:
            console.print("[yellow]Daemon is not running[/yellow]")
            return

        if not state.pid:
            console.print("[red]No PID found for daemon[/red]")
            return

        console.print(f"Stopping daemon (PID: {state.pid})...")

        # Send SIGTERM
        import os
        import signal

        try:
            os.kill(state.pid, signal.SIGTERM)
            console.print("[green]✅ Stop signal sent[/green]")
            console.print("Daemon will shut down gracefully...")

        except ProcessLookupError:
            console.print("[yellow]Process not found (may have already stopped)[/yellow]")
            # Clean up state
            state.is_running = False
            state.pid = None
            db.commit()

    finally:
        db.close()


@app.command()
def status():
    """Show daemon status and statistics."""
    db = SessionLocal()

    try:
        state = db.query(DaemonState).first()

        if not state:
            console.print("[yellow]Daemon has never been started[/yellow]")
            return

        console.print("[bold]Daemon Status:[/bold]\n")

        if state.is_running:
            console.print("Status: [green]RUNNING[/green]")
            console.print(f"PID: {state.pid}")
            console.print(f"Started: {state.started_at.strftime('%Y-%m-%d %H:%M:%S')}")

            # Check heartbeat
            if state.last_heartbeat:
                from datetime import datetime, timedelta

                age = datetime.utcnow() - state.last_heartbeat
                if age < timedelta(minutes=5):
                    console.print(f"Last heartbeat: [green]{age.seconds}s ago[/green]")
                else:
                    console.print(f"Last heartbeat: [red]{age.seconds}s ago (may be stuck)[/red]")
        else:
            console.print("Status: [red]STOPPED[/red]")

        # Active configuration
        if state.active_config_id:
            config = (
                db.query(DaemonConfig)
                .filter(DaemonConfig.id == state.active_config_id)
                .first()
            )
            if config:
                console.print(f"\nActive Configuration: {config.name}")
                console.print(f"Keywords: {config.keywords}")
                console.print(f"Platforms: {config.platforms}")

        # Statistics
        console.print("\n[bold]Statistics:[/bold]")
        console.print(f"Jobs discovered (total): {state.total_jobs_discovered}")
        console.print(f"Applications today: {state.total_applications_today}")

        if state.last_discovery_run:
            console.print(
                f"Last discovery: {state.last_discovery_run.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        # Queue health
        from backend.app.automation.queue_manager import QueueManager

        with QueueManager() as queue_mgr:
            health = queue_mgr.get_queue_health()

            console.print(f"\n[bold]Queue Health: {health['health_status']}[/bold]")
            console.print(f"Queued jobs: {health['total_queued']}")
            console.print(f"Processing: {health['processing']}")
            console.print(f"Completed today: {health['completed_today']}")
            console.print(f"Failed today: {health['failed_today']}")

            if health.get('oldest_age_hours'):
                console.print(f"Oldest queued: {health['oldest_age_hours']:.1f} hours")

    finally:
        db.close()


@app.command()
def logs(
    lines: int = typer.Option(50, help="Number of log lines to show"),
    level: Optional[str] = typer.Option(None, help="Filter by level (INFO, WARNING, ERROR)"),
):
    """View daemon logs."""
    logs = DaemonLogger.get_recent_logs(limit=lines, level=level)

    if not logs:
        console.print("[yellow]No logs found[/yellow]")
        return

    for log in reversed(logs):  # Show oldest first
        timestamp = log["timestamp"][:19]  # Trim milliseconds
        level_style = (
            "green" if log["level"] == "INFO"
            else "yellow" if log["level"] == "WARNING"
            else "red"
        )

        console.print(f"[{level_style}]{timestamp} [{log['level']}][/{level_style}] {log['message']}")

        if log.get("details"):
            console.print(f"  [dim]{log['details']}[/dim]")


@app.command()
def delete(name: str = typer.Argument(..., help="Configuration name")):
    """Delete a daemon configuration."""
    db = SessionLocal()

    try:
        config = db.query(DaemonConfig).filter(DaemonConfig.name == name).first()

        if not config:
            console.print(f"[red]Configuration '{name}' not found[/red]")
            return

        if config.is_active:
            console.print("[red]Cannot delete active configuration[/red]")
            console.print("Stop the daemon first: [cyan]job-apply daemon stop[/cyan]")
            return

        if Confirm.ask(f"Delete configuration '{name}'?"):
            db.delete(config)
            db.commit()
            console.print(f"[green]✅ Deleted configuration '{name}'[/green]")

    finally:
        db.close()
