import asyncio
import logging
import os

from .app import App


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app = App(os.environ["BOT_TOKEN"], int(os.environ["ADMIN_ID"]), os.getenv("DB_PATH", "work/bot.db"))
    asyncio.run(app.run())


if __name__ == "__main__":
    main()
