#!/usr/bin/env python3
"""
HerZog v3.0 - Главная точка входа
Телеграм-бот для управления системой планирования строительства
"""

import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),  # Вывод в консоль
        logging.FileHandler('herzog_bot.log', encoding='utf-8')  # Вывод в файл
    ]
)

# Отключаем спам от внешних библиотек
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def main():
    """Основная функция запуска бота"""
    
    # Получаем токен бота
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в .env файле")
        return
    
    # Создаем приложение
    application = Application.builder().token(token).build()
    
    # Подключаем обработчики
    from src.telegram_bot.handlers import setup_handlers
    setup_handlers(application)
    
    logger.info("Запуск HerZog v3.0...")
    
    # Запускаем бота
    application.run_polling(allowed_updates=['message', 'callback_query'])

if __name__ == '__main__':
    main()