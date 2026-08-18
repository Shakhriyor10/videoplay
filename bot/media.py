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


def _source(query: str, provider: str) -> str:
    if query.startswith(("http://", "https://")):
        return query
    # The first search hit is often deleted, geo-blocked or members-only.
    # Ask for several candidates; the extraction command ignores broken entries
    # and we select the first playable one below.
    prefix = "scsearch5" if provider == "soundcloud" else "ytsearch5"
    return f"{prefix}:{query}"


def _common_command_options(command: list[str]) -> None:
    # Allow yt-dlp to keep its official YouTube JS challenge solver current.
    command.extend(["--remote-components", "ejs:github"])

    cookie_file = os.getenv("YTDLP_COOKIE_FILE", "").strip()
    if cookie_file:
        command.extend(["--cookies", cookie_file])

    provider_url = os.getenv("YTDLP_POT_PROVIDER_URL", "").strip().rstrip("/")
    if provider_url:
        command.extend([
            "--extractor-args", "youtube:player_client=mweb",
            "--extractor-args", f"youtubepot-bgutilhttp:base_url={provider_url}",
        ])


def _extract(query: str, video: bool) -> Media:
    source = _source(query, "youtube")
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


def _media_from_info(info: dict, fallback_title: str) -> Media:
    stream_url = info.get("url")
    if not stream_url:
        raise MediaSearchError("source did not return a playable stream")
    return Media(
        title=info.get("title") or fallback_title,
        webpage_url=info.get("webpage_url") or fallback_title,
        stream_url=stream_url,
        duration=info.get("duration"),
        headers={str(key): str(value) for key, value in (info.get("http_headers") or {}).items()},
    )


async def _extract_info(source: str, *, video: bool, flat: bool = False) -> dict:
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
        "--skip-download",
        "--no-cache-dir",
        "--socket-timeout",
        "20",
        "--retries",
        "2",
        "--extractor-retries",
        "2",
        "--dump-single-json",
    ]
    if flat:
        command.extend(["--flat-playlist", "--playlist-end", "5"])
    else:
        command.extend(["--no-playlist", "--format", media_format])
    _common_command_options(command)
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
        raise MediaSearchError("source extraction failed")

    try:
        return json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MediaSearchError("Источник вернул некорректный ответ") from error


async def find_media(query: str, *, video: bool, provider: str = "youtube") -> Media:
    if query.startswith(("http://", "https://")):
        return _media_from_info(
            await _extract_info(query, video=video),
            query,
        )

    search = await _extract_info(_source(query, provider), video=video, flat=True)
    entries = [entry for entry in search.get("entries", []) if entry]
    if not entries:
        raise MediaNotFoundError("По этому запросу ничего не найдено")

    for entry in entries:
        candidate = entry.get("webpage_url") or entry.get("url") or entry.get("id")
        if not candidate:
            continue
        candidate = str(candidate)
        if provider == "youtube" and not candidate.startswith(("http://", "https://")):
            candidate = f"https://www.youtube.com/watch?v={candidate}"
        try:
            info = await _extract_info(candidate, video=video)
            return _media_from_info(info, entry.get("title") or query)
        except MediaSearchError:
            logger.info("Skipping unavailable %s candidate %s", provider, candidate)

    raise MediaSearchError(f"no playable {provider} candidates")
