"""Main CLI application using Typer."""

from pathlib import Path

import typer
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from . import __version__
from .ai import Recipe, RecipeExtractor, RecipeExtractorError
from .config import Settings, get_settings
from .docmost import DocmostClient, DocmostError
from .formatter import RecipeFormatter
from .utils import console, ensure_directory, sanitize_filename, setup_logging
from .youtube import TranscriptFetcher, VideoIDExtractor, YouTubeError

app = typer.Typer(
    name="yt-recipes",
    help="Extract recipes from YouTube videos and upload to Docmost",
    add_completion=False,
)


@app.command()
def process(
    url: str = typer.Argument(..., help="YouTube video URL"),
    language: str | None = typer.Option(
        None, "--language", "-l", help="Target language code (es, en, fr, de, it, pt)"
    ),
    preview: bool = typer.Option(
        False, "--preview", "-p", help="Preview recipes before uploading"
    ),
    export_dir: Path | None = typer.Option(
        None, "--export-dir", "-e", help="Export recipes to local directory"
    ),
    no_upload: bool = typer.Option(
        False, "--no-upload", help="Skip uploading to Docmost (only export locally)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Process a single YouTube URL and extract recipes."""
    logger = setup_logging(verbose)

    try:
        settings = get_settings()
    except Exception as exc:
        console.print(f"[red]Error loading settings: {exc}[/red]")
        console.print(
            "[yellow]Make sure .env file exists with all required variables.[/yellow]"
        )
        raise typer.Exit(1) from exc

    # Use settings defaults if not provided
    target_language = language or settings.default_language
    export_path = export_dir or (settings.export_dir if export_dir is not None else None)

    console.print(
        Panel.fit(
            f"[bold cyan]YouTube Recipes Extractor v{__version__}[/bold cyan]\n"
            f"Target Language: [green]{target_language}[/green]",
            border_style="cyan",
        )
    )

    try:
        # Step 1: Extract video ID
        console.print("\n[bold]Step 1:[/bold] Extracting video ID...")
        video_id = VideoIDExtractor.extract(url)
        console.print(f"[green]✓[/green] Video ID: [cyan]{video_id}[/cyan]")

        # Step 2: Fetch transcript
        console.print("\n[bold]Step 2:[/bold] Fetching transcript...")
        with TranscriptFetcher(settings) as fetcher:
            transcript = fetcher.fetch(video_id)
        console.print(
            f"[green]✓[/green] Transcript fetched ({len(transcript)} characters)"
        )

        # Step 3: Extract recipes
        console.print(
            f"\n[bold]Step 3:[/bold] Extracting recipes (language: {target_language})..."
        )
        with RecipeExtractor(settings) as extractor:
            recipes = extractor.extract(transcript, target_language)

        if not recipes:
            console.print("[yellow]No recipes found in this video.[/yellow]")
            raise typer.Exit(0)

        console.print(f"[green]✓[/green] Found {len(recipes)} recipe(s)")

        # Step 4: Format recipes
        console.print("\n[bold]Step 4:[/bold] Formatting recipes...")
        formatted_recipes = RecipeFormatter.format_batch(recipes, video_id, url)
        console.print(f"[green]✓[/green] Formatted {len(formatted_recipes)} recipe(s)")

        # Step 5: Preview (if requested)
        if preview:
            _preview_recipes(recipes)
            if not Confirm.ask(
                "\n[bold]Proceed with upload/export?[/bold]", default=True
            ):
                console.print("[yellow]Operation cancelled.[/yellow]")
                raise typer.Exit(0)

        # Step 6: Export to local files (if requested)
        if export_path:
            console.print(f"\n[bold]Step 5:[/bold] Exporting to {export_path}...")
            _export_recipes(formatted_recipes, export_path)
            console.print(f"[green]✓[/green] Exported {len(formatted_recipes)} recipe(s)")

        # Step 7: Upload to Docmost (unless disabled)
        if not no_upload:
            console.print("\n[bold]Step 6:[/bold] Uploading to Docmost...")
            _upload_recipes(formatted_recipes, settings)
            console.print(f"[green]✓[/green] Uploaded {len(formatted_recipes)} recipe(s)")

        console.print("\n[bold green]✓ Done![/bold green]")

    except (YouTubeError, RecipeExtractorError, DocmostError) as exc:
        console.print(f"\n[red]Error: {exc}[/red]")
        raise typer.Exit(1) from exc
    except KeyboardInterrupt as exc:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        raise typer.Exit(0) from exc
    except Exception as exc:
        logger.exception("Unexpected error")
        console.print(f"\n[red]Unexpected error: {exc}[/red]")
        raise typer.Exit(1) from exc


@app.command()
def batch(
    file_path: Path = typer.Argument(
        ..., help="File containing YouTube URLs (one per line)"
    ),
    language: str | None = typer.Option(
        None, "--language", "-l", help="Target language code (es, en, fr, de, it, pt)"
    ),
    preview: bool = typer.Option(
        False, "--preview", "-p", help="Preview recipes before uploading"
    ),
    export_dir: Path | None = typer.Option(
        None, "--export-dir", "-e", help="Export recipes to local directory"
    ),
    no_upload: bool = typer.Option(
        False, "--no-upload", help="Skip uploading to Docmost (only export locally)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Process multiple YouTube URLs from a file."""
    logger = setup_logging(verbose)

    try:
        settings = get_settings()
    except Exception as exc:
        console.print(f"[red]Error loading settings: {exc}[/red]")
        console.print(
            "[yellow]Make sure .env file exists with all required variables.[/yellow]"
        )
        raise typer.Exit(1) from exc

    # Read URLs from file
    if not file_path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        raise typer.Exit(1)

    urls = []
    with open(file_path) as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not urls:
        console.print(f"[yellow]No URLs found in {file_path}[/yellow]")
        raise typer.Exit(0)

    console.print(
        Panel.fit(
            f"[bold cyan]YouTube Recipes Batch Processor v{__version__}[/bold cyan]\n"
            f"Processing: [green]{len(urls)}[/green] URL(s)",
            border_style="cyan",
        )
    )

    target_language = language or settings.default_language
    export_path = export_dir or (settings.export_dir if export_dir is not None else None)

    total_recipes = 0
    failed_urls = []

    for idx, url in enumerate(urls, 1):
        console.print(f"\n[bold cyan]Processing URL {idx}/{len(urls)}:[/bold cyan] {url}")

        try:
            # Extract, fetch, and process
            video_id = VideoIDExtractor.extract(url)

            with TranscriptFetcher(settings) as fetcher:
                transcript = fetcher.fetch(video_id)

            with RecipeExtractor(settings) as extractor:
                recipes = extractor.extract(transcript, target_language)

            if not recipes:
                console.print("[yellow]  No recipes found[/yellow]")
                continue

            formatted_recipes = RecipeFormatter.format_batch(recipes, video_id, url)

            # Export if requested
            if export_path:
                _export_recipes(formatted_recipes, export_path)

            # Upload if not disabled
            if not no_upload:
                _upload_recipes(formatted_recipes, settings)

            total_recipes += len(recipes)
            console.print(f"[green]  ✓ Processed {len(recipes)} recipe(s)[/green]")

        except Exception as e:
            logger.error(f"Failed to process {url}: {e}")
            console.print(f"[red]  ✗ Failed: {e}[/red]")
            failed_urls.append(url)

    # Summary
    console.print("\n[bold green]Batch processing complete![/bold green]")
    console.print(f"Total recipes processed: [cyan]{total_recipes}[/cyan]")

    if failed_urls:
        console.print(f"\n[yellow]Failed URLs ({len(failed_urls)}):[/yellow]")
        for url in failed_urls:
            console.print(f"  - {url}")


@app.command()
def version():
    """Show version information."""
    console.print(
        f"[bold cyan]yt-recipes[/bold cyan] version [green]{__version__}[/green]"
    )


def _preview_recipes(recipes: list[Recipe]) -> None:
    """Display recipe preview in a table."""
    table = Table(title="Extracted Recipes", show_header=True, header_style="bold cyan")
    table.add_column("Icon", style="cyan", width=6)
    table.add_column("Name", style="green")
    table.add_column("Servings", style="yellow")
    table.add_column("Time", style="magenta")
    table.add_column("Difficulty", style="blue")
    table.add_column("Ingredients", style="white")

    for recipe in recipes:
        table.add_row(
            recipe.icon,
            recipe.name,
            recipe.servings,
            recipe.total_time,
            recipe.difficulty,
            str(len(recipe.ingredients)),
        )

    console.print("\n")
    console.print(table)


def _export_recipes(formatted_recipes: list[dict], export_dir: Path) -> None:
    """Export recipes to local markdown files."""
    ensure_directory(export_dir)

    for recipe_data in formatted_recipes:
        filename = sanitize_filename(recipe_data["title"]) + ".md"
        file_path = export_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(recipe_data["content"])


def _upload_recipes(formatted_recipes: list[dict], settings: Settings) -> None:
    """Upload recipes to Docmost."""
    with DocmostClient(settings) as client:
        client.login()

        for recipe_data in formatted_recipes:
            client.upload_recipe(
                title=recipe_data["title"],
                content=recipe_data["content"],
                icon=recipe_data["icon"],
            )


if __name__ == "__main__":
    app()
