"""Main CLI application entry point."""
import typer
from rich.console import Console

from cli.commands import ai, apply, auth, daemon, init, jobs, profile, questions

app = typer.Typer(
    name="job-apply",
    help="AI-powered job application automation tool",
    add_completion=True,
)

# Register command modules
app.add_typer(profile.app, name="profile", help="Manage user profile")
app.add_typer(auth.app, name="auth", help="Manage platform authentication")
app.add_typer(jobs.app, name="jobs", help="Search and manage jobs")
app.add_typer(apply.app, name="apply", help="Apply to jobs")
app.add_typer(daemon.app, name="daemon", help="Manage background daemon")
app.add_typer(questions.app, name="questions", help="Manage Q&A and knowledge base")
app.add_typer(ai.app, name="ai", help="AI-powered features")
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
