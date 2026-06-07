"""Authentication commands for job platforms."""
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Prompt

from backend.app.automation.browser import BrowserManager, run_async
from backend.app.automation.scrapers.linkedin_scraper import LinkedInScraper
from backend.app.config import settings

app = typer.Typer()
console = Console()


@app.command()
def linkedin():
    """Authenticate with LinkedIn and save session."""
    console.print("[bold]LinkedIn Authentication[/bold]\n")
    console.print("A browser will open where you can log in to LinkedIn.")
    console.print("The session will be saved after you log in successfully.\n")
    console.print("[dim]Note: LinkedIn may require 2FA or verification.[/dim]\n")

    console.print("[yellow]Press Enter to open browser...[/yellow]")
    input()

    async def _auth():
        browser = BrowserManager()
        await browser.start(headless=False)
        await browser.create_context("linkedin")

        page = await browser.new_page()
        await page.goto("https://www.linkedin.com/login")

        console.print("\n[bold]Please log in to LinkedIn in the browser...[/bold]")
        console.print("[dim]Complete any 2FA or verification if prompted.[/dim]")
        console.print("[yellow]Press Enter in terminal after you see your LinkedIn feed...[/yellow]\n")

        input()

        # Verify we're logged in
        try:
            await page.goto("https://www.linkedin.com/feed/", wait_until="networkidle", timeout=10000)
            current_url = page.url
            if "feed" in current_url or "linkedin.com/in/" in current_url:
                # Save session
                await browser.save_session("linkedin")
                await browser.close()
                return True
            else:
                await browser.close()
                return False
        except:
            await browser.close()
            return False

    success = run_async(_auth())

    if success:
        console.print("[bold green]✅ Successfully authenticated with LinkedIn![/bold green]")
        console.print("Session saved. You can now use automated job search and applications.")
    else:
        console.print("[bold red]❌ Authentication failed[/bold red]")
        console.print("Please try again and ensure you complete the login.")


@app.command()
def indeed():
    """Authenticate with Indeed (manual login)."""
    console.print("[bold]Indeed Authentication[/bold]\n")
    console.print("A browser will open where you can log in to Indeed.")
    console.print("The session will be saved after you log in successfully.\n")

    console.print("[yellow]Press Enter to open browser...[/yellow]")
    input()

    async def _auth():
        browser = BrowserManager()
        await browser.start(headless=False)
        await browser.create_context("indeed")

        page = await browser.new_page()
        await page.goto("https://secure.indeed.com/account/login")

        console.print("\n[bold]Please log in to Indeed in the browser...[/bold]")
        console.print("Press Enter in terminal after you've logged in successfully.")

        input()

        # Save session
        await browser.save_session("indeed")
        await browser.close()

    run_async(_auth())

    console.print("[bold green]✅ Session saved![/bold green]")
    console.print("You can now use automated job search and applications.")


@app.command()
def status():
    """Show authentication status for all platforms."""
    console.print("[bold]Authentication Status:[/bold]\n")

    session_dir = settings.data_dir / "browser_sessions"

    # Check LinkedIn session
    linkedin_session = session_dir / "linkedin"
    if linkedin_session.exists():
        console.print("  • LinkedIn: [green]✓ Authenticated[/green]")
    else:
        console.print("  • LinkedIn: [red]✗ Not authenticated[/red]")
        console.print("    Run: [cyan]job-apply auth linkedin[/cyan]")

    # Check Indeed session
    indeed_session = session_dir / "indeed"
    if indeed_session.exists():
        console.print("  • Indeed: [green]✓ Authenticated[/green]")
    else:
        console.print("  • Indeed: [red]✗ Not authenticated[/red]")
        console.print("    Run: [cyan]job-apply auth indeed[/cyan]")


@app.command()
def clear(platform: str = typer.Argument(..., help="Platform to clear (linkedin, indeed, all)")):
    """Clear saved authentication session."""
    session_dir = settings.data_dir / "browser_sessions"

    if platform == "all":
        platforms = ["linkedin", "indeed"]
    else:
        platforms = [platform]

    for p in platforms:
        session_file = session_dir / p
        if session_file.exists():
            session_file.unlink()
            console.print(f"[green]✓ Cleared {p} session[/green]")
        else:
            console.print(f"[yellow]No {p} session found[/yellow]")

    console.print("\nYou'll need to re-authenticate to use automation.")
