import json
from pathlib import Path

LANGUAGES = {"uz", "ru", "en"}

TEXTS = {
    "ru": {
        "start": "🎵 <b>VideoPlay Music Bot</b>\n\nДобавьте бота в группу и дайте права приглашать пользователей и управлять видеочатами. Аккаунт @skroozy6 подключится автоматически при первой команде.",
        "language": "🌐 Выберите язык",
        "add": "➕ Добавить в группу",
        "change_language": "🌐 Изменить язык",
        "back": "⬅️ Назад",
        "help": "<b>Команды</b>\n/play — музыка\n/vplay или /video — видео\n/skip — следующий трек\n/pause — пауза\n/resume — продолжить\n/stop — остановить\n/queue — очередь\n/language — язык",
        "denied": "Команда доступна владельцу или администратору с правом управления видеочатами.",
        "usage": "Укажите название или ссылку: <code>/{command} название</code>",
        "searching": "🔎 Ищу: <b>{query}</b>",
        "assistant_joined": "✅ Аккаунт-ассистент автоматически добавлен. Запускаю поток…",
        "assistant_join_failed": "⚠️ {reason}\n\nВыдайте боту право приглашать пользователей.",
        "not_found": "🔎 Ничего не найдено. Уточните название или отправьте прямую ссылку YouTube.",
        "search_failed": "⚠️ Ошибка источника: {reason}.\nПопробуйте прямую ссылку или повторите позже.",
        "playback_failed": "⚠️ {reason}.\nУбедитесь, что видеочат уже запущен и @skroozy6 не заблокирован.",
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
        "ready": "✅ Бот готов. Выдайте право приглашать пользователей, запустите видеочат и используйте /play, /vplay или /video.",
    },
    "uz": {
        "start": "🎵 <b>VideoPlay Music Bot</b>\n\nAssalomu alaykum, <b>{name}</b>!",
        "language": "🌐 Tilni tanlang",
        "add": "➕ Guruhga qo'shish",
        "change_language": "🌐 Tilni o'zgartirish",
        "back": "⬅️ Ortga",
        "help": "<b>Buyruqlar</b>\n/play — musiqa\n/vplay yoki /video — video\n/skip — keyingi trek\n/pause — pauza\n/resume — davom ettirish\n/stop — to'xtatish\n/queue — navbat\n/language — til",
        "denied": "Buyruq faqat egasi yoki videochatlarni boshqarish huquqiga ega administrator uchun.",
        "usage": "Nom yoki havolani kiriting: <code>/{command} nomi</code>",
        "searching": "🔎 Qidirilmoqda: <b>{query}</b>",
        "assistant_joined": "✅ Assistent akkaunti avtomatik qo'shildi. Oqim boshlanmoqda…",
        "assistant_join_failed": "⚠️ {reason}\n\nBotga foydalanuvchilarni taklif qilish huquqini bering.",
        "not_found": "🔎 Hech narsa topilmadi. Nomni aniqlashtiring yoki YouTube havolasini yuboring.",
        "search_failed": "⚠️ Manba xatosi: {reason}.\nTo'g'ridan-to'g'ri havola yuboring yoki keyinroq urinib ko'ring.",
        "playback_failed": "⚠️ {reason}.\nVideochat boshlanganini va @skroozy6 bloklanmaganini tekshiring.",
        "playing": "{icon} Hozir ijro etilmoqda: <b>{title}</b>",
        "queued": "➕ Navbatga qo'shildi №{position}: <b>{title}</b>",
        "failed": "Oqimni boshlash imkoni bo'lmadi. Videochat, FFmpeg va @skroozy6 huquqlarini tekshiring.",
        "paused": "⏸ Ijro pauza qilindi.", "resumed": "▶️ Ijro davom etdi.",
        "stopped": "⏹ Ijro to'xtatildi, navbat tozalandi.",
        "skipped": "⏭ Keyingi: <b>{title}</b>", "queue_empty": "📭 Navbat bo'sh.",
        "queue_title": "📋 <b>Navbat</b>", "nothing": "Hozir hech narsa ijro etilmayapti.",
        "ready": "✅ Bot tayyor. Taklif qilish huquqini bering, videochatni boshlang va /play, /vplay yoki /video dan foydalaning.",
    },
    "en": {
        "start": "🎵 <b>VideoPlay Music Bot</b>\n\nAdd the bot to a group and grant permission to invite users and manage video chats. @skroozy6 will join automatically on the first command.",
        "language": "🌐 Select language", "add": "➕ Add to group",
        "change_language": "🌐 Change language", "back": "⬅️ Back",
        "help": "<b>Commands</b>\n/play — music\n/vplay or /video — video\n/skip — next track\n/pause — pause\n/resume — resume\n/stop — stop\n/queue — queue\n/language — language",
        "denied": "Only the owner or an admin allowed to manage video chats can use this command.",
        "usage": "Provide a title or URL: <code>/{command} title</code>",
        "searching": "🔎 Searching: <b>{query}</b>",
        "assistant_joined": "✅ The assistant account joined automatically. Starting stream…",
        "assistant_join_failed": "⚠️ {reason}\n\nGrant the bot permission to invite users.",
        "not_found": "🔎 Nothing was found. Refine the title or send a direct YouTube link.",
        "search_failed": "⚠️ Source error: {reason}.\nTry a direct link or try again later.",
        "playback_failed": "⚠️ {reason}.\nMake sure the video chat is active and @skroozy6 is not blocked.",
        "playing": "{icon} Now playing: <b>{title}</b>",
        "queued": "➕ Added to queue #{position}: <b>{title}</b>",
        "failed": "Could not start the stream. Check the active video chat, FFmpeg, and @skroozy6 permissions.",
        "paused": "⏸ Playback paused.", "resumed": "▶️ Playback resumed.",
        "stopped": "⏹ Playback stopped and queue cleared.",
        "skipped": "⏭ Switched to: <b>{title}</b>", "queue_empty": "📭 Queue is empty.",
        "queue_title": "📋 <b>Queue</b>", "nothing": "Nothing is playing now.",
        "ready": "✅ Bot is ready. Grant invite permission, start a video chat, and use /play, /vplay, or /video.",
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
