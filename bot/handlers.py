from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiogram import F, Router, html
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.i18n import LanguageStore
from bot.errors import (
    AssistantJoinError,
    MediaNotFoundError,
    MediaSearchError,
    PlaybackError,
)

if TYPE_CHECKING:
    from bot.player import Player

router = Router(name="player")
logger = logging.getLogger(__name__)
GROUPS = F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP})


def start_keyboard(username: str, lang: str, store: LanguageStore, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=store.text(user_id, "add"), url=f"https://t.me/{username}?startgroup=true")],
        [InlineKeyboardButton(text=store.text(user_id, "change_language"), callback_data="language")],
    ])


def language_keyboard(store: LanguageStore, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang:uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
        [InlineKeyboardButton(text="🇺🇸 English", callback_data="lang:en")],
        [InlineKeyboardButton(text=store.text(user_id, "back"), callback_data="home")],
    ])


@router.message(CommandStart())
async def start(message: Message, language_store: LanguageStore) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if message.chat.type == ChatType.PRIVATE:
        me = await message.bot.get_me()
        await message.answer(
            language_store.text(
                user_id,
                "start",
                name=html.quote(message.from_user.full_name if message.from_user else "do'stim"),
            ),
            reply_markup=start_keyboard(me.username or "", language_store.get(user_id), language_store, user_id),
        )
    else:
        await message.answer(language_store.text(user_id, "help"))


@router.message(Command("help"))
async def help_command(message: Message, language_store: LanguageStore) -> None:
    await message.answer(language_store.text(message.from_user.id if message.from_user else None, "help"))


@router.message(Command("language"))
async def language_command(message: Message, language_store: LanguageStore) -> None:
    user_id = message.from_user.id if message.from_user else 0
    await message.answer(
        language_store.text(user_id, "language"),
        reply_markup=language_keyboard(language_store, user_id),
    )


@router.callback_query(F.data == "language")
async def open_language(query: CallbackQuery, language_store: LanguageStore) -> None:
    await query.answer()
    if query.message:
        await query.message.edit_text(
            language_store.text(query.from_user.id, "language"),
            reply_markup=language_keyboard(language_store, query.from_user.id),
        )


@router.callback_query(F.data.startswith("lang:"))
async def select_language(query: CallbackQuery, language_store: LanguageStore) -> None:
    language_store.set(query.from_user.id, (query.data or "").split(":", 1)[1])
    await query.answer()
    if query.message:
        me = await query.bot.get_me()
        await query.message.edit_text(
            language_store.text(
                query.from_user.id,
                "start",
                name=html.quote(query.from_user.full_name),
            ),
            reply_markup=start_keyboard(me.username or "", language_store.get(query.from_user.id), language_store, query.from_user.id),
        )


@router.callback_query(F.data == "home")
async def home(query: CallbackQuery, language_store: LanguageStore) -> None:
    await query.answer()
    if query.message:
        me = await query.bot.get_me()
        await query.message.edit_text(
            language_store.text(
                query.from_user.id,
                "start",
                name=html.quote(query.from_user.full_name),
            ),
            reply_markup=start_keyboard(me.username or "", language_store.get(query.from_user.id), language_store, query.from_user.id),
        )


@router.message(F.new_chat_members)
async def bot_joined(message: Message, language_store: LanguageStore) -> None:
    me = await message.bot.get_me()
    if any(member.id == me.id for member in message.new_chat_members or []):
        await message.answer(language_store.text(message.from_user.id if message.from_user else None, "ready"))


async def _play(message: Message, command: CommandObject, player: Player, store: LanguageStore, *, video: bool) -> None:
    user_id = message.from_user.id if message.from_user else None
    query = (command.args or "").strip().strip('"')
    command_name = "vplay" if video else "play"
    if not query:
        await message.answer(store.text(user_id, "usage", command=command_name))
        return
    status = await message.answer(store.text(user_id, "searching", query=html.quote(query)))
    try:
        # Search first: do not invite the assistant for an invalid/blocked query.
        media = await player.resolve(query, video=video)
        joined = await player.ensure_assistant(message.bot, message.chat.id)
        if joined:
            await status.edit_text(store.text(user_id, "assistant_joined"))
        result = await player.enqueue_resolved(message.chat.id, media, video=video)
        key = "playing" if result.started else "queued"
        await status.edit_text(store.text(
            user_id, key, icon="🎬" if video else "🎵",
            title=html.quote(result.item.media.title), position=result.position,
        ))
    except AssistantJoinError as error:
        logger.exception("Assistant join failed in chat %s", message.chat.id)
        await status.edit_text(
            store.text(user_id, "assistant_join_failed", reason=html.quote(str(error)))
        )
    except MediaNotFoundError:
        logger.info("Media was not found in chat %s for query %r", message.chat.id, query)
        await status.edit_text(store.text(user_id, "not_found"))
    except MediaSearchError as error:
        logger.warning("Media search failed in chat %s: %s", message.chat.id, error)
        await status.edit_text(
            store.text(user_id, "search_failed", reason=html.quote(str(error)))
        )
    except PlaybackError as error:
        logger.exception("Voice-chat playback failed in chat %s", message.chat.id)
        await status.edit_text(
            store.text(user_id, "playback_failed", reason=html.quote(str(error)))
        )
    except Exception:
        logger.exception("Playback failed in chat %s", message.chat.id)
        await status.edit_text(store.text(user_id, "failed"))


@router.message(Command("play"), GROUPS)
async def play_audio(message: Message, command: CommandObject, player: Player, language_store: LanguageStore) -> None:
    await _play(message, command, player, language_store, video=False)


@router.message(Command("vplay", "video"), GROUPS)
async def play_video(message: Message, command: CommandObject, player: Player, language_store: LanguageStore) -> None:
    await _play(message, command, player, language_store, video=True)


@router.message(Command("pause"), GROUPS)
async def pause(message: Message, player: Player, language_store: LanguageStore) -> None:
    changed = await player.pause(message.chat.id)
    await message.answer(language_store.text(message.from_user.id, "paused" if changed else "nothing"))


@router.message(Command("resume"), GROUPS)
async def resume(message: Message, player: Player, language_store: LanguageStore) -> None:
    changed = await player.resume(message.chat.id)
    await message.answer(language_store.text(message.from_user.id, "resumed" if changed else "nothing"))


@router.message(Command("stop"), GROUPS)
async def stop(message: Message, player: Player, language_store: LanguageStore) -> None:
    changed = await player.leave(message.chat.id)
    await message.answer(language_store.text(message.from_user.id, "stopped" if changed else "nothing"))


@router.message(Command("skip"), GROUPS)
async def skip(message: Message, player: Player, language_store: LanguageStore) -> None:
    item = await player.skip(message.chat.id)
    if item:
        await message.answer(language_store.text(message.from_user.id, "skipped", title=html.quote(item.media.title)))
    else:
        await message.answer(language_store.text(message.from_user.id, "nothing"))


@router.message(Command("queue"), GROUPS)
async def show_queue(message: Message, player: Player, language_store: LanguageStore) -> None:
    current, queued = player.get_queue(message.chat.id)
    if not current and not queued:
        await message.answer(language_store.text(message.from_user.id, "queue_empty"))
        return
    lines = [language_store.text(message.from_user.id, "queue_title")]
    if current:
        lines.append(f"▶️ {html.quote(current.media.title)}")
    lines.extend(f"{index}. {html.quote(item.media.title)}" for index, item in enumerate(queued, 1))
    await message.answer("\n".join(lines))
