#!/usr/bin/env python3
"""
Тест новой архитектуры с system_instruction для предотвращения RECITATION
"""

import asyncio
import sys
import os
import json
import logging
from pathlib import Path

# Добавляем путь к основному коду
sys.path.insert(0, str(Path(__file__).parent))

from src.ai_agents.work_packager import WorkPackager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_work_packager_with_system_instruction():
    """Тест work_packager с новой архитектурой system_instruction"""
    logger.info("🧪 Тестирование WorkPackager с system_instruction архитектурой")

    # Ищем проект с малым количеством работ
    projects_dir = "/home/imort/Herzog_v3/projects"
    test_project_path = None

    for user_id in os.listdir(projects_dir):
        user_path = os.path.join(projects_dir, user_id)
        if not os.path.isdir(user_path):
            continue

        for project_id in os.listdir(user_path):
            project_path = os.path.join(user_path, project_id)
            truth_path = os.path.join(project_path, "true.json")

            if os.path.exists(truth_path):
                try:
                    with open(truth_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    work_items = data.get('source_work_items', [])
                    if 10 <= len(work_items) <= 30:  # Ищем проект с 10-30 работами
                        test_project_path = project_path
                        logger.info(f"✅ Найден тестовый проект: {project_path}")
                        logger.info(f"✅ Количество работ: {len(work_items)}")
                        break

                except Exception as e:
                    continue

        if test_project_path:
            break

    if not test_project_path:
        logger.error("❌ Не найден подходящий тестовый проект")
        return False

    # Тестируем work_packager с новой архитектурой
    agent = WorkPackager()
    result = await agent.process(test_project_path)

    if result.get('success'):
        logger.info(f"✅ WorkPackager успешно завершен!")
        logger.info(f"📊 Создано {result.get('work_packages_created', 0)} пакетов")

        # Проверяем, что файлы отладки созданы корректно
        debug_path = os.path.join(test_project_path, "4_packaged", "llm_input.json")
        if os.path.exists(debug_path):
            with open(debug_path, 'r', encoding='utf-8') as f:
                debug_data = json.load(f)

            if 'system_instruction' in debug_data and 'user_prompt' in debug_data:
                logger.info("✅ Структурированные данные отладки созданы корректно")
                logger.info(f"📝 System instruction: {len(debug_data['system_instruction'])} символов")
                logger.info(f"📝 User prompt: {len(debug_data['user_prompt'])} символов")
            else:
                logger.warning("⚠️ Структура отладочных данных некорректна")

        return True
    else:
        logger.error(f"❌ WorkPackager провален: {result.get('error')}")
        return False

async def test_simple_system_instruction():
    """Простой тест механизма system_instruction"""
    logger.info("🧪 Простой тест system_instruction")

    from src.shared.gemini_client import gemini_client

    system_instruction = "Ты - помощник программиста. Отвечай только в JSON формате."
    user_prompt = '{"question": "What is 2+2?"}'

    try:
        response = await gemini_client.generate_response(
            prompt=user_prompt,
            system_instruction=system_instruction
        )

        if response.get('success'):
            logger.info("✅ Простой тест system_instruction прошел успешно")
            return True
        else:
            logger.error(f"❌ Простой тест провален: {response.get('error')}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка при простом тесте: {e}")
        return False

async def main():
    """Главная функция тестирования"""
    logger.info("🚀 Тестирование новой архитектуры с system_instruction")

    # Тест 1: Простой механизм
    simple_test_ok = await test_simple_system_instruction()

    # Тест 2: WorkPackager
    work_packager_ok = await test_work_packager_with_system_instruction()

    # Итоги
    logger.info("📊 === ИТОГИ ТЕСТИРОВАНИЯ ===")
    logger.info(f"Простой тест: {'✅ OK' if simple_test_ok else '❌ FAIL'}")
    logger.info(f"WorkPackager: {'✅ OK' if work_packager_ok else '❌ FAIL'}")

    if simple_test_ok and work_packager_ok:
        logger.info("🎉 Новая архитектура работает успешно!")
        return 0
    else:
        logger.error("💥 Новая архитектура требует доработки")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)