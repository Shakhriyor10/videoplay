import asyncio

from pyrogram import Client


async def main() -> None:
    api_id = int(input("API_ID: ").strip())
    api_hash = input("API_HASH: ").strip()
    async with Client("videoplay_session", api_id=api_id, api_hash=api_hash, in_memory=True) as app:
        print("\nSESSION_STRING (сохраните в .env и никому не отправляйте):")
        print(await app.export_session_string())


if __name__ == "__main__":
    asyncio.run(main())
