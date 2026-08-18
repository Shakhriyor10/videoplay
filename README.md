# VideoPlay

Telegram-бот на aiogram 3 для воспроизведения музыки и видео в групповом видеочате.

## Как это устроено

- Bot API (`aiogram`) принимает команды.
- Пользовательский аккаунт-помощник (`Kurigram` + `PyTgCalls`) входит в видеочат.
- `yt-dlp` ищет медиа и получает поток.

Обычный Bot API не умеет самостоятельно подключаться к групповым звонкам, поэтому
`SESSION_STRING` пользовательского аккаунта обязателен. Используйте отдельный аккаунт:
автоматизация пользовательского аккаунта может нести риск ограничений со стороны Telegram.

## Установка

Требуются Python 3.10+ и FFmpeg в `PATH`.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Если ранее был установлен оригинальный `Pyrogram 2.0.106`, удалите его перед установкой:

```powershell
python -m pip uninstall -y Pyrogram
python -m pip install --upgrade --force-reinstall -r requirements.txt
```

Заполните `.env`: `BOT_TOKEN` возьмите у BotFather, `API_ID` и `API_HASH` — на
https://my.telegram.org. Строку аккаунта-помощника создайте интерактивной командой
`python generate_session.py` и поместите результат в `SESSION_STRING`.

Для аккаунта `@skroozy6` оставьте значения:

```env
ASSISTANT_USER_ID=8807687180
ASSISTANT_USERNAME=skroozy6
```

Приложение проверяет постоянный ID авторизованного аккаунта при запуске.

### Ограничения YouTube на VPS

Если журнал содержит `HTTP Error 403` или `Sign in to confirm you're not a bot`,
YouTube ограничил IP сервера. Экспортируйте cookies отдельного тестового YouTube-аккаунта
в Netscape-формате, сохраните их вне Git как `/var/www/videoplay/cookies.txt` и добавьте:

```env
YTDLP_COOKIE_FILE=/var/www/videoplay/cookies.txt
```

Защитите файл командой `chmod 600 /var/www/videoplay/cookies.txt`. Не добавляйте его
в репозиторий. Использование аккаунта с yt-dlp может привести к ограничениям YouTube,
поэтому не используйте основной личный аккаунт.

Добавьте бота и аккаунт-помощник в группу. Аккаунту-помощнику разрешите управлять
видеочатами. Сначала вручную запустите видеочат, затем выполните `python bot.py`
(точка запуска `python main.py` также поддерживается).

## Команды

- `/play название или ссылка` — аудио;
- `/vplay название или ссылка` — видео до 720p;
- `/video название или ссылка` — алиас команды `/vplay`;
- `/skip` — следующий трек;
- `/pause` — пауза;
- `/resume` — продолжить;
- `/stop` — выйти из видеочата и очистить очередь;
- `/queue` — показать текущий трек и очередь;
- `/language` — русский, узбекский или английский язык;
- `/help` — справка.

Все участники группы могут использовать команды воспроизведения и управления.
