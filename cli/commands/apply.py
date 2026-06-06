"""Application commands."""
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from backend.app.automation.batch_processor import BatchProcessor
from backend.app.automation.browser import run_async
from backend.app.database.session import SessionLocal
from backend.app.models import Application, UserProfile

app = typer.Typer()
console = Console()


@app.command()
def single(
    job_id: int = typer.Argument(..., help="Job ID to apply to"),
    resume_id: Optional[int] = typer.Option(None, help="Resume ID (uses default if not specified)"),
):
    """Apply to a single job."""
    db = SessionLocal()

    try:
        # Get user profile
        profile = db.query(UserProfile).first()
        if not profile:
            console.print("[bold red]No profile found. Create one first:[/bold red]")
            console.print("  [cyan]job-apply profile create[/cyan]")
            return

        console.print(f"🚀 Applying to job ID: {job_id}")

        async def _apply():
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Automating application...", total=None)

                processor = BatchProcessor()
                result = await processor.apply_to_single_job(
                    job_id=job_id,
                    user_profile_id=profile.id,
                    resume_id=resume_id,
                )

                progress.update(task, completed=True)
                return result

        result = run_async(_apply())

        if result["success"]:
            console.print("[bold green]✅ Application submitted successfully![/bold green]")
            if "message" in result:
                console.print(f"Message: {result['message']}")
        else:
            console.print(f"[bold red]❌ Application failed[/bold red]")
            console.print(f"Error: {result.get('error', 'Unknown error')}")

    finally:
        db.close()


@app.command()
def bulk(
    max_applications: int = typer.Option(10, help="Maximum applications to process"),
    platform: Optional[str] = typer.Option(None, help="Platform filter (linkedin, indeed)"),
):
    """Process application queue in bulk."""
    db = SessionLocal()

    try:
        # Get user profile
        profile = db.query(UserProfile).first()
        if not profile:
            console.print("[bold red]No profile found. Create one first.[/bold red]")
            return

        console.print(f"🚀 Processing up to {max_applications} applications...")

        if platform:
            console.print(f"Platform: {platform}")

        platforms = [platform] if platform else None

        async def _process():
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"Processing applications (0/{max_applications})...",
                    total=max_applications,
                )

                processor = BatchProcessor()
                results = await processor.process_queue(
                    user_profile_id=profile.id,
                    max_applications=max_applications,
                    platforms=platforms,
                )

                progress.update(task, completed=max_applications)
                return results

        results = run_async(_process())

        # Display results
        console.print("\n[bold]Batch Processing Results:[/bold]")
        console.print(f"Total Processed: {results['total_processed']}")
        console.print(f"✅ Successful: [green]{results['successful']}[/green]")
        console.print(f"❌ Failed: [red]{results['failed']}[/red]")
        console.print(f"⏭️  Skipped: [yellow]{results['skipped']}[/yellow]")

        if results["details"]:
            console.print("\n[bold]Details:[/bold]")
            table = Table()
            table.add_column("Job", style="cyan")
            table.add_column("Company", style="blue")
            table.add_column("Platform", style="magenta")
            table.add_column("Status", style="white")

            for detail in results["details"]:
                status_style = (
                    "green" if detail["status"] == "success"
                    else "red" if detail["status"] == "failed"
                    else "yellow"
                )
                table.add_row(
                    detail.get("job_title", f"Job {detail['job_id']}")[:30],
                    detail.get("company", "N/A")[:25],
                    detail.get("platform", "N/A"),
                    f"[{status_style}]{detail['status']}[/{status_style}]",
                )

            console.print(table)

    finally:
        db.close()


@app.command()
def list(
    status: Optional[str] = typer.Option(None, help="Filter by status"),
    limit: int = typer.Option(20, help="Number to show"),
):
    """List applications."""
    db = SessionLocal()

    try:
        query = db.query(Application).order_by(Application.created_at.desc())

        if status:
            query = query.filter(Application.status == status)

        applications = query.limit(limit).all()

        if not applications:
            console.print("[yellow]No applications found.[/yellow]")
            return

        table = Table(title=f"Applications ({len(applications)} shown)")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Job ID", style="cyan", no_wrap=True)
        table.add_column("Platform", style="magenta")
        table.add_column("Status", style="white")
        table.add_column("Submitted", style="green")

        for app in applications:
            submitted = (
                app.submitted_at.strftime("%Y-%m-%d %H:%M")
                if app.submitted_at else "Not submitted"
            )

            status_color = (
                "green" if app.status == "submitted"
                else "red" if app.status == "failed"
                else "yellow"
            )

            table.add_row(
                str(app.id),
                str(app.job_id),
                app.platform,
                f"[{status_color}]{app.status}[/{status_color}]",
                submitted,
            )

        console.print(table)

    finally:
        db.close()


@app.command()
def stats():
    """Show application statistics."""
    db = SessionLocal()

    try:
        total_apps = db.query(Application).count()
        submitted = db.query(Application).filter(Application.status == "submitted").count()
        failed = db.query(Application).filter(Application.status == "failed").count()
        pending = db.query(Application).filter(Application.status.in_(["queued", "processing"])).count()

        console.print("[bold]Application Statistics:[/bold]\n")
        console.print(f"Total Applications: {total_apps}")
        console.print(f"✅ Submitted: [green]{submitted}[/green]")
        console.print(f"❌ Failed: [red]{failed}[/red]")
        console.print(f"⏳ Pending: [yellow]{pending}[/yellow]")

        if total_apps > 0:
            success_rate = (submitted / total_apps) * 100
            console.print(f"\nSuccess Rate: [cyan]{success_rate:.1f}%[/cyan]")

    finally:
        db.close()
