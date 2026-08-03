import logging
from asyncio import Lock
from collections import defaultdict, deque
from dataclasses import dataclass

from pyrogram import Client
from pytgcalls import PyTgCalls, filters
from pytgcalls.types import StreamEnded

from bot.config import Settings
from bot.media import Media, find_media

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class QueueItem:
    media: Media
    video: bool


@dataclass(frozen=True, slots=True)
class EnqueueResult:
    item: QueueItem
    started: bool
    position: int


class Player:
    def __init__(self, settings: Settings) -> None:
        self.client = Client(
            "videoplay",
            api_id=settings.api_id,
            api_hash=settings.api_hash,
            session_string=settings.session_string,
            in_memory=True,
        )
        self.calls = PyTgCalls(self.client)
        self.assistant_user_id = settings.assistant_user_id
        self.assistant_username = settings.assistant_username
        self.current: dict[int, QueueItem] = {}
        self.queues: dict[int, deque[QueueItem]] = defaultdict(deque)
        self.locks: dict[int, Lock] = defaultdict(Lock)
        self.calls.on_update(filters.stream_end(StreamEnded.Type.AUDIO))(
            self._on_stream_end
        )

    async def start(self) -> None:
        await self.calls.start()
        account = await self.client.get_me()
        if account.id != self.assistant_user_id:
            await self.calls.stop()
            raise RuntimeError(
                "SESSION_STRING принадлежит другому аккаунту: "
                f"ожидался ID {self.assistant_user_id}, получен {account.id}"
            )
        if account.username and account.username.lower() != self.assistant_username.lower():
            logger.warning(
                "Username ассистента изменился: ожидался @%s, получен @%s. "
                "Проверка по постоянному ID пройдена.",
                self.assistant_username,
                account.username,
            )

    async def enqueue(self, chat_id: int, query: str, *, video: bool) -> EnqueueResult:
        media = await find_media(query, video=video)
        item = QueueItem(media=media, video=video)
        async with self.locks[chat_id]:
            if chat_id not in self.current:
                await self.calls.play(chat_id, media.stream_url)
                self.current[chat_id] = item
                return EnqueueResult(item, True, 0)
            self.queues[chat_id].append(item)
            return EnqueueResult(item, False, len(self.queues[chat_id]))

    async def _advance(self, chat_id: int) -> QueueItem | None:
        async with self.locks[chat_id]:
            if self.queues[chat_id]:
                item = self.queues[chat_id].popleft()
                await self.calls.play(chat_id, item.media.stream_url)
                self.current[chat_id] = item
                return item
            self.current.pop(chat_id, None)
            return None

    async def _on_stream_end(self, _client: PyTgCalls, update: StreamEnded) -> None:
        try:
            await self._advance(update.chat_id)
        except Exception:
            logger.exception("Could not advance queue in chat %s", update.chat_id)

    async def skip(self, chat_id: int) -> QueueItem | None:
        if chat_id not in self.current:
            return None
        item = await self._advance(chat_id)
        if item is None:
            await self.calls.leave_call(chat_id)
        return item

    def get_queue(self, chat_id: int) -> tuple[QueueItem | None, list[QueueItem]]:
        return self.current.get(chat_id), list(self.queues[chat_id])

    async def pause(self, chat_id: int) -> bool:
        if chat_id not in self.current:
            return False
        await self.calls.pause(chat_id)
        return True

    async def resume(self, chat_id: int) -> bool:
        if chat_id not in self.current:
            return False
        await self.calls.resume(chat_id)
        return True

    async def leave(self, chat_id: int) -> bool:
        active = chat_id in self.current
        self.current.pop(chat_id, None)
        self.queues[chat_id].clear()
        if not active:
            return False
        await self.calls.leave_call(chat_id)
        return True

    async def stop_all(self) -> None:
        await self.calls.stop()
