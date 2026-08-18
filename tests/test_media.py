import unittest
from unittest.mock import MagicMock, patch

from bot.errors import MediaNotFoundError, MediaSearchError
from bot.media import _extract
from yt_dlp.utils import DownloadError


class MediaExtractionTests(unittest.TestCase):
    @patch("bot.media.yt_dlp.YoutubeDL")
    def test_extracts_first_search_result(self, youtube_dl: MagicMock) -> None:
        youtube_dl.return_value.__enter__.return_value.extract_info.return_value = {
            "entries": [{
                "title": "Track",
                "webpage_url": "https://example.test/watch?v=1",
                "url": "https://cdn.example.test/audio",
                "duration": 123,
                "http_headers": {"User-Agent": "test-agent"},
            }]
        }
        media = _extract("track name", video=False)
        self.assertEqual(media.title, "Track")
        self.assertEqual(media.duration, 123)
        self.assertEqual(media.headers["User-Agent"], "test-agent")

    @patch("bot.media.yt_dlp.YoutubeDL")
    def test_empty_search_has_specific_error(self, youtube_dl: MagicMock) -> None:
        youtube_dl.return_value.__enter__.return_value.extract_info.return_value = {
            "entries": []
        }
        with self.assertRaises(MediaNotFoundError):
            _extract("missing", video=False)

    @patch("bot.media.yt_dlp.YoutubeDL")
    def test_provider_failure_has_specific_error(self, youtube_dl: MagicMock) -> None:
        youtube_dl.return_value.__enter__.return_value.extract_info.side_effect = (
            DownloadError("blocked")
        )
        with self.assertRaises(MediaSearchError):
            _extract("blocked", video=False)


if __name__ == "__main__":
    unittest.main()
