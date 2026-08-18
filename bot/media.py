import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass

import yt_dlp
from yt_dlp.utils import DownloadError

from bot.errors import MediaNotFoundError, MediaSearchError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Media:
    title: str
    webpage_url: str
    stream_url: str
    duration: int | None
    headers: dict[str, str]


def _extract(query: str, video: bool) -> Media:
    source = query if query.startswith(("http://", "https://")) else f"ytsearch1:{query}"
    options = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
        "socket_timeout": 20,
        "retries": 2,
        "fragment_retries": 2,
        "extractor_retries": 2,
        "geo_bypass": True,
        "cachedir": False,
        "format": (
            "best[height<=720][vcodec!=none][acodec!=none]/best[height<=720]/best"
            if video
            else "bestaudio/best"
        ),
    }
    cookie_file = os.getenv("YTDLP_COOKIE_FILE", "").strip()
    if cookie_file:
        options["cookiefile"] = cookie_file

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(source, download=False)
    except DownloadError as error:
        logger.warning("yt-dlp failed for query %r: %s", query, error)
        raise MediaSearchError("YouTube не ответил или ограничил сервер") from error

    if not info:
        raise MediaNotFoundError("По этому запросу ничего не найдено")

    if "entries" in info:
        entries = [entry for entry in info["entries"] if entry]
        if not entries:
            raise MediaNotFoundError("По этому запросу ничего не найдено")
        info = entries[0]

    stream_url = info.get("url")
    if not stream_url:
        raise MediaSearchError("Источник не предоставил ссылку на поток")

    return Media(
        title=info.get("title") or query,
        webpage_url=info.get("webpage_url") or query,
        stream_url=stream_url,
        duration=info.get("duration"),
        headers={str(key): str(value) for key, value in (info.get("http_headers") or {}).items()},
    )


async def find_media(query: str, *, video: bool) -> Media:
    source = query if query.startswith(("http://", "https://")) else f"ytsearch1:{query}"
    media_format = (
        "best[height<=720][vcodec!=none][acodec!=none]/best[height<=720]/best"
        if video
        else "bestaudio/best"
    )
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--quiet",
        "--no-warnings",
        "--no-playlist",
        "--skip-download",
        "--no-cache-dir",
        "--socket-timeout",
        "20",
        "--retries",
        "2",
        "--extractor-retries",
        "2",
        "--format",
        media_format,
        "--dump-single-json",
    ]
    cookie_file = os.getenv("YTDLP_COOKIE_FILE", "").strip()
    if cookie_file:
        command.extend(["--cookies", cookie_file])
    command.append(source)

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        async with asyncio.timeout(45):
            stdout, stderr = await process.communicate()
    except TimeoutError as error:
        process.kill()
        await process.wait()
        raise MediaSearchError("Поиск занял больше 45 секунд") from error

    if process.returncode != 0:
        detail = stderr.decode("utf-8", errors="replace").strip().splitlines()
        if detail:
            logger.warning("yt-dlp subprocess failed: %s", detail[-1])
        raise MediaSearchError("YouTube не ответил или ограничил сервер")

    try:
        info = json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MediaSearchError("Источник вернул некорректный ответ") from error

    if "entries" in info:
        entries = [entry for entry in info["entries"] if entry]
        if not entries:
            raise MediaNotFoundError("По этому запросу ничего не найдено")
        info = entries[0]
    stream_url = info.get("url")
    if not stream_url:
        raise MediaSearchError("Источник не предоставил ссылку на поток")
    return Media(
        title=info.get("title") or query,
        webpage_url=info.get("webpage_url") or query,
        stream_url=stream_url,
        duration=info.get("duration"),
        headers={str(key): str(value) for key, value in (info.get("http_headers") or {}).items()},
    )
