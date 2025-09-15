#!/usr/bin/env python3
"""
Упрощенный тест отдельных агентов на меньших данных
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
from src.ai_agents.works_to_packages import WorksToPackagesAssigner
from src.ai_agents.counter import WorkVolumeCalculator
from src.ai_agents.scheduler_and_staffer import SchedulerAndStaffer

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_salt_mechanism():
    """Тест механизма соли отдельно"""
    logger.info("🧪 Тестирование механизма соли")

    agent = WorkPackager()
    test_prompt = "Тестовый промпт для проверки соли"
    salted_prompt = agent._add_salt_to_prompt(test_prompt)

    logger.info(f"✅ Оригинальный промпт: {len(test_prompt)} символов")
    logger.info(f"✅ С солью: {len(salted_prompt)} символов")
    logger.info(f"✅ Соль добавлена: {'ID:' in salted_prompt and 'Контроль:' in salted_prompt}")

    return True

async def test_small_project():
    """Тест на проекте с минимальным количеством работ"""
    logger.info("🧪 Поиск проекта с малым количеством работ")

    # Ищем проекты
    projects_dir = "/home/imort/Herzog_v3/projects"
    small_project_path = None

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
                    if 10 <= len(work_items) <= 50:  # Ищем проект с 10-50 работами
                        small_project_path = project_path
                        logger.info(f"✅ Найден подходящий проект: {project_path}")
                        logger.info(f"✅ Количество работ: {len(work_items)}")
                        break

                except Exception as e:
                    continue

        if small_project_path:
            break

    if not small_project_path:
        logger.error("❌ Не найден проект с малым количеством работ")
        return False

    # Тестируем work_packager на малых данных
    logger.info("🧪 Тестирование work_packager на малых данных")
    agent = WorkPackager()
    result = await agent.process(small_project_path)

    if result.get('success'):
        logger.info(f"✅ work_packager: Создано {result.get('packages_created', 0)} пакетов")
        return True
    else:
        logger.error(f"❌ work_packager: {result.get('error')}")
        return False

async def main():
    """Главная функция тестирования"""
    logger.info("🚀 Запуск упрощенного тестирования агентов")

    # Тест 1: Механизм соли
    salt_ok = await test_salt_mechanism()

    # Тест 2: Малый проект
    small_project_ok = await test_small_project()

    # Итоги
    logger.info("📊 === ИТОГИ ТЕСТОВ ===")
    logger.info(f"Механизм соли: {'✅ OK' if salt_ok else '❌ FAIL'}")
    logger.info(f"Малый проект: {'✅ OK' if small_project_ok else '❌ FAIL'}")

    return 0 if (salt_ok and small_project_ok) else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)