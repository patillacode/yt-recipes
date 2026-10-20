"""Recipe rendering to Obsidian markdown."""

from datetime import date

from .ai import Recipe
from .utils import sanitize_filename


def _quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render(recipe: Recipe, source: str, created: date | None = None) -> str:
    """Render a recipe as a note with frontmatter, matching the vault's recetas format."""
    today = date.today()
    created = created or today

    ingredientes = "\n".join(
        i if i.startswith("#") else f"- {i}" for i in recipe.ingredientes
    )
    pasos = "\n".join(f"{n}. {p}" for n, p in enumerate(recipe.pasos, 1))
    notas = "\n".join(f"- {n}" for n in recipe.notas) or "- Ninguna"

    out = f"""---
tags: [recetas]
type: recipe
created: {created.isoformat()}
updated: {today.isoformat()}
source: {_quote(source)}
raciones: {_quote(recipe.raciones)}
tiempo_total: {recipe.tiempo_total}
dificultad: {recipe.dificultad}
categoria: [{", ".join(recipe.categoria)}]
electrodomestico: {recipe.electrodomestico}
---

# {recipe.nombre}

## Ingredientes

{ingredientes}

## Pasos

{pasos}

## Notas

{notas}
"""
    if recipe.original:
        out += f"\n## Original\n\n{recipe.original.strip()}\n"
    return out


def filename(title: str) -> str:
    return sanitize_filename(title) + ".md"
