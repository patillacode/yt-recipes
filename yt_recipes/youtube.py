"""YouTube video ID extraction and transcript fetching."""

import logging
import re

import httpx

from .config import Settings

logger = logging.getLogger("yt_recipes")


class YouTubeError(Exception):
    """Base exception for YouTube-related errors."""

    pass


class VideoIDExtractor:
    """Extract YouTube video ID from various URL formats."""

    @staticmethod
    def extract(url: str) -> str:
        """
        Extract video ID from YouTube URL.

        Supports formats:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        - https://www.youtube.com/v/VIDEO_ID

        Args:
            url: YouTube URL

        Returns:
            Extracted video ID

        Raises:
            YouTubeError: If URL format is invalid
        """
        video_id = ""

        # Handle youtube.com/watch format
        if "youtube.com/watch" in url:
            match = re.search(r"[?&]v=([^&]+)", url)
            if match:
                video_id = match.group(1)

        # Handle youtu.be format
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0].split("/")[0]

        # Handle youtube.com/embed format
        elif "youtube.com/embed/" in url:
            video_id = url.split("embed/")[1].split("?")[0].split("/")[0]

        # Handle youtube.com/v format
        elif "youtube.com/v/" in url:
            video_id = url.split("v/")[1].split("?")[0].split("/")[0]

        if not video_id:
            raise YouTubeError(
                "Invalid YouTube URL format. Supported formats: "
                "youtube.com/watch?v=ID, youtu.be/ID, youtube.com/embed/ID, "
                "youtube.com/v/ID"
            )

        logger.debug(f"Extracted video ID: {video_id}")
        return video_id


class TranscriptFetcher:
    """Fetch YouTube video transcripts using RapidAPI."""

    def __init__(self, settings: Settings):
        """
        Initialize transcript fetcher.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.client = httpx.Client(timeout=30.0)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def fetch(self, video_id: str) -> str:
        """
        Fetch transcript for a YouTube video.

        Args:
            video_id: YouTube video ID

        Returns:
            Transcript text

        Raises:
            YouTubeError: If transcript cannot be fetched
        """
        url = f"https://{self.settings.rapidapi_host}/api/transcript"
        headers = {
            "x-rapidapi-key": self.settings.rapidapi_key,
            "x-rapidapi-host": self.settings.rapidapi_host,
        }
        params = {"videoId": video_id}

        logger.debug(f"Fetching transcript for video ID: {video_id}")

        try:
            response = self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            raise YouTubeError(f"Failed to fetch transcript: {e}") from e

        # Parse transcript response
        transcript_text = self._parse_transcript(data)

        if not transcript_text or transcript_text.strip() == "":
            raise YouTubeError("No transcript text found in response")

        logger.info(f"Fetched transcript ({len(transcript_text)} characters)")
        return transcript_text

    def _parse_transcript(self, data: any) -> str:
        """
        Parse transcript from API response.

        Args:
            data: API response data

        Returns:
            Concatenated transcript text
        """
        transcript_text = ""

        # Handle different response formats
        if isinstance(data, list):
            transcript_text = " ".join(str(segment.get("text", "")) for segment in data)
        elif isinstance(data, dict) and "transcript" in data:
            if isinstance(data["transcript"], list):
                transcript_text = " ".join(
                    str(segment.get("text", "")) for segment in data["transcript"]
                )
        elif isinstance(data, str):
            transcript_text = data

        return transcript_text.strip()


def extract_video_id(url: str) -> str:
    """
    Convenience function to extract video ID.

    Args:
        url: YouTube URL

    Returns:
        Video ID
    """
    return VideoIDExtractor.extract(url)


def fetch_transcript(video_id: str, settings: Settings) -> str:
    """
    Convenience function to fetch transcript.

    Args:
        video_id: YouTube video ID
        settings: Application settings

    Returns:
        Transcript text
    """
    with TranscriptFetcher(settings) as fetcher:
        return fetcher.fetch(video_id)
