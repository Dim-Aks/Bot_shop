import asyncio
import logging
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher


load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


async def main():
    from handlers import router
    dp.include_router(router)
    await bot.send_message(490243009, "Здарова!")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    logging.basicConfig(filename='logs/bot.log', level=logging.DEBUG)
    asyncio.run(main())
