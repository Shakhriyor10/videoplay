import json
from pathlib import Path

LANGUAGES = {"uz", "ru", "en"}

TEXTS = {
    "ru": {
        "start": "🎵 <b>VideoPlay Music Bot</b>\n\nДобавьте бота и @skroozy6 в группу, назначьте администраторами и запустите видеочат.",
        "language": "🌐 Выберите язык",
        "add": "➕ Добавить в группу",
        "change_language": "🌐 Изменить язык",
        "back": "⬅️ Назад",
        "help": "<b>Команды</b>\n/play — музыка\n/vplay — видео\n/skip — следующий трек\n/pause — пауза\n/resume — продолжить\n/stop — остановить\n/queue — очередь\n/language — язык",
        "denied": "Команда доступна владельцу или администратору с правом управления видеочатами.",
        "usage": "Укажите название или ссылку: <code>/{command} название</code>",
        "searching": "🔎 Ищу: <b>{query}</b>",
        "playing": "{icon} Сейчас играет: <b>{title}</b>",
        "queued": "➕ Добавлено в очередь №{position}: <b>{title}</b>",
        "failed": "Не удалось запустить поток. Проверьте активный видеочат, FFmpeg и права @skroozy6.",
        "paused": "⏸ Воспроизведение приостановлено.",
        "resumed": "▶️ Воспроизведение продолжено.",
        "stopped": "⏹ Воспроизведение остановлено, очередь очищена.",
        "skipped": "⏭ Переключено: <b>{title}</b>",
        "queue_empty": "📭 Очередь пуста.",
        "queue_title": "📋 <b>Очередь</b>",
        "nothing": "Сейчас ничего не воспроизводится.",
        "ready": "✅ Бот готов. Запустите видеочат и используйте /play или /vplay.",
    },
    "uz": {
        "start": "🎵 <b>VideoPlay Music Bot</b>\n\nBot va @skroozy6 ni guruhga qo'shing, administrator qiling va videochatni boshlang.",
        "language": "🌐 Tilni tanlang",
        "add": "➕ Guruhga qo'shish",
        "change_language": "🌐 Tilni o'zgartirish",
        "back": "⬅️ Ortga",
        "help": "<b>Buyruqlar</b>\n/play — musiqa\n/vplay — video\n/skip — keyingi trek\n/pause — pauza\n/resume — davom ettirish\n/stop — to'xtatish\n/queue — navbat\n/language — til",
        "denied": "Buyruq faqat egasi yoki videochatlarni boshqarish huquqiga ega administrator uchun.",
        "usage": "Nom yoki havolani kiriting: <code>/{command} nomi</code>",
        "searching": "🔎 Qidirilmoqda: <b>{query}</b>",
        "playing": "{icon} Hozir ijro etilmoqda: <b>{title}</b>",
        "queued": "➕ Navbatga qo'shildi №{position}: <b>{title}</b>",
        "failed": "Oqimni boshlash imkoni bo'lmadi. Videochat, FFmpeg va @skroozy6 huquqlarini tekshiring.",
        "paused": "⏸ Ijro pauza qilindi.", "resumed": "▶️ Ijro davom etdi.",
        "stopped": "⏹ Ijro to'xtatildi, navbat tozalandi.",
        "skipped": "⏭ Keyingi: <b>{title}</b>", "queue_empty": "📭 Navbat bo'sh.",
        "queue_title": "📋 <b>Navbat</b>", "nothing": "Hozir hech narsa ijro etilmayapti.",
        "ready": "✅ Bot tayyor. Videochatni boshlang va /play yoki /vplay dan foydalaning.",
    },
    "en": {
        "start": "🎵 <b>VideoPlay Music Bot</b>\n\nAdd the bot and @skroozy6 to a group, make them admins, and start a video chat.",
        "language": "🌐 Select language", "add": "➕ Add to group",
        "change_language": "🌐 Change language", "back": "⬅️ Back",
        "help": "<b>Commands</b>\n/play — music\n/vplay — video\n/skip — next track\n/pause — pause\n/resume — resume\n/stop — stop\n/queue — queue\n/language — language",
        "denied": "Only the owner or an admin allowed to manage video chats can use this command.",
        "usage": "Provide a title or URL: <code>/{command} title</code>",
        "searching": "🔎 Searching: <b>{query}</b>",
        "playing": "{icon} Now playing: <b>{title}</b>",
        "queued": "➕ Added to queue #{position}: <b>{title}</b>",
        "failed": "Could not start the stream. Check the active video chat, FFmpeg, and @skroozy6 permissions.",
        "paused": "⏸ Playback paused.", "resumed": "▶️ Playback resumed.",
        "stopped": "⏹ Playback stopped and queue cleared.",
        "skipped": "⏭ Switched to: <b>{title}</b>", "queue_empty": "📭 Queue is empty.",
        "queue_title": "📋 <b>Queue</b>", "nothing": "Nothing is playing now.",
        "ready": "✅ Bot is ready. Start a video chat and use /play or /vplay.",
    },
}


class LanguageStore:
    def __init__(self, path: str = "languages.json") -> None:
        self.path = Path(path)
        try:
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            self.data = {}

    def get(self, user_id: int | None) -> str:
        return self.data.get(str(user_id), "uz")

    def set(self, user_id: int, language: str) -> None:
        if language not in LANGUAGES:
            return
        self.data[str(user_id)] = language
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def text(self, user_id: int | None, key: str, **values: object) -> str:
        return TEXTS[self.get(user_id)][key].format(**values)
