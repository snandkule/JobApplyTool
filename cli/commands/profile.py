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
from backend.app.config import settings

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

        # Parse resume content
        console.print("[cyan]Parsing resume content...[/cyan]")
        from backend.app.services.resume_parser import parse_resume
        parsed_content = parse_resume(dest_path)

        if parsed_content:
            console.print("[green]✓ Resume parsed successfully[/green]")
        else:
            console.print("[yellow]⚠ Resume parsing failed, but file was saved[/yellow]")

        # Create resume record
        resume = Resume(
            user_id=profile.id,
            file_path=str(dest_path),
            file_name=file_path.name,
            title=title or file_path.stem,
            is_default=make_default,
            parsed_content=parsed_content,
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


@app.command()
def list_resumes():
    """List all resumes in your profile."""
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).first()
        if not profile:
            console.print("[yellow]No profile found.[/yellow]")
            return

        resumes = db.query(Resume).filter(Resume.user_id == profile.id).all()
        if not resumes:
            console.print("[yellow]No resumes found. Add one with:[/yellow]")
            console.print("  [cyan]job-apply profile add-resume ~/resume.pdf[/cyan]")
            return

        table = Table(title="Resumes")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("File Name", style="blue")
        table.add_column("Default", style="green")
        table.add_column("Parsed", style="yellow")

        for resume in resumes:
            table.add_row(
                str(resume.id),
                resume.title or "Untitled",
                resume.file_name,
                "✓" if resume.is_default else "",
                "✓" if resume.parsed_content else "✗",
            )

        console.print(table)

    finally:
        db.close()


@app.command()
def show_resume(
    resume_id: int = typer.Argument(..., help="Resume ID"),
    show_content: bool = typer.Option(False, "--content", help="Show parsed content"),
):
    """Show resume details."""
    db = SessionLocal()
    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            console.print(f"[red]Resume {resume_id} not found.[/red]")
            return

        # Basic info
        table = Table(title=f"Resume #{resume_id}", show_header=False)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Title", resume.title or "Untitled")
        table.add_row("File Name", resume.file_name)
        table.add_row("File Path", resume.file_path)
        table.add_row("Default", "Yes" if resume.is_default else "No")
        table.add_row("Tags", resume.tags or "None")
        table.add_row("Created", resume.created_at.strftime("%Y-%m-%d %H:%M"))

        console.print(table)

        # Parsed content
        if resume.parsed_content:
            console.print("\n[bold green]✓ Resume has been parsed[/bold green]")

            if show_content:
                import json
                parsed = json.loads(resume.parsed_content)

                console.print(f"\n[bold]Word Count:[/bold] {parsed.get('word_count', 0)}")
                console.print(f"[bold]Character Count:[/bold] {parsed.get('char_count', 0)}")

                if parsed.get('emails'):
                    console.print(f"\n[bold]Emails:[/bold] {', '.join(parsed['emails'])}")

                if parsed.get('phones'):
                    console.print(f"\n[bold]Phones:[/bold] {', '.join(parsed['phones'])}")

                if parsed.get('urls'):
                    console.print(f"\n[bold]URLs:[/bold]")
                    for url in parsed['urls']:
                        console.print(f"  • {url}")

                if parsed.get('skills'):
                    console.print(f"\n[bold]Detected Skills:[/bold]")
                    for skill in parsed['skills']:
                        console.print(f"  • {skill}")

                if parsed.get('sections'):
                    console.print(f"\n[bold]Sections Found:[/bold]")
                    for section_name in parsed['sections'].keys():
                        console.print(f"  • {section_name.title()}")

                console.print("\n[dim]Use --content to see full parsed text[/dim]")
        else:
            console.print("\n[yellow]⚠ Resume has not been parsed yet[/yellow]")
            console.print("Re-add the resume to trigger parsing:")
            console.print(f"  [cyan]job-apply profile add-resume {resume.file_path}[/cyan]")

    finally:
        db.close()


@app.command()
def reparse_resume(resume_id: int = typer.Argument(..., help="Resume ID")):
    """Re-parse a resume to extract content."""
    db = SessionLocal()
    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            console.print(f"[red]Resume {resume_id} not found.[/red]")
            return

        console.print(f"[cyan]Parsing resume: {resume.file_name}...[/cyan]")

        from pathlib import Path
        from backend.app.services.resume_parser import parse_resume

        parsed_content = parse_resume(Path(resume.file_path))

        if parsed_content:
            resume.parsed_content = parsed_content
            db.commit()
            console.print("[bold green]✓ Resume parsed successfully![/bold green]")
            console.print("\nUse 'job-apply profile show-resume {} --content' to view".format(resume_id))
        else:
            console.print("[red]✗ Resume parsing failed[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        db.rollback()
    finally:
        db.close()


@app.command()
def build_from_resume(
    resume_id: int = typer.Argument(..., help="Resume ID to build profile from"),
    auto_apply: bool = typer.Option(False, "--yes", "-y", help="Auto-apply all suggestions"),
):
    """Build profile automatically from resume with confirmation."""
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).first()
        if not profile:
            console.print("[red]No profile found. Create one first:[/red]")
            console.print("  [cyan]job-apply profile create[/cyan]")
            raise typer.Exit(code=1)

        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            console.print(f"[red]Resume {resume_id} not found.[/red]")
            raise typer.Exit(code=1)

        if not resume.parsed_content:
            console.print("[yellow]Resume has not been parsed yet. Parsing now...[/yellow]")
            from pathlib import Path
            from backend.app.services.resume_parser import parse_resume

            parsed_content = parse_resume(Path(resume.file_path))
            if parsed_content:
                resume.parsed_content = parsed_content
                db.commit()
                console.print("[green]✓ Resume parsed[/green]")
            else:
                console.print("[red]Failed to parse resume[/red]")
                raise typer.Exit(code=1)

        # Build suggestions
        console.print("\n[cyan]Analyzing resume and building profile suggestions...[/cyan]")
        from backend.app.services.profile_builder import ProfileBuilder

        with ProfileBuilder() as builder:
            suggestions = builder.build_from_resume(resume_id, profile.id)

            # Show suggestions
            has_suggestions = False

            # Profile updates
            if suggestions["profile_updates"]:
                has_suggestions = True
                console.print("\n[bold yellow]Profile Field Updates:[/bold yellow]")
                table = Table(show_header=False)
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="white")

                for field, value in suggestions["profile_updates"].items():
                    current_value = getattr(profile, field, None)
                    if not current_value:
                        table.add_row(field.replace("_", " ").title(), value)

                console.print(table)

            # Skills
            if suggestions["skills_to_add"]:
                has_suggestions = True
                console.print(f"\n[bold yellow]Skills to Add ({len(suggestions['skills_to_add'])}):[/bold yellow]")
                skills_list = [s["name"] for s in suggestions["skills_to_add"]]
                console.print(", ".join(skills_list[:20]))
                if len(skills_list) > 20:
                    console.print(f"... and {len(skills_list) - 20} more")

            # Work history
            if suggestions["work_history_to_add"]:
                has_suggestions = True
                console.print(f"\n[bold yellow]Work History Entries ({len(suggestions['work_history_to_add'])}):[/bold yellow]")
                for work in suggestions["work_history_to_add"][:3]:
                    console.print(f"  • {work.get('title', 'Unknown')} at {work.get('company', 'Unknown')}")

            # Education
            if suggestions["education_to_add"]:
                has_suggestions = True
                console.print(f"\n[bold yellow]Education Entries ({len(suggestions['education_to_add'])}):[/bold yellow]")
                for edu in suggestions["education_to_add"]:
                    console.print(f"  • {edu.get('degree', 'Unknown')}")

            if not has_suggestions:
                console.print("\n[green]✓ No new suggestions. Your profile is already complete![/green]")
                return

            # Confirmation
            if not auto_apply:
                console.print("\n[bold]Apply these suggestions?[/bold]")
                console.print("You can choose:")
                console.print("  [cyan]all[/cyan] - Apply all suggestions")
                console.print("  [cyan]profile[/cyan] - Only update profile fields")
                console.print("  [cyan]skills[/cyan] - Only add skills")
                console.print("  [cyan]work[/cyan] - Only add work history")
                console.print("  [cyan]education[/cyan] - Only add education")
                console.print("  [cyan]none[/cyan] - Cancel")

                choice = Prompt.ask(
                    "Selection",
                    choices=["all", "profile", "skills", "work", "education", "none"],
                    default="all"
                )

                if choice == "none":
                    console.print("[yellow]Cancelled.[/yellow]")
                    return

                selected_fields = None if choice == "all" else [
                    {"profile": "profile", "skills": "skills", "work": "work_history", "education": "education"}[choice]
                ]
            else:
                selected_fields = None

            # Apply suggestions
            console.print("\n[cyan]Applying suggestions...[/cyan]")
            counts = builder.apply_suggestions(profile.id, suggestions, selected_fields)

            # Show results
            console.print("\n[bold green]✓ Profile updated![/bold green]")
            if counts["profile_fields_updated"] > 0:
                console.print(f"  Profile fields: {counts['profile_fields_updated']}")
            if counts["skills_added"] > 0:
                console.print(f"  Skills added: {counts['skills_added']}")
            if counts["work_history_added"] > 0:
                console.print(f"  Work history: {counts['work_history_added']}")
            if counts["education_added"] > 0:
                console.print(f"  Education: {counts['education_added']}")

            console.print("\n[dim]View your profile: job-apply profile show[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        db.rollback()
    finally:
        db.close()
