from datetime import date

import pytest
from pydantic import ValidationError

from yt_recipes.ai import Recipe
from yt_recipes.formatter import render

SAMPLE = {
    "nombre": "Nuggets caseros",
    "raciones": "4-6",
    "tiempo_total": 30,
    "dificultad": "media",
    "categoria": "pollo",
    "electrodomestico": "air-fryer",
    "ingredientes": ["Filetes de pollo", "Pan rallado"],
    "pasos": ["Cortar el pollo", "Empanar"],
    "notas": ["Ajustar al gusto"],
}


def test_render():
    out = render(Recipe(**SAMPLE), "https://youtu.be/abc", date(2025, 10, 7))
    keys = [line.split(":")[0] for line in out.split("---")[1].strip().splitlines()]
    assert keys == [
        "tags", "type", "created", "updated", "source", "raciones",
        "tiempo_total", "dificultad", "categoria", "electrodomestico",
    ]  # fmt: skip
    assert "created: 2025-10-07" in out
    assert "tiempo_total: 30\n" in out
    for h in ("# Nuggets caseros", "## Ingredientes", "## Pasos", "## Notas"):
        assert h in out
    assert "## Original" not in out
    assert "2. Empanar" in out


def test_original_section():
    out = render(Recipe(**SAMPLE, original="texto crudo"), "docmost")
    assert out.rstrip().endswith("## Original\n\ntexto crudo")


@pytest.mark.parametrize(
    "field,value",
    [
        ("categoria", "sopa"),
        ("dificultad", "muy fácil"),
        ("electrodomestico", "microondas"),
    ],
)
def test_bad_enum_raises(field, value):
    with pytest.raises(ValidationError):
        Recipe(**{**SAMPLE, field: value})
