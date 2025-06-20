from typing import Optional

import typer
from rich.console import Console

from ...utils import get_client

console = Console()


def create_run(
    thread_id: str = typer.Argument(..., help="Thread ID to run"),
    assistant_id: str = typer.Option(..., "--assistant-id", "-a", help="Assistant ID to use"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Override assistant's model"),
    instructions: Optional[str] = typer.Option(None, "--instructions", "-i", help="Override assistant's instructions"),
    stream: bool = typer.Option(False, "--stream", "-s", help="Stream the response"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Only output the run ID"),
):
    """Create a run in a thread."""
    client = get_client()
    try:
        if stream and not quiet:
            # Streaming not yet implemented in SDK
            console.print("[yellow]Note: Streaming runs not yet implemented in CLI[/yellow]")

        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            model=model,
            instructions=instructions,
            stream=False,  # Always false for now
        )

        if quiet:
            print(run.id)
        else:
            console.print(f"[green]Created run: {run.id}[/green]")
            console.print(f"Status: {run.status}")
            console.print(f"Assistant: {run.assistant_id}")
            console.print(f"Model: {run.model}")

            # Wait for completion if not streaming
            if not stream:
                console.print("[yellow]Waiting for completion...[/yellow]")
                while run.status in ["queued", "in_progress", "requires_action"]:
                    run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
                    if run.status == "requires_action":
                        console.print("[red]Run requires action (tool calls)[/red]")
                        break

                if run.status == "completed":
                    console.print("[green]Run completed successfully[/green]")
                    # Show the messages
                    messages = client.beta.threads.messages.list(thread_id=thread_id, limit=1, order="desc")
                    if messages.data:
                        latest = messages.data[0]
                        if latest.content:
                            console.print("\n[cyan]Assistant response:[/cyan]")
                            for content in latest.content:
                                if hasattr(content, "text") and hasattr(content.text, "value"):
                                    console.print(content.text.value)
                elif run.status == "failed":
                    console.print(f"[red]Run failed: {run.last_error}[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
