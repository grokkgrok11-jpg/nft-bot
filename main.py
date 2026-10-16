import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

BOT_TOKEN = "8850115069:AAHt8yX4-4gswis3VY4mmO2zj_ipBjkK2s4"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Живой")

@dp.message()
async def echo(message: Message):
    await message.answer(f"Получил: {message.text}")

async def main():
    print("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
