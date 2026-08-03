import asyncio
from dataclasses import dataclass
from functools import partial

import yt_dlp


@dataclass(frozen=True, slots=True)
class Media:
    title: str
    webpage_url: str
    stream_url: str
    duration: int | None


def _extract(query: str, video: bool) -> Media:
    source = query if query.startswith(("http://", "https://")) else f"ytsearch1:{query}"
    options = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
        "format": (
            "best[height<=720][vcodec!=none][acodec!=none]/best[height<=720]/best"
            if video
            else "bestaudio/best"
        ),
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(source, download=False)

    if "entries" in info:
        entries = [entry for entry in info["entries"] if entry]
        if not entries:
            raise LookupError("Ничего не найдено")
        info = entries[0]

    stream_url = info.get("url")
    if not stream_url:
        raise LookupError("Не удалось получить ссылку на медиапоток")

    return Media(
        title=info.get("title") or query,
        webpage_url=info.get("webpage_url") or query,
        stream_url=stream_url,
        duration=info.get("duration"),
    )


async def find_media(query: str, *, video: bool) -> Media:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(_extract, query, video))
