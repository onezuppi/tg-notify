import os
import logging
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import timezone, timedelta
from dotenv import load_dotenv

from background_check import background_check, STATE

load_dotenv()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
if not TELEGRAM_BOT_TOKEN:
    logging.error("TELEGRAM_BOT_TOKEN не задан в .env файле")
    exit(1)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DB_PATH = "bot.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            chat_id INTEGER NOT NULL,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def add_user(user_id: int, chat_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT OR IGNORE INTO users (user_id, chat_id) VALUES (?, ?)', (user_id, chat_id))
        conn.commit()
    except Exception as e:
        logger.error(f"Ошибка добавления пользователя: {e}")
    finally:
        conn.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    add_user(user.id, chat_id)
    welcome_text = (
        "Привет!\n\n"
        "Бот запущен и выполняет проверку страницы с билетами.\n"
        "Доступные команды:\n"
        "/start - Регистрация и приветственное сообщение\n"
        "/stats - Статистика последней проверки\n"
        "/info - Список команд"
    )
    await update.message.reply_text(welcome_text)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if STATE.get("last_request_time") and STATE.get("last_response"):
        tz = timezone(timedelta(hours=5))
        last_time_gmt5 = STATE.get("last_request_time").astimezone(tz)
        msg = (
            f"Последняя проверка: {last_time_gmt5.strftime('%Y-%m-%d %H:%M:%S')} (ЕКБ)\n"
            f"Результат: {STATE.get('last_response')}"
        )
    else:
        msg = "Проверки ещё не проводились."
    await update.message.reply_text(msg)


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info_text = (
        "/start - Регистрация и запуск уведомлений\n"
        "/stats - Статистика последней проверки\n"
        "/info - Информация о командах"
    )
    await update.message.reply_text(info_text)


def main():
    init_db()

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("info", info))

    app.job_queue.run_repeating(background_check, interval=3*60, first=30)

    app.run_polling()


if __name__ == "__main__":
    main()
