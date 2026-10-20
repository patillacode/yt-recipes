# YouTube Recipes CLI

Extract recipes from YouTube cooking videos with AI (Groq, Llama 3.3 70B) and save them as notes in an Obsidian vault. Recipes are always written in Spanish.

## Setup

Requires [uv](https://github.com/astral-sh/uv).

```bash
uv sync
cp .env.example .env   # then fill in RAPIDAPI_KEY and GROQ_API_KEY
```

- `RAPIDAPI_KEY`: https://rapidapi.com/h0p3rwe/api/youtube-transcript3
- `GROQ_API_KEY`: https://console.groq.com/
- `RECIPES_DIR` (optional): folder to write notes to. Defaults to `~/syncthing/obsidian/recetas`.

## Usage

```bash
uv run yt-recipes process "https://youtu.be/VIDEO_ID"          # one video
uv run yt-recipes process "URL" --preview                      # confirm before saving
uv run yt-recipes process "URL" --dir ./out                    # write somewhere else
uv run yt-recipes batch urls.txt                               # one URL per line, # comments allowed
```

`just` shortcuts: `just run URL`, `just preview URL`, `just batch FILE`.

Notes are never overwritten:

- A video already present in the folder (matched by the `source` property) is skipped, so re-running is safe.
- A different video with the same recipe title is saved as `Title (2).md`.

## Note format

One file per recipe, `Sentence case title.md`, flat in the recipes folder:

```markdown
---
tags: [recetas]
type: recipe
created: 2026-10-20
updated: 2026-10-20
source: "https://youtu.be/VIDEO_ID"
raciones: "4-6"
tiempo_total: 30          # integer minutes (upper bound of any range)
dificultad: media         # fácil | media | difícil
categoria: pollo          # aperitivo | carne | pollo | pescado | huevos | verduras | pasta | arroz | sandwich | patatas | postre
electrodomestico: air-fryer   # air-fryer | horno | fuego | ninguno
---

# Nuggets caseros

## Ingredientes
## Pasos
## Notas
```

The format is defined in `yt_recipes/formatter.py` (`render`) and the allowed values in `yt_recipes/ai.py`. The model's output is validated against them, so an out-of-list value fails loudly instead of writing a bad note. The vault side (properties, Bases view) is documented in `_meta/vault-guide.md` in the vault.

## Development

```bash
uv run ruff check . && uv run --group test pytest
```

## Project structure

```
yt_recipes/
├── cli.py        # Typer app: process, batch
├── config.py     # Settings (.env)
├── youtube.py    # Video ID extraction & transcripts
├── ai.py         # Recipe model + Groq extraction
├── formatter.py  # Recipe -> Obsidian markdown
└── utils.py
```
