"""Main CLI application entry point."""
import typer
from rich.console import Console

from cli.commands import auth, profile, init

app = typer.Typer(
    name="job-apply",
    help="AI-powered job application automation tool",
    add_completion=True,
)

# Register command modules
app.add_typer(profile.app, name="profile", help="Manage user profile")
app.add_typer(auth.app, name="auth", help="Manage platform authentication")
app.command()(init.init_command)

console = Console()


@app.command()
def version():
    """Show version information."""
    from backend.app.config import settings

    console.print(f"[bold]{settings.app_name}[/bold] v{settings.app_version}")


@app.callback()
def callback():
    """
    Job Apply Tool - Automate your job application process.
    """
    pass


if __name__ == "__main__":
    app()
