"""Profile management commands."""
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from backend.app.database.session import SessionLocal
from backend.app.models import Resume, Skill, UserProfile, WorkHistory

app = typer.Typer()
console = Console()


@app.command()
def create():
    """Create a new user profile interactively."""
    console.print(Panel.fit("📝 Create User Profile", style="bold blue"))

    db = SessionLocal()
    try:
        # Check if profile already exists
        existing = db.query(UserProfile).first()
        if existing:
            if not Confirm.ask(
                "A profile already exists. Do you want to update it?", default=False
            ):
                console.print("[yellow]Profile creation cancelled.[/yellow]")
                return
            profile = existing
        else:
            profile = UserProfile()

        # Collect basic information
        profile.name = Prompt.ask("Full Name")
        profile.email = Prompt.ask("Email")
        profile.phone = Prompt.ask("Phone", default=profile.phone or "")
        profile.location = Prompt.ask("Location", default=profile.location or "")
        profile.linkedin_url = Prompt.ask("LinkedIn URL (optional)", default=profile.linkedin_url or "")
        profile.github_url = Prompt.ask("GitHub URL (optional)", default=profile.github_url or "")

        # Work authorization
        profile.work_authorization = Prompt.ask(
            "Work Authorization (e.g., Citizen, H1B, Green Card)",
            default=profile.work_authorization or "Citizen",
        )
        profile.requires_sponsorship = Confirm.ask(
            "Do you require visa sponsorship?", default=profile.requires_sponsorship
        )

        # Availability
        profile.available_start_date = Prompt.ask(
            "Available start date", default=profile.available_start_date or "2 weeks notice"
        )

        if existing:
            db.commit()
        else:
            db.add(profile)
            db.commit()

        console.print("\n[bold green]✅ Profile created successfully![/bold green]")
        console.print(f"Profile ID: {profile.id}")

    except Exception as e:
        console.print(f"[bold red]❌ Error creating profile: {e}[/bold red]")
        db.rollback()
    finally:
        db.close()


@app.command()
def show():
    """Show current user profile."""
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).first()
        if not profile:
            console.print("[yellow]No profile found. Create one with:[/yellow]")
            console.print("  [cyan]job-apply profile create[/cyan]")
            return

        # Display profile information
        table = Table(title="User Profile", show_header=False)
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        table.add_row("Name", profile.name)
        table.add_row("Email", profile.email)
        if profile.phone:
            table.add_row("Phone", profile.phone)
        if profile.location:
            table.add_row("Location", profile.location)
        if profile.linkedin_url:
            table.add_row("LinkedIn", profile.linkedin_url)
        if profile.github_url:
            table.add_row("GitHub", profile.github_url)

        table.add_row("Work Authorization", profile.work_authorization or "Not specified")
        table.add_row("Requires Sponsorship", "Yes" if profile.requires_sponsorship else "No")
        table.add_row("Available Start", profile.available_start_date or "Not specified")

        console.print(table)

        # Show resume count
        resume_count = db.query(Resume).filter(Resume.user_id == profile.id).count()
        console.print(f"\n📄 Resumes: {resume_count}")

        # Show skills count
        skills_count = db.query(Skill).filter(Skill.user_id == profile.id).count()
        console.print(f"🎯 Skills: {skills_count}")

        # Show work history count
        work_count = db.query(WorkHistory).filter(WorkHistory.user_id == profile.id).count()
        console.print(f"💼 Work History Entries: {work_count}")

    finally:
        db.close()


@app.command()
def add_resume(
    file_path: Path = typer.Argument(..., help="Path to resume file"),
    title: Optional[str] = typer.Option(None, help="Resume title/description"),
    make_default: bool = typer.Option(False, "--default", help="Set as default resume"),
):
    """Add a resume to your profile."""
    if not file_path.exists():
        console.print(f"[bold red]❌ File not found: {file_path}[/bold red]")
        raise typer.Exit(code=1)

    db = SessionLocal()
    try:
        profile = db.query(UserProfile).first()
        if not profile:
            console.print("[yellow]No profile found. Create one first:[/yellow]")
            console.print("  [cyan]job-apply profile create[/cyan]")
            raise typer.Exit(code=1)

        # Copy resume to data directory
        import shutil

        dest_path = settings.resumes_dir / file_path.name
        shutil.copy(file_path, dest_path)

        # Create resume record
        resume = Resume(
            user_id=profile.id,
            file_path=str(dest_path),
            file_name=file_path.name,
            title=title or file_path.stem,
            is_default=make_default,
        )

        # If this is set as default, unset other defaults
        if make_default:
            db.query(Resume).filter(
                Resume.user_id == profile.id, Resume.is_default == True
            ).update({"is_default": False})

        db.add(resume)
        db.commit()

        console.print(
            f"\n[bold green]✅ Resume added successfully![/bold green] ID: {resume.id}"
        )
        console.print(f"File: {dest_path}")

    except Exception as e:
        console.print(f"[bold red]❌ Error adding resume: {e}[/bold red]")
        db.rollback()
    finally:
        db.close()


@app.command()
def add_skill(
    name: str = typer.Argument(..., help="Skill name"),
    category: str = typer.Option("technical", help="Skill category"),
    proficiency: Optional[str] = typer.Option(None, help="Proficiency level"),
):
    """Add a skill to your profile."""
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).first()
        if not profile:
            console.print("[yellow]No profile found. Create one first.[/yellow]")
            raise typer.Exit(code=1)

        skill = Skill(
            user_id=profile.id, name=name, category=category, proficiency=proficiency
        )
        db.add(skill)
        db.commit()

        console.print(f"[bold green]✅ Skill added: {name}[/bold green]")

    except Exception as e:
        console.print(f"[bold red]❌ Error: {e}[/bold red]")
        db.rollback()
    finally:
        db.close()


@app.command()
def list_skills():
    """List all skills in your profile."""
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).first()
        if not profile:
            console.print("[yellow]No profile found.[/yellow]")
            return

        skills = db.query(Skill).filter(Skill.user_id == profile.id).all()
        if not skills:
            console.print("[yellow]No skills found. Add some with:[/yellow]")
            console.print("  [cyan]job-apply profile add-skill Python[/cyan]")
            return

        table = Table(title="Skills")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Category", style="blue")
        table.add_column("Proficiency", style="green")

        for skill in skills:
            table.add_row(
                str(skill.id),
                skill.name,
                skill.category,
                skill.proficiency or "Not specified",
            )

        console.print(table)

    finally:
        db.close()
