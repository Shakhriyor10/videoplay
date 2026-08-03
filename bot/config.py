import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    api_id: int
    api_hash: str
    session_string: str
    assistant_user_id: int
    assistant_username: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        required = ("BOT_TOKEN", "API_ID", "API_HASH", "SESSION_STRING")
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            names = ", ".join(missing)
            raise RuntimeError(f"Не заданы переменные окружения: {names}")

        return cls(
            bot_token=os.environ["BOT_TOKEN"],
            api_id=int(os.environ["API_ID"]),
            api_hash=os.environ["API_HASH"],
            session_string=os.environ["SESSION_STRING"],
            assistant_user_id=int(os.getenv("ASSISTANT_USER_ID", "8807687180")),
            assistant_username=os.getenv("ASSISTANT_USERNAME", "skroozy6").lstrip("@"),
        )
