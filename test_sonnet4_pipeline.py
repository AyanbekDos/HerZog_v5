#!/usr/bin/env python3
"""
Тестирование полного пайплайна с Sonnet 4 и всеми исправлениями
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime

# Добавляем путь к модулям
sys.path.insert(0, os.path.abspath('.'))

from src.shared.claude_client import claude_client
from src.ai_agents.work_packager import run_work_packager
from src.ai_agents.works_to_packages import run_works_to_packages
from src.ai_agents.counter import run_counter
from src.ai_agents.scheduler_and_staffer import run_scheduler_and_staffer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_claude_client():
    """Тест базовой работы Claude клиента"""
    logger.info("🧪 Тестирую Claude клиент...")

    # Проверяем настройки
    logger.info(f"🔧 Тестовый режим: {claude_client.test_mode}")
    logger.info(f"🤖 Модель по умолчанию: {claude_client.model_name}")

    # Простой тест API
    test_prompt = """Верни JSON: {"test": "success", "message": "Sonnet 4 работает!"}"""

    result = await claude_client.generate_response(
        prompt=test_prompt,
        agent_name="test",
        system_instruction="Ты тестовый помощник. Возвращай только валидный JSON."
    )

    if result.get('success'):
        logger.info(f"✅ Claude API работает: {result.get('response', {}).get('message', 'OK')}")
        return True
    else:
        logger.error(f"❌ Claude API не работает: {result.get('error')}")
        return False

async def test_project_agents(project_path: str):
    """Тест всех агентов на реальном проекте"""
    if not os.path.exists(project_path):
        logger.error(f"❌ Проект не найден: {project_path}")
        return False

    logger.info(f"🧪 Тестирую агенты на проекте: {project_path}")

    try:
        # 1. Work Packager
        logger.info("🤖 Запуск work_packager...")
        result1 = await run_work_packager(project_path)
        if not result1.get('success', False):
            logger.error(f"❌ work_packager failed: {result1.get('error')}")
            return False
        logger.info(f"✅ work_packager: {result1.get('packages_created', 0)} пакетов")

        # 2. Works to Packages
        logger.info("🤖 Запуск works_to_packages...")
        result2 = await run_works_to_packages(project_path)
        if not result2.get('success', False):
            logger.error(f"❌ works_to_packages failed: {result2.get('error')}")
            return False
        logger.info(f"✅ works_to_packages: {result2.get('works_processed', 0)} работ обработано")

        # 3. Counter
        logger.info("🤖 Запуск counter...")
        result3 = await run_counter(project_path)
        if not result3.get('success', False):
            logger.error(f"❌ counter failed: {result3.get('error')}")
            return False
        logger.info(f"✅ counter: {result3.get('packages_processed', 0)} пакетов посчитано")

        # 4. Scheduler and Staffer
        logger.info("🤖 Запуск scheduler_and_staffer...")
        result4 = await run_scheduler_and_staffer(project_path)
        if not result4.get('success', False):
            logger.error(f"❌ scheduler_and_staffer failed: {result4.get('error')}")
            return False
        logger.info(f"✅ scheduler_and_staffer: {result4.get('packages_scheduled', 0)} пакетов запланировано")

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка тестирования агентов: {e}")
        return False

def test_true_json_enrichment(project_path: str):
    """Проверка что true.json обогащается правильно"""
    truth_path = os.path.join(project_path, "true.json")

    if not os.path.exists(truth_path):
        logger.error(f"❌ true.json не найден: {truth_path}")
        return False

    with open(truth_path, 'r', encoding='utf-8') as f:
        truth_data = json.load(f)

    # Проверяем project_name и source_file_name
    metadata = truth_data.get('metadata', {})
    project_name = metadata.get('project_name', '')
    source_file_name = metadata.get('source_file_name', '')

    logger.info(f"📄 Имя проекта: '{project_name}'")
    logger.info(f"📄 Исходный файл: '{source_file_name}'")

    if project_name == "Безымянный проект":
        logger.warning("⚠️ Проект всё ещё безымянный")
    if source_file_name == "estimate.xlsx":
        logger.warning("⚠️ Имя файла всё ещё дефолтное")

    # Проверяем обоснования планирования
    work_packages = truth_data.get('results', {}).get('work_packages', [])
    reasoning_count = 0

    for package in work_packages:
        if 'scheduling_reasoning' in package:
            reasoning_count += 1
            reasoning = package['scheduling_reasoning']
            logger.info(f"📋 Пакет {package.get('package_id')}: {len(reasoning)} обоснований")

    if reasoning_count == 0:
        logger.error("❌ Обоснования планирования не найдены в true.json")
        return False
    else:
        logger.info(f"✅ Найдено {reasoning_count} пакетов с обоснованиями планирования")

    return True

async def main():
    """Основная функция тестирования"""
    logger.info("🚀 Запуск тестирования Sonnet 4 пайплайна")
    logger.info(f"📅 Время: {datetime.now()}")

    # 1. Тест Claude клиента
    if not await test_claude_client():
        logger.error("❌ Claude клиент не работает, останавливаю тесты")
        return

    # 2. Проверяем доступные проекты
    projects_dir = "projects"
    if not os.path.exists(projects_dir):
        logger.error("❌ Папка projects не найдена")
        return

    # Найдем последний проект
    test_project = None
    for user_dir in os.listdir(projects_dir):
        user_path = os.path.join(projects_dir, user_dir)
        if os.path.isdir(user_path):
            for project_dir in os.listdir(user_path):
                project_path = os.path.join(user_path, project_dir)
                if os.path.isdir(project_path) and os.path.exists(os.path.join(project_path, "true.json")):
                    test_project = project_path

    if not test_project:
        logger.error("❌ Не найден проект с true.json для тестирования")
        return

    logger.info(f"🎯 Тестовый проект: {test_project}")

    # 3. Тест агентов
    if await test_project_agents(test_project):
        logger.info("✅ Все агенты работают")

        # 4. Проверка обогащения true.json
        if test_true_json_enrichment(test_project):
            logger.info("✅ true.json правильно обогащается")
        else:
            logger.error("❌ Проблемы с обогащением true.json")
    else:
        logger.error("❌ Проблемы с агентами")

    # 5. Статистика клиента
    stats = claude_client.get_usage_stats()
    logger.info(f"💰 Статистика использования Claude:")
    logger.info(f"   Запросов: {stats['total_requests']}")
    logger.info(f"   Входных токенов: {stats['total_input_tokens']}")
    logger.info(f"   Выходных токенов: {stats['total_output_tokens']}")
    logger.info(f"   Примерная стоимость: ${stats['estimated_cost']:.4f}")

    logger.info("🎉 Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(main())