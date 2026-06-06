"""Job discovery and management commands."""
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from backend.app.automation.batch_processor import BatchProcessor
from backend.app.automation.browser import BrowserManager, run_async
from backend.app.automation.scrapers.indeed_scraper import IndeedScraper
from backend.app.automation.scrapers.linkedin_scraper import LinkedInScraper
from backend.app.database.session import SessionLocal
from backend.app.models import ApplicationQueue, Job

app = typer.Typer()
console = Console()


@app.command()
def search(
    keywords: str = typer.Argument(..., help="Job title or keywords"),
    location: str = typer.Option("", help="Location (leave empty for remote/all)"),
    platform: str = typer.Option("all", help="Platform: linkedin, indeed, or all"),
    remote: bool = typer.Option(False, help="Remote jobs only"),
    max_results: int = typer.Option(25, help="Maximum results per platform"),
):
    """Search for jobs and save to database."""
    console.print(f"🔍 Searching for: [cyan]{keywords}[/cyan]")

    if location:
        console.print(f"📍 Location: [cyan]{location}[/cyan]")

    if remote:
        console.print("🏠 Remote jobs only")

    async def _search():
        browser = BrowserManager()
        await browser.start(headless=True)

        results = {"linkedin": 0, "indeed": 0}

        try:
            # LinkedIn search
            if platform in ["all", "linkedin"]:
                console.print("\n[bold]Searching LinkedIn...[/bold]")
                linkedin_scraper = LinkedInScraper(browser)
                await browser.create_context("linkedin")

                jobs = await linkedin_scraper.search_jobs(
                    keywords=keywords,
                    location=location,
                    remote=remote,
                    max_results=max_results,
                )

                saved = await linkedin_scraper.save_jobs_to_db(jobs)
                results["linkedin"] = saved
                console.print(f"✓ Found {len(jobs)} jobs, saved {saved} new jobs")

            # Indeed search
            if platform in ["all", "indeed"]:
                console.print("\n[bold]Searching Indeed...[/bold]")
                indeed_scraper = IndeedScraper(browser)
                await browser.create_context("indeed")

                jobs = await indeed_scraper.search_jobs(
                    keywords=keywords,
                    location=location,
                    remote=remote,
                    max_results=max_results,
                )

                saved = await indeed_scraper.save_jobs_to_db(jobs)
                results["indeed"] = saved
                console.print(f"✓ Found {len(jobs)} jobs, saved {saved} new jobs")

        finally:
            await browser.close()

        return results

    results = run_async(_search())

    total = sum(results.values())
    console.print(f"\n[bold green]✅ Total new jobs saved: {total}[/bold green]")
    console.print("\nNext steps:")
    console.print("  • View jobs: [cyan]job-apply jobs list[/cyan]")
    console.print("  • Queue for application: [cyan]job-apply jobs queue <job_id>[/cyan]")


@app.command()
def list(
    status: Optional[str] = typer.Option(None, help="Filter by status"),
    platform: Optional[str] = typer.Option(None, help="Filter by platform"),
    limit: int = typer.Option(20, help="Number of jobs to show"),
):
    """List discovered jobs."""
    db = SessionLocal()

    try:
        query = db.query(Job).order_by(Job.scraped_at.desc())

        if status:
            query = query.filter(Job.status == status)

        if platform:
            query = query.filter(Job.platform == platform)

        jobs = query.limit(limit).all()

        if not jobs:
            console.print("[yellow]No jobs found.[/yellow]")
            return

        table = Table(title=f"Jobs ({len(jobs)} shown)")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Title", style="white")
        table.add_column("Company", style="blue")
        table.add_column("Location", style="green")
        table.add_column("Platform", style="magenta")
        table.add_column("Status", style="yellow")

        for job in jobs:
            table.add_row(
                str(job.id),
                job.title[:40] + "..." if len(job.title) > 40 else job.title,
                job.company[:30] + "..." if len(job.company) > 30 else job.company,
                job.location[:25] + "..." if len(job.location) > 25 else job.location,
                job.platform,
                job.status,
            )

        console.print(table)

    finally:
        db.close()


@app.command()
def view(job_id: int = typer.Argument(..., help="Job ID to view")):
    """View detailed job information."""
    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()

        if not job:
            console.print(f"[bold red]Job {job_id} not found[/bold red]")
            return

        console.print(f"\n[bold]{job.title}[/bold]")
        console.print(f"Company: {job.company}")
        console.print(f"Location: {job.location}")
        console.print(f"Remote: {'Yes' if job.is_remote else 'No'}")
        console.print(f"Platform: {job.platform}")
        console.print(f"Status: {job.status}")
        console.print(f"URL: {job.url}")

        if job.description:
            console.print(f"\n[bold]Description:[/bold]")
            console.print(job.description[:500] + "..." if len(job.description) > 500 else job.description)

        if job.match_score:
            console.print(f"\nMatch Score: {job.match_score:.1%}")

    finally:
        db.close()


@app.command()
def queue(job_id: int = typer.Argument(..., help="Job ID to queue")):
    """Add a job to the application queue."""
    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()

        if not job:
            console.print(f"[bold red]Job {job_id} not found[/bold red]")
            return

        # Check if already queued
        existing = db.query(ApplicationQueue).filter(
            ApplicationQueue.job_id == job_id
        ).first()

        if existing:
            console.print(f"[yellow]Job already in queue (status: {existing.status})[/yellow]")
            return

        # Add to queue
        queue_item = ApplicationQueue(
            job_id=job_id,
            priority=0,
            status="queued",
        )
        db.add(queue_item)
        db.commit()

        console.print(f"[bold green]✅ Job added to queue[/bold green]")
        console.print(f"Title: {job.title}")
        console.print(f"Company: {job.company}")

    finally:
        db.close()


@app.command()
def queue_list():
    """List jobs in application queue."""
    db = SessionLocal()

    try:
        queue_items = (
            db.query(ApplicationQueue)
            .filter(ApplicationQueue.status == "queued")
            .order_by(ApplicationQueue.priority.desc(), ApplicationQueue.added_at)
            .all()
        )

        if not queue_items:
            console.print("[yellow]Queue is empty[/yellow]")
            return

        table = Table(title=f"Application Queue ({len(queue_items)} jobs)")
        table.add_column("Queue ID", style="cyan")
        table.add_column("Job ID", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Company", style="blue")
        table.add_column("Platform", style="magenta")
        table.add_column("Added", style="green")

        for item in queue_items:
            job = db.query(Job).filter(Job.id == item.job_id).first()
            if job:
                table.add_row(
                    str(item.id),
                    str(job.id),
                    job.title[:30] + "..." if len(job.title) > 30 else job.title,
                    job.company[:25] + "..." if len(job.company) > 25 else job.company,
                    job.platform,
                    item.added_at.strftime("%Y-%m-%d"),
                )

        console.print(table)

    finally:
        db.close()
