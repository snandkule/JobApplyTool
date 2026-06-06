"""Q&A system commands for managing pending questions."""
import json
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from backend.app.database.session import SessionLocal
from backend.app.models import Job, PendingQuestion
from backend.app.services.knowledge_base import KnowledgeBaseService
from backend.app.services.question_service import QuestionService

app = typer.Typer()
console = Console()


@app.command()
def list(
    status: str = typer.Option("pending", help="Filter by status"),
    limit: int = typer.Option(50, help="Number to show"),
):
    """List pending questions."""
    with QuestionService() as qs:
        questions = qs.get_pending_questions(status=status)[:limit]

        if not questions:
            console.print(f"[yellow]No {status} questions found.[/yellow]")
            if status == "pending":
                console.print("\nAll questions have been answered! 🎉")
            return

        table = Table(title=f"{status.title()} Questions ({len(questions)})")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Job", style="blue")
        table.add_column("Question", style="white")
        table.add_column("Type", style="magenta")
        table.add_column("Created", style="green")

        db = SessionLocal()
        try:
            for q in questions:
                job = db.query(Job).filter(Job.id == q.job_id).first()
                job_desc = f"{job.company} - {job.title[:30]}" if job else f"Job {q.job_id}"

                table.add_row(
                    str(q.id),
                    job_desc,
                    q.question_text[:50] + "..." if len(q.question_text) > 50 else q.question_text,
                    q.field_type,
                    q.created_at.strftime("%m/%d %H:%M"),
                )

            console.print(table)

            if status == "pending":
                console.print(f"\nAnswer questions: [cyan]job-apply questions batch-answer[/cyan]")

        finally:
            db.close()


@app.command()
def answer(
    question_id: int = typer.Argument(..., help="Question ID"),
    response: str = typer.Option(..., help="Your answer"),
    save: bool = typer.Option(True, help="Save to knowledge base"),
    policy: str = typer.Option("always_same", help="Reuse policy"),
):
    """Answer a single question."""
    with QuestionService() as qs:
        try:
            question = qs.answer_question(
                question_id=question_id,
                answer=response,
                save_to_kb=save,
                reuse_policy=policy,
            )

            console.print(f"[green]✅ Question {question_id} answered[/green]")
            console.print(f"Answer saved: {response}")

            if save:
                console.print("[dim]Answer added to knowledge base for future reuse[/dim]")

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


@app.command()
def batch_answer():
    """Answer all pending questions interactively."""
    with QuestionService() as qs:
        questions = qs.get_pending_questions(status="pending")

        if not questions:
            console.print("[green]No pending questions! All caught up.[/green]")
            return

        console.print(f"[bold]Found {len(questions)} pending questions[/bold]\n")

        answers = {}
        for i, question in enumerate(questions, 1):
            console.print(f"[bold cyan]Question {i}/{len(questions)}:[/bold cyan]")
            console.print(f"  {question.question_text}")
            console.print(f"  [dim]Type: {question.field_type}[/dim]\n")

            # Get answer
            if question.field_type == "yes_no":
                answer = Prompt.ask("  Answer", choices=["yes", "no", "skip"])
            else:
                answer = Prompt.ask("  Answer (or 'skip')")

            if answer.lower() == "skip":
                qs.skip_question(question.id)
                console.print("  [yellow]Skipped[/yellow]\n")
                continue

            answers[question.id] = answer
            console.print("  [green]✓[/green]\n")

        if not answers:
            console.print("[yellow]All questions skipped[/yellow]")
            return

        # Ask about saving to KB
        save_to_kb = Confirm.ask("\nSave answers to knowledge base for future reuse?", default=True)
        policy = "always_same"

        if save_to_kb:
            policy = Prompt.ask(
                "Reuse policy",
                choices=["always_same", "context_dependent", "always_ask"],
                default="always_same",
            )

        # Save answers
        count = qs.batch_answer_questions(answers, save_to_kb=save_to_kb, reuse_policy=policy)

        console.print(f"\n[bold green]✅ Answered {count} questions![/bold green]")

        if save_to_kb:
            console.print("[dim]Answers saved to knowledge base[/dim]")

        # Check if any applications are ready to resume
        ready = qs.check_applications_ready_to_resume()
        if ready:
            console.print(f"\n[cyan]{len(ready)} applications ready to resume[/cyan]")
            console.print("Resume them: [cyan]job-apply questions resume-paused[/cyan]")


@app.command()
def resume_paused():
    """Resume applications that were paused for questions."""
    from backend.app.automation.batch_processor import BatchProcessor
    from backend.app.automation.browser import run_async
    from backend.app.models import UserProfile

    with QuestionService() as qs:
        ready_app_ids = qs.check_applications_ready_to_resume()

        if not ready_app_ids:
            console.print("[yellow]No applications ready to resume[/yellow]")
            console.print("Answer pending questions first: [cyan]job-apply questions batch-answer[/cyan]")
            return

        console.print(f"[bold]Found {len(ready_app_ids)} applications ready to resume[/bold]\n")

        if not Confirm.ask(f"Resume {len(ready_app_ids)} applications?"):
            return

        # Get user profile
        db = SessionLocal()
        profile = db.query(UserProfile).first()
        db.close()

        if not profile:
            console.print("[red]No profile found[/red]")
            return

        console.print("Resuming applications...\n")

        async def _resume():
            processor = BatchProcessor()
            results = {"success": 0, "failed": 0}

            for app_id in ready_app_ids:
                # Get answered questions
                answered = qs.get_answered_questions_for_application(app_id)

                # TODO: Resume application with answers
                # This requires modifying applicators to accept pre-filled answers
                console.print(f"[dim]Application {app_id}: {len(answered)} answers ready[/dim]")

            return results

        results = run_async(_resume())

        console.print(f"\n[green]✅ Resumed {results['success']} applications[/green]")
        if results['failed'] > 0:
            console.print(f"[red]Failed: {results['failed']}[/red]")


@app.command()
def stats():
    """Show question statistics."""
    with QuestionService() as qs:
        stats = qs.get_question_statistics()

        console.print("[bold]Question Statistics:[/bold]\n")
        console.print(f"Pending: [yellow]{stats['total_pending']}[/yellow]")
        console.print(f"Answered: [green]{stats['total_answered']}[/green]")
        console.print(f"Skipped: [red]{stats['total_skipped']}[/red]")
        console.print(f"Answer Rate: [cyan]{stats['answer_rate']}%[/cyan]")

        if stats['common_questions']:
            console.print("\n[bold]Most Common Questions:[/bold]")
            for i, q in enumerate(stats['common_questions'], 1):
                console.print(f"{i}. {q['question']} ({q['count']}x)")


@app.command()
def kb_list():
    """List knowledge base entries."""
    with KnowledgeBaseService() as kb:
        entries = kb.get_all_entries()

        if not entries:
            console.print("[yellow]Knowledge base is empty[/yellow]")
            return

        table = Table(title=f"Knowledge Base ({len(entries)} entries)")
        table.add_column("ID", style="cyan")
        table.add_column("Question", style="white")
        table.add_column("Answer", style="green")
        table.add_column("Policy", style="magenta")
        table.add_column("Used", style="blue")

        for entry in entries[:50]:  # Show top 50
            table.add_row(
                str(entry.id),
                entry.question_normalized[:40],
                (entry.answer or "")[:30],
                entry.reuse_policy,
                f"{entry.usage_count}x",
            )

        console.print(table)


@app.command()
def kb_export(
    output: str = typer.Argument("knowledge_base.json", help="Output file"),
):
    """Export knowledge base to JSON."""
    with KnowledgeBaseService() as kb:
        data = kb.export_knowledge_base()

        with open(output, "w") as f:
            json.dump(data, f, indent=2)

        console.print(f"[green]✅ Exported {data['count']} entries to {output}[/green]")


@app.command()
def kb_import(
    input_file: str = typer.Argument(..., help="JSON file to import"),
):
    """Import knowledge base from JSON."""
    try:
        with open(input_file) as f:
            data = json.load(f)

        with KnowledgeBaseService() as kb:
            kb.import_knowledge_base(data)

        console.print(f"[green]✅ Imported {len(data.get('entries', []))} entries[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
