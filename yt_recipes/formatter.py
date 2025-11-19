"""Recipe formatting to markdown."""

from typing import List

from .ai import Recipe


class RecipeFormatter:
    """Format recipes as markdown documents."""

    @staticmethod
    def format(recipe: Recipe, video_id: str, youtube_url: str = None) -> str:
        """
        Format a recipe as markdown.

        Args:
            recipe: Recipe object to format
            video_id: YouTube video ID
            youtube_url: Full YouTube URL (optional, will be constructed if not provided)

        Returns:
            Formatted markdown string
        """
        if youtube_url is None:
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"

        # Build ingredients list
        ingredients_md = "\n".join(f"- {ing}" for ing in recipe.ingredients)

        # Build instructions list
        instructions_md = "\n".join(
            f"{idx + 1}. {step}" for idx, step in enumerate(recipe.instructions)
        )

        # Build notes list
        if recipe.notes and len(recipe.notes) > 0:
            notes_md = "\n".join(f"- {note}" for note in recipe.notes)
        else:
            notes_md = "- None"

        # Construct markdown
        markdown = f"""# {recipe.name}

**Servings:** {recipe.servings}
**Time:** {recipe.prep_time} preparation + {recipe.cook_time} cooking (total: {recipe.total_time})
**Difficulty:** {recipe.difficulty}
**Link:** [YouTube]({youtube_url})

## Ingredients

{ingredients_md}

## Instructions

{instructions_md}

## Notes

{notes_md}
"""

        return markdown

    @staticmethod
    def format_batch(
        recipes: list[Recipe], video_id: str, youtube_url: str = ""
    ) -> list[dict]:
        """
        Format multiple recipes.

        Args:
            recipes: List of Recipe objects
            video_id: YouTube video ID
            youtube_url: Full YouTube URL (optional)

        Returns:
            List of dicts with title, icon, content, and video_id
        """
        formatted = []

        for recipe in recipes:
            markdown = RecipeFormatter.format(recipe, video_id, youtube_url)
            formatted.append(
                {
                    "title": recipe.name,
                    "icon": recipe.icon or "🍽️",
                    "content": markdown,
                    "video_id": video_id,
                }
            )

        return formatted


def format_recipe(recipe: Recipe, video_id: str, youtube_url: str = "") -> dict:
    """
    Convenience function to format a single recipe.

    Args:
        recipe: Recipe object
        video_id: YouTube video ID
        youtube_url: Full YouTube URL

    Returns:
        Dict with title, icon, content, video_id
    """
    markdown = RecipeFormatter.format(recipe, video_id, youtube_url)
    return {
        "title": recipe.name,
        "icon": recipe.icon or "🍽️",
        "content": markdown,
        "video_id": video_id,
    }
