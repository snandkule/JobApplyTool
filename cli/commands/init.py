"""Initialize command."""
import typer
from rich.console import Console
from rich.panel import Panel

from backend.app.config import settings
from backend.app.database.session import init_db

console = Console()


@typer.command(name="init")
def init_command():
    """Initialize the application (create directories and database)."""
    console.print(Panel.fit("🚀 Initializing Job Apply Tool", style="bold blue"))

    try:
        # Ensure directories exist
        console.print("📁 Creating directories...")
        settings.ensure_directories()
        console.print("   ✓ Data directories created", style="green")

        # Initialize database
        console.print("🗄️  Initializing database...")
        init_db()
        console.print(f"   ✓ Database created at: {settings.database_url}", style="green")

        console.print("\n[bold green]✅ Initialization complete![/bold green]")
        console.print("\nNext steps:")
        console.print("  1. Create your profile: [cyan]job-apply profile create[/cyan]")
        console.print("  2. Add your resume: [cyan]job-apply profile add-resume resume.pdf[/cyan]")
        console.print(
            "  3. Authenticate with platforms: [cyan]job-apply auth linkedin[/cyan]"
        )

    except Exception as e:
        console.print(f"[bold red]❌ Initialization failed: {e}[/bold red]")
        raise typer.Exit(code=1)
