import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from bot.config import Settings
from bot.handlers import router
from bot.i18n import LanguageStore
from bot.player import Player


async def main() -> None:
    settings = Settings.from_env()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    player = Player(settings)
    language_store = LanguageStore()
    dispatcher = Dispatcher()
    dispatcher["player"] = player
    dispatcher["language_store"] = language_store
    dispatcher.include_router(router)

    await player.start()
    try:
        await bot.set_my_commands([
            BotCommand(command="play", description="🎵 Play music"),
            BotCommand(command="vplay", description="🎬 Play video"),
            BotCommand(command="skip", description="⏭ Next track"),
            BotCommand(command="pause", description="⏸ Pause"),
            BotCommand(command="resume", description="▶️ Resume"),
            BotCommand(command="stop", description="⏹ Stop"),
            BotCommand(command="queue", description="📋 Queue"),
            BotCommand(command="language", description="🌐 Language"),
            BotCommand(command="help", description="ℹ️ Help"),
        ])
        await dispatcher.start_polling(bot)
    finally:
        await player.stop_all()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
