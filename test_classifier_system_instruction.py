#!/usr/bin/env python3
"""
Тест gemini_classifier с новой архитектурой system_instruction
"""

import asyncio
import sys
import os
import json
import logging
from pathlib import Path

# Добавляем путь к основному коду
sys.path.insert(0, str(Path(__file__).parent))

from src.data_processing.gemini_classifier import classify_with_gemini

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_gemini_classifier_with_system_instruction():
    """Тест gemini_classifier с новой архитектурой"""
    logger.info("🧪 Тестирование gemini_classifier с system_instruction")

    # Создаем тестовые данные
    test_items = [
        {
            "id": "test_001",
            "code": "1.1-01",
            "name": "Погрузка строительных материалов"
        },
        {
            "id": "test_002",
            "code": "2.2-03",
            "name": "Цемент портландский М400"
        },
        {
            "id": "test_003",
            "code": "3.3-05",
            "name": "Монтаж металлоконструкций"
        },
        {
            "id": "test_004",
            "code": "4.4-07",
            "name": "Накладные расходы"
        }
    ]

    try:
        result = await classify_with_gemini(test_items)

        if result and len(result) > 0:
            logger.info("✅ Gemini classifier успешно классифицировал позиции!")
            for item_id, classification in result.items():
                logger.info(f"📝 {item_id}: {classification.get('classification')} - {classification.get('reasoning')}")

            return True
        else:
            logger.error("❌ Gemini classifier не вернул результатов")
            return False

    except Exception as e:
        logger.error(f"❌ Ошибка в gemini_classifier: {e}")
        return False

async def main():
    """Главная функция тестирования"""
    logger.info("🚀 Тестирование gemini_classifier с новой архитектурой")

    classifier_ok = await test_gemini_classifier_with_system_instruction()

    # Итоги
    logger.info("📊 === ИТОГИ ТЕСТИРОВАНИЯ ===")
    logger.info(f"Gemini Classifier: {'✅ OK' if classifier_ok else '❌ FAIL'}")

    return 0 if classifier_ok else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)