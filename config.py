import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Variabel TELEGRAM_BOT_TOKEN tidak ditemukan. Pastikan sudah diisi di file .env")

if not GROQ_API_KEY:
    raise ValueError("Variabel GROQ_API_KEY tidak ditemukan. Pastikan sudah diisi di file .env")
