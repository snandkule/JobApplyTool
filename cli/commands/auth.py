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
        import asyncio  # Import at function level
        browser = BrowserManager()
        await browser.start(headless=False)
        await browser.create_context("linkedin")

        page = await browser.new_page()
        await page.goto("https://www.linkedin.com/login")

        console.print("\n[bold cyan]IMPORTANT: Follow these steps:[/bold cyan]")
        console.print("1. Log in to LinkedIn in the browser")
        console.print("2. Complete any 2FA or verification")
        console.print("3. [bold]WAIT until you see your LinkedIn feed[/bold]")
        console.print("   (The URL should change to: https://www.linkedin.com/feed/)")
        console.print("4. [bold yellow]Only then press Enter in this terminal[/bold yellow]\n")

        console.print("[yellow]Waiting for you to complete login...[/yellow]")
        input("\nPress Enter ONLY after you see the feed: ")

        # Verify we're logged in by checking current URL
        try:
            # Give the page a moment to settle after user presses Enter
            console.print(f"\n[dim]Checking authentication...[/dim]")
            await asyncio.sleep(2)

            # Wait for navigation to complete
            try:
                await page.wait_for_load_state("networkidle", timeout=5000)
            except:
                pass  # Continue even if this times out

            current_url = page.url
            console.print(f"[dim]Current URL: {current_url}[/dim]")

            # Check if we're on the feed or another logged-in page
            if "feed" in current_url:
                console.print("[green]✓ Detected LinkedIn feed[/green]")
            elif "linkedin.com" in current_url and "login" not in current_url:
                console.print("[yellow]⚠ On LinkedIn but not on feed, attempting to navigate...[/yellow]")
            else:
                console.print(f"[red]✗ Still on login page. You must complete the login first.[/red]")
                console.print(f"[red]Current URL: {current_url}[/red]")
                console.print("\n[yellow]Tips:[/yellow]")
                console.print("• Enter your email and password")
                console.print("• Click 'Sign in'")
                console.print("• Complete any verification")
                console.print("• WAIT for the feed to load")
                console.print("• Then run: job-apply auth linkedin again")
                await browser.close()
                return False

            # We're logged in, try to ensure we're on feed
            if "feed" not in current_url:
                try:
                    await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=15000)
                    console.print("[green]✓ Navigated to feed[/green]")
                except Exception as nav_error:
                    console.print(f"[yellow]Navigation issue (but will save session): {nav_error}[/yellow]")

            # Save session
            console.print("[cyan]Saving LinkedIn session...[/cyan]")
            await browser.save_session("linkedin")
            console.print("[green]✓ Session saved successfully![/green]")
            await browser.close()
            return True
        except Exception as e:
            console.print(f"[red]Error during verification: {e}[/red]")
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
