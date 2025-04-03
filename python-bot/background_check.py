import asyncio
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from telegram.ext import ContextTypes
import sqlite3

from request_handler import get_cart_count_selenium

logger = logging.getLogger(__name__)

# Глобальные переменные для статистики проверки
STATE = {
    "last_request_time": None,
    "last_response": None
}


def background_check_sync():
    global STATE
    try:
        count = get_cart_count_selenium()
        STATE["last_request_time"] = datetime.now()
        STATE["last_response"] = { "count": count }
        logger.info(f"Получен ответ: {STATE['last_response']}")
        return count
    except Exception as e:
        logger.error(f"Ошибка проверки: {e}")
        return 0


def get_all_chat_ids():
    """Возвращает список chat_id всех пользователей из базы данных bot.db."""
    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id FROM users")
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"Ошибка получения chat_id из БД: {e}")
        return []


async def background_check(context: ContextTypes.DEFAULT_TYPE):
    """
    Фоновая функция, вызываемая периодически ботом.
    Получает JSON-ответ со страницы с билетами и, если count > 0, отправляет уведомление всем пользователям из БД.
    """
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        count = await loop.run_in_executor(pool, background_check_sync)
    print("got count", count)

    if count > 0:
        chat_ids = get_all_chat_ids()
        for chat_id in chat_ids:
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"Уведомление: В корзине {count} билетов!"
                )
                logger.info(f"Уведомление отправлено для chat_id {chat_id}.")
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления для chat_id {chat_id}: {e}")
