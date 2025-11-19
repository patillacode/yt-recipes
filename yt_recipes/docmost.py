"""Docmost API client for recipe upload and management."""

import io
import logging
import re
from typing import Any

import httpx

from .config import Settings

logger = logging.getLogger("yt_recipes")


class DocmostError(Exception):
    """Base exception for Docmost-related errors."""

    pass


class DocmostClient:
    """Client for interacting with Docmost API."""

    def __init__(self, settings: Settings):
        """
        Initialize Docmost client.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.client = httpx.Client(timeout=30.0, follow_redirects=True)
        self.auth_token: str | None = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def login(self) -> str:
        """
        Authenticate with Docmost and obtain auth token.

        Returns:
            Authentication token

        Raises:
            DocmostError: If login fails
        """
        url = f"{self.settings.docmost_url}/api/auth/login"
        data = {
            "email": self.settings.docmost_email,
            "password": self.settings.docmost_password,
        }

        headers = {"Authorization": "Bearer"}
        logger.debug("Logging into Docmost...")

        try:
            response = self.client.post(url, headers=headers, data=data)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise DocmostError(f"Login failed: {e}") from e

        # Extract authToken from set-cookie header
        auth_token = self._extract_auth_token(response)

        if not auth_token:
            raise DocmostError("Failed to extract auth token from login response")

        self.auth_token = auth_token
        logger.info("Successfully authenticated with Docmost")
        return auth_token

    def _extract_auth_token(self, response: httpx.Response) -> str | None:
        """
        Extract auth token from response cookies.

        Args:
            response: HTTP response from login

        Returns:
            Auth token if found, None otherwise
        """
        set_cookie_headers = response.headers.get_list("set-cookie")

        for cookie in set_cookie_headers:
            if "authToken=" in cookie:
                match = re.search(r"authToken=([^;]+)", cookie)
                if match:
                    return match.group(1)

        return None

    def import_recipe(self, title: str, content: str, icon: str = "🍽️") -> dict[str, Any]:
        """
        Import a recipe to Docmost as a new page.

        Args:
            title: Recipe title
            content: Recipe content in markdown
            icon: Recipe icon emoji

        Returns:
            Response data with created page info

        Raises:
            DocmostError: If import fails
        """
        if not self.auth_token:
            raise DocmostError("Not authenticated. Call login() first.")

        url = f"{self.settings.docmost_url}/api/pages/import"
        headers = {"Cookie": f"authToken={self.auth_token}"}

        # Create multipart form data
        files = {
            "file": ("recipe.md", io.BytesIO(content.encode("utf-8")), "text/markdown")
        }
        data = {
            "title": title,
            "spaceId": self.settings.docmost_space_id,
            "icon": icon,
        }

        logger.debug(f"Importing recipe: {title}")

        try:
            response = self.client.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            result = response.json()
        except httpx.HTTPError as e:
            raise DocmostError(f"Failed to import recipe: {e}") from e

        logger.info(f"Imported recipe: {title}")
        return result

    def move_to_folder(self, page_id: str) -> dict[str, Any]:
        """
        Move a page to the configured recipe folder.

        Args:
            page_id: ID of the page to move

        Returns:
            Response data

        Raises:
            DocmostError: If move fails
        """
        if not self.auth_token:
            raise DocmostError("Not authenticated. Call login() first.")

        url = f"{self.settings.docmost_url}/api/pages/move"
        headers = {
            "Cookie": f"authToken={self.auth_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "pageId": page_id,
            "position": "ZZZZZ",  # Position at end
            "parentPageId": self.settings.docmost_parent_page_id,
        }

        logger.debug(f"Moving page {page_id} to recipe folder")

        try:
            response = self.client.post(url, headers=headers, data=data)
            response.raise_for_status()
            result = response.json()
        except httpx.HTTPError as e:
            raise DocmostError(f"Failed to move page: {e}") from e

        logger.debug(f"Moved page {page_id} to recipe folder")
        return result

    def upload_recipe(self, title: str, content: str, icon: str = "🍽️") -> str:
        """
        Upload a recipe and move it to the recipe folder.

        This is a convenience method that combines import and move operations.

        Args:
            title: Recipe title
            content: Recipe content in markdown
            icon: Recipe icon emoji

        Returns:
            Page ID of the uploaded recipe

        Raises:
            DocmostError: If upload fails
        """
        # Import the recipe
        import_result = self.import_recipe(title, content, icon)

        # Extract page ID
        try:
            page_id = import_result["data"]["id"]
        except (KeyError, TypeError) as e:
            raise DocmostError(
                f"Failed to extract page ID from import result: {e}"
            ) from e

        # Move to folder
        self.move_to_folder(page_id)

        logger.info(f"Successfully uploaded recipe: {title} (ID: {page_id})")
        return page_id


def upload_to_docmost(title: str, content: str, icon: str, settings: Settings) -> str:
    """
    Convenience function to upload a recipe to Docmost.

    Args:
        title: Recipe title
        content: Recipe markdown content
        icon: Recipe icon
        settings: Application settings

    Returns:
        Page ID
    """
    with DocmostClient(settings) as client:
        client.login()
        return client.upload_recipe(title, content, icon)
