import logging
import asyncio
from asyncio import Lock
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from pyrogram import Client
from pytgcalls import PyTgCalls, filters
from pytgcalls.types import MediaStream, StreamEnded

from bot.config import Settings
from bot.errors import AssistantJoinError, PlaybackError
from bot.media import Media, cleanup_media, find_media, prepare_media

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
        self.assistant_locks: dict[int, Lock] = defaultdict(Lock)
        self.calls.on_update(filters.stream_end(StreamEnded.Type.AUDIO))(
            self._on_stream_end
        )

    async def start(self) -> None:
        await self.calls.start()
        account = await self.client.get_me()
        if account.id != self.assistant_user_id:
            await self.client.stop()
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

    async def ensure_assistant(self, bot: Any, chat_id: int) -> bool:
        """Join the assistant through a temporary one-use invite when necessary."""
        async with self.assistant_locks[chat_id]:
            try:
                bot_info = await bot.get_me()
                bot_member = await bot.get_chat_member(chat_id, bot_info.id)
                if not getattr(bot_member, "can_invite_users", False):
                    raise AssistantJoinError(
                        "Боту требуется право приглашать пользователей."
                    )

                try:
                    member = await bot.get_chat_member(chat_id, self.assistant_user_id)
                    status = getattr(member.status, "value", member.status)
                except Exception:
                    status = "left"
                if status in {"member", "administrator", "creator", "restricted"}:
                    return False

                if status == "kicked":
                    await bot.unban_chat_member(
                        chat_id,
                        self.assistant_user_id,
                        only_if_banned=True,
                    )

                invite = await bot.create_chat_invite_link(
                    chat_id=chat_id,
                    name="VideoPlay assistant",
                    expire_date=datetime.now(timezone.utc) + timedelta(minutes=2),
                    member_limit=1,
                )
                try:
                    await self.client.join_chat(invite.invite_link)
                finally:
                    try:
                        await bot.revoke_chat_invite_link(chat_id, invite.invite_link)
                    except Exception:
                        logger.warning(
                            "Could not revoke assistant invite in chat %s",
                            chat_id,
                            exc_info=True,
                        )

                if getattr(bot_member, "can_promote_members", False):
                    try:
                        await bot.promote_chat_member(
                            chat_id=chat_id,
                            user_id=self.assistant_user_id,
                            can_manage_video_chats=True,
                        )
                    except Exception:
                        logger.warning(
                            "Assistant joined chat %s but could not be promoted",
                            chat_id,
                            exc_info=True,
                        )
                return True
            except AssistantJoinError:
                raise
            except Exception as error:
                raise AssistantJoinError(
                    "Не удалось автоматически добавить аккаунт-ассистент."
                ) from error

    async def resolve(self, query: str, *, video: bool) -> Media:
        return await find_media(query, video=video)

    @staticmethod
    def _stream(item: QueueItem) -> MediaStream:
        source = item.media.local_path or item.media.stream_url
        return MediaStream(
            source,
            headers=None if item.media.local_path else (item.media.headers or None),
            video_flags=(
                MediaStream.Flags.AUTO_DETECT
                if item.video
                else MediaStream.Flags.IGNORE
            ),
        )

    async def enqueue_resolved(
        self,
        chat_id: int,
        media: Media,
        *,
        video: bool,
    ) -> EnqueueResult:
        item = QueueItem(media=media, video=video)
        async with self.locks[chat_id]:
            if chat_id not in self.current:
                item.media = await prepare_media(item.media, video=item.video)
                try:
                    async with asyncio.timeout(40):
                        await self.calls.play(chat_id, self._stream(item))
                except TimeoutError as error:
                    cleanup_media(item.media)
                    raise PlaybackError("Подключение к видеочату превысило 40 секунд") from error
                except Exception as error:
                    cleanup_media(item.media)
                    raise PlaybackError("Не удалось подключиться к активному видеочату") from error
                self.current[chat_id] = item
                return EnqueueResult(item, True, 0)
            self.queues[chat_id].append(item)
            return EnqueueResult(item, False, len(self.queues[chat_id]))

    async def _advance(self, chat_id: int) -> QueueItem | None:
        async with self.locks[chat_id]:
            if self.queues[chat_id]:
                previous = self.current.get(chat_id)
                item = self.queues[chat_id].popleft()
                # Resolve and download a fresh local copy immediately before playback.
                item.media = await find_media(item.media.webpage_url, video=item.video)
                item.media = await prepare_media(item.media, video=item.video)
                try:
                    await self.calls.play(chat_id, self._stream(item))
                except Exception:
                    cleanup_media(item.media)
                    raise
                self.current[chat_id] = item
                cleanup_media(previous.media if previous else None)
                return item
            previous = self.current.pop(chat_id, None)
            cleanup_media(previous.media if previous else None)
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
        current = self.current.pop(chat_id, None)
        cleanup_media(current.media if current else None)
        for item in self.queues[chat_id]:
            cleanup_media(item.media)
        self.queues[chat_id].clear()
        if not active:
            return False
        await self.calls.leave_call(chat_id)
        return True

    async def stop_all(self) -> None:
        for chat_id in list(self.current):
            try:
                await self.calls.leave_call(chat_id)
            except Exception:
                logger.debug("Could not leave chat %s during shutdown", chat_id, exc_info=True)
            cleanup_media(self.current[chat_id].media)
        self.current.clear()
        self.queues.clear()
        if self.client.is_connected:
            await self.client.stop()
