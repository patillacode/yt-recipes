"""Main CLI application using Typer."""

from pathlib import Path

import typer
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from . import __version__
from .ai import Recipe, RecipeExtractor, RecipeExtractorError
from .config import Settings, get_settings
from .formatter import filename, render
from .utils import console, ensure_directory, setup_logging
from .youtube import TranscriptFetcher, VideoIDExtractor, YouTubeError

app = typer.Typer(
    name="yt-recipes",
    help="Extract recipes from YouTube videos and save them to an Obsidian vault",
    add_completion=False,
)


def _load_settings() -> Settings:
    try:
        return get_settings()
    except Exception as exc:
        console.print(f"[red]Error loading settings: {exc}[/red]")
        console.print(
            "[yellow]Make sure .env file exists with all required variables.[/yellow]"
        )
        raise typer.Exit(1) from exc


def _source(video_id: str) -> str:
    return f"https://youtu.be/{video_id}"


def _already_imported(recipes_dir: Path, video_id: str) -> bool:
    """True if a note in recipes_dir already has this video as its source."""
    marker = f'source: "{_source(video_id)}'
    return any(
        marker in path.read_text(encoding="utf-8")[:600]
        for path in recipes_dir.glob("*.md")
    )


def _write_recipes(recipes: list[Recipe], video_id: str, recipes_dir: Path) -> list[Path]:
    """Write one note per recipe. Never overwrites: name clashes get a ' (n)' suffix."""
    ensure_directory(recipes_dir)
    written = []
    for recipe in recipes:
        content = render(recipe, _source(video_id))
        stem = filename(recipe.nombre).removesuffix(".md")
        n = 1
        while True:
            path = recipes_dir / (f"{stem}.md" if n == 1 else f"{stem} ({n}).md")
            try:
                with open(path, "x", encoding="utf-8") as f:
                    f.write(content)
            except FileExistsError:
                n += 1
                continue
            break
        written.append(path)
    return written


def _extract(url: str, settings: Settings, recipes_dir: Path):
    """Fetch and extract. Returns (video_id, recipes), or None if already imported."""
    video_id = VideoIDExtractor.extract(url)
    if recipes_dir.exists() and _already_imported(recipes_dir, video_id):
        console.print(f"[yellow]Skipped: {video_id} is already in {recipes_dir}[/yellow]")
        return None
    with TranscriptFetcher(settings) as fetcher:
        transcript = fetcher.fetch(video_id)
    with RecipeExtractor(settings) as extractor:
        return video_id, extractor.extract(transcript)


@app.command()
def process(
    url: str = typer.Argument(..., help="YouTube video URL"),
    preview: bool = typer.Option(
        False, "--preview", "-p", help="Preview recipes before saving"
    ),
    dir: Path | None = typer.Option(
        None, "--dir", "-d", help="Recipes folder (default: RECIPES_DIR setting)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Process a single YouTube URL and save its recipes to the vault."""
    logger = setup_logging(verbose)
    settings = _load_settings()
    recipes_dir = (dir or settings.recipes_dir).expanduser()

    console.print(
        Panel.fit(
            f"[bold cyan]YouTube Recipes Extractor v{__version__}[/bold cyan]\n"
            f"Saving to: [green]{recipes_dir}[/green]",
            border_style="cyan",
        )
    )

    try:
        console.print("\n[bold]Extracting recipes...[/bold]")
        result = _extract(url, settings, recipes_dir)
        if result is None:
            raise typer.Exit(0)
        video_id, recipes = result

        if not recipes:
            console.print("[yellow]No recipes found in this video.[/yellow]")
            raise typer.Exit(0)
        console.print(f"[green]✓[/green] Found {len(recipes)} recipe(s)")

        if preview:
            _preview_recipes(recipes)
            if not Confirm.ask("\n[bold]Save these recipes?[/bold]", default=True):
                console.print("[yellow]Operation cancelled.[/yellow]")
                raise typer.Exit(0)

        for path in _write_recipes(recipes, video_id, recipes_dir):
            console.print(f"[green]✓[/green] {path.name}")
        console.print("\n[bold green]✓ Done![/bold green]")

    except typer.Exit:
        raise
    except (YouTubeError, RecipeExtractorError) as exc:
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
    dir: Path | None = typer.Option(
        None, "--dir", "-d", help="Recipes folder (default: RECIPES_DIR setting)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Process multiple YouTube URLs from a file."""
    logger = setup_logging(verbose)
    settings = _load_settings()
    recipes_dir = (dir or settings.recipes_dir).expanduser()

    if not file_path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        raise typer.Exit(1)

    with open(file_path) as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not urls:
        console.print(f"[yellow]No URLs found in {file_path}[/yellow]")
        raise typer.Exit(0)

    console.print(
        Panel.fit(
            f"[bold cyan]YouTube Recipes Batch Processor v{__version__}[/bold cyan]\n"
            f"Processing: [green]{len(urls)}[/green] URL(s) -> "
            f"[green]{recipes_dir}[/green]",
            border_style="cyan",
        )
    )

    total_recipes = 0
    failed_urls = []

    for idx, url in enumerate(urls, 1):
        console.print(f"\n[bold cyan]Processing URL {idx}/{len(urls)}:[/bold cyan] {url}")
        try:
            result = _extract(url, settings, recipes_dir)
            if result is None:
                continue
            video_id, recipes = result
            if not recipes:
                console.print("[yellow]  No recipes found[/yellow]")
                continue
            _write_recipes(recipes, video_id, recipes_dir)
            total_recipes += len(recipes)
            console.print(f"[green]  ✓ Saved {len(recipes)} recipe(s)[/green]")
        except Exception as e:
            logger.error(f"Failed to process {url}: {e}")
            console.print(f"[red]  ✗ Failed: {e}[/red]")
            failed_urls.append(url)

    console.print("\n[bold green]Batch processing complete![/bold green]")
    console.print(f"Total recipes saved: [cyan]{total_recipes}[/cyan]")
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
    table.add_column("Nombre", style="green")
    table.add_column("Categoría", style="cyan")
    table.add_column("Aparato", style="magenta")
    table.add_column("Raciones", style="yellow")
    table.add_column("Min", style="magenta")
    table.add_column("Dificultad", style="blue")
    table.add_column("Ingredientes", style="white")

    for recipe in recipes:
        table.add_row(
            recipe.nombre,
            recipe.categoria,
            recipe.electrodomestico,
            recipe.raciones,
            str(recipe.tiempo_total),
            recipe.dificultad,
            str(len(recipe.ingredientes)),
        )

    console.print("\n")
    console.print(table)


if __name__ == "__main__":
    app()
