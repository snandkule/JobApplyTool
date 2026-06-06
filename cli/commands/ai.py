"""AI-powered commands for job applications."""
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from backend.app.ai.ai_service import AIService
from backend.app.database.session import SessionLocal
from backend.app.models import Application, Job, UserProfile

app = typer.Typer()
console = Console()


@app.command()
def generate_cover_letter(
    job_id: int = typer.Argument(..., help="Job ID"),
    user_id: int = typer.Option(1, help="User profile ID"),
    max_words: int = typer.Option(400, help="Maximum word count"),
    save: bool = typer.Option(True, help="Save to database"),
):
    """Generate AI cover letter for a job."""
    console.print(f"[cyan]Generating cover letter for job {job_id}...[/cyan]")

    try:
        ai = AIService()
        cover_letter = ai.generate_cover_letter(
            job_id=job_id,
            user_profile_id=user_id,
            max_words=max_words,
        )

        # Display cover letter
        console.print("\n")
        console.print(
            Panel(
                cover_letter,
                title=f"[bold green]Generated Cover Letter (Job {job_id})[/bold green]",
                border_style="green",
            )
        )

        if save:
            # Save to database
            db = SessionLocal()
            try:
                job = db.query(Job).filter(Job.id == job_id).first()
                if job:
                    # Create or update application
                    app_record = (
                        db.query(Application)
                        .filter(
                            Application.job_id == job_id,
                            Application.user_id == user_id,
                        )
                        .first()
                    )

                    if not app_record:
                        app_record = Application(
                            job_id=job_id,
                            user_id=user_id,
                            status="draft",
                        )
                        db.add(app_record)

                    app_record.cover_letter_text = cover_letter
                    db.commit()

                    console.print(
                        f"\n[green]✅ Cover letter saved to application record[/green]"
                    )
            finally:
                db.close()

        console.print(
            f"\n[dim]Word count: ~{len(cover_letter.split())} words[/dim]"
        )

    except Exception as e:
        console.print(f"[red]Error generating cover letter: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def match_score(
    job_id: int = typer.Argument(..., help="Job ID"),
    user_id: int = typer.Option(1, help="User profile ID"),
):
    """Calculate AI-powered job match score."""
    console.print(f"[cyan]Analyzing job match for job {job_id}...[/cyan]")

    try:
        ai = AIService()
        result = ai.calculate_job_match(
            job_id=job_id,
            user_profile_id=user_id,
        )

        # Display results
        score = result.get("match_score", 0)
        score_pct = int(score * 100)

        # Color based on score
        if score >= 0.8:
            score_color = "green"
            recommendation = "🎯 Strong Match"
        elif score >= 0.6:
            score_color = "yellow"
            recommendation = "⚠️ Moderate Match"
        else:
            score_color = "red"
            recommendation = "❌ Weak Match"

        console.print(
            f"\n[bold {score_color}]Match Score: {score_pct}%[/bold {score_color}]"
        )
        console.print(f"{recommendation}")
        console.print(f"\nRecommendation: [{score_color}]{result.get('recommendation', 'N/A').upper()}[/{score_color}]")

        if "reasoning" in result:
            console.print(f"\n[bold]Reasoning:[/bold]")
            console.print(result["reasoning"])

        if result.get("matching_skills"):
            console.print(f"\n[bold green]Matching Skills:[/bold green]")
            for skill in result["matching_skills"]:
                console.print(f"  ✓ {skill}")

        if result.get("missing_skills"):
            console.print(f"\n[bold red]Missing Skills:[/bold red]")
            for skill in result["missing_skills"]:
                console.print(f"  ✗ {skill}")

        # Update job with match score
        db = SessionLocal()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.match_score = score
                db.commit()
                console.print(f"\n[dim]Match score saved to job record[/dim]")
        finally:
            db.close()

    except Exception as e:
        console.print(f"[red]Error calculating match score: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def suggest_answer(
    question: str = typer.Argument(..., help="Question text"),
    job_id: Optional[int] = typer.Option(None, help="Job ID for context"),
    user_id: int = typer.Option(1, help="User profile ID"),
    field_type: str = typer.Option("text", help="Field type"),
):
    """Get AI suggestion for application question."""
    console.print(f"[cyan]Generating answer suggestion...[/cyan]")

    try:
        ai = AIService()
        answer = ai.suggest_answer(
            question_text=question,
            job_id=job_id,
            user_profile_id=user_id,
            field_type=field_type,
        )

        console.print("\n")
        console.print(
            Panel(
                answer,
                title=f"[bold green]Suggested Answer[/bold green]",
                subtitle=f"[dim]Question: {question}[/dim]",
                border_style="green",
            )
        )

        console.print(
            f"\n[yellow]Review and edit before using in application[/yellow]"
        )

    except Exception as e:
        console.print(f"[red]Error generating answer: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def batch_suggest(
    user_id: int = typer.Option(1, help="User profile ID"),
    status: str = typer.Option("pending", help="Question status"),
):
    """Get AI suggestions for all pending questions."""
    from backend.app.models import PendingQuestion

    console.print(
        f"[cyan]Generating suggestions for {status} questions...[/cyan]"
    )

    db = SessionLocal()
    try:
        # Get pending questions
        questions = (
            db.query(PendingQuestion)
            .filter(PendingQuestion.status == status)
            .all()
        )

        if not questions:
            console.print(f"[yellow]No {status} questions found[/yellow]")
            return

        console.print(f"Found {len(questions)} questions\n")

        # Generate suggestions
        ai = AIService()
        question_tuples = [
            (q.id, q.question_text, q.field_type) for q in questions
        ]

        suggestions = ai.batch_suggest_answers(
            questions=question_tuples,
            user_profile_id=user_id,
        )

        # Display results
        for question in questions:
            suggestion = suggestions.get(question.id)

            if suggestion:
                console.print(f"[bold cyan]Q{question.id}:[/bold cyan] {question.question_text}")
                console.print(f"[green]→ {suggestion}[/green]\n")
            else:
                console.print(f"[bold cyan]Q{question.id}:[/bold cyan] {question.question_text}")
                console.print(f"[red]→ Failed to generate suggestion[/red]\n")

        console.print(
            f"\n[yellow]Review suggestions with: job-apply questions list[/yellow]"
        )

    finally:
        db.close()


@app.command()
def analyze_resume(
    job_id: int = typer.Argument(..., help="Job ID"),
    user_id: int = typer.Option(1, help="User profile ID"),
):
    """Analyze which resume to use for a job."""
    console.print(f"[cyan]Analyzing resumes for job {job_id}...[/cyan]")

    try:
        ai = AIService()
        result = ai.analyze_resume_for_job(
            job_id=job_id,
            user_profile_id=user_id,
        )

        console.print("\n")

        if result.get("recommended_resume_id"):
            console.print(
                f"[bold green]Recommended Resume: ID {result['recommended_resume_id']}[/bold green]"
            )

            if "reasoning" in result:
                console.print(f"\n[bold]Why:[/bold]")
                console.print(result["reasoning"])

        else:
            console.print("[red]No resume recommendations available[/red]")

        if result.get("suggestions"):
            console.print(f"\n[bold yellow]Suggestions:[/bold yellow]")
            for i, suggestion in enumerate(result["suggestions"], 1):
                console.print(f"{i}. {suggestion}")

    except Exception as e:
        console.print(f"[red]Error analyzing resume: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def bulk_cover_letters(
    user_id: int = typer.Option(1, help="User profile ID"),
    status: str = typer.Option("queued", help="Job status to process"),
    limit: int = typer.Option(10, help="Max jobs to process"),
):
    """Generate cover letters for multiple jobs."""
    console.print(
        f"[cyan]Generating cover letters for {status} jobs...[/cyan]"
    )

    db = SessionLocal()
    try:
        # Get jobs
        jobs = (
            db.query(Job)
            .filter(Job.status == status)
            .limit(limit)
            .all()
        )

        if not jobs:
            console.print(f"[yellow]No {status} jobs found[/yellow]")
            return

        console.print(f"Processing {len(jobs)} jobs...\n")

        ai = AIService()
        success = 0
        failed = 0

        for job in jobs:
            try:
                console.print(f"[dim]{job.company} - {job.title}...[/dim]", end=" ")

                cover_letter = ai.generate_cover_letter(
                    job_id=job.id,
                    user_profile_id=user_id,
                )

                # Save to application
                app_record = (
                    db.query(Application)
                    .filter(
                        Application.job_id == job.id,
                        Application.user_id == user_id,
                    )
                    .first()
                )

                if not app_record:
                    app_record = Application(
                        job_id=job.id,
                        user_id=user_id,
                        status="draft",
                    )
                    db.add(app_record)

                app_record.cover_letter_text = cover_letter
                db.commit()

                console.print("[green]✓[/green]")
                success += 1

            except Exception as e:
                console.print(f"[red]✗ {str(e)}[/red]")
                failed += 1

        console.print(f"\n[bold]Results:[/bold]")
        console.print(f"Success: [green]{success}[/green]")
        if failed > 0:
            console.print(f"Failed: [red]{failed}[/red]")

    finally:
        db.close()
