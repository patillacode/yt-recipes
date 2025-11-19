"""Utility functions and logging setup."""

import logging
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

console = Console()


def setup_logging(verbose: bool = False) -> logging.Logger:
    """
    Setup logging with Rich handler.

    Args:
        verbose: Enable verbose (DEBUG) logging

    Returns:
        Configured logger instance
    """
    level = logging.DEBUG if verbose else logging.INFO

    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console,
                rich_tracebacks=True,
                tracebacks_show_locals=verbose,
                show_path=verbose,
            )
        ],
    )

    logger = logging.getLogger("yt_recipes")
    logger.setLevel(level)

    return logger


def create_progress() -> Progress:
    """
    Create a Rich progress bar with custom columns.

    Returns:
        Configured Progress instance
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    )


def ensure_directory(path: Path) -> None:
    """
    Ensure directory exists, create if it doesn't.

    Args:
        path: Directory path to ensure
    """
    path.mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")

    # Limit length
    if len(filename) > 200:
        filename = filename[:200]

    return filename.strip()


def format_time(seconds: int) -> str:
    """
    Format seconds into human-readable time string.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string (e.g., "1h 30m", "45m", "30s")
    """
    if seconds < 60:
        return f"{seconds}s"

    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes > 0:
        return f"{hours}h {remaining_minutes}m"
    return f"{hours}h"
