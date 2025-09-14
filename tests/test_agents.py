#!/usr/bin/env python3
"""
Железобетонные тесты для всех AI агентов системы HerZog
Используют реальные данные из проекта для проверки надежности
"""

import asyncio
import sys
import os
import json
import logging
from pathlib import Path

# Добавляем путь к основному коду
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_agents.work_packager import WorkPackager
from src.ai_agents.works_to_packages import WorksToPackagesAssigner
from src.ai_agents.counter import WorkVolumeCalculator
from src.ai_agents.scheduler_and_staffer import SchedulerAndStaffer

logger = logging.getLogger(__name__)

class AgentTester:
    """Класс для железобетонного тестирования агентов"""

    def __init__(self, test_project_path: str):
        self.test_project_path = test_project_path
        self.results = {}

    async def test_work_packager(self):
        """Тест агента work_packager"""
        logger.info("🧪 Тестирование work_packager")

        agent = WorkPackager()
        result = await agent.process(self.test_project_path)

        self.results['work_packager'] = {
            'success': result.get('success', False),
            'packages_created': result.get('packages_created', 0),
            'error': result.get('error')
        }

        if result.get('success'):
            logger.info(f"✅ work_packager: Создано {result.get('packages_created', 0)} пакетов")
        else:
            logger.error(f"❌ work_packager: {result.get('error')}")

    async def test_works_to_packages(self):
        """Тест агента works_to_packages"""
        logger.info("🧪 Тестирование works_to_packages")

        agent = WorksToPackagesAssigner(batch_size=25)  # Меньший батч для тестов
        result = await agent.process(self.test_project_path)

        self.results['works_to_packages'] = {
            'success': result.get('success', False),
            'works_processed': result.get('works_processed', 0),
            'batches_processed': result.get('batches_processed', 0),
            'error': result.get('error')
        }

        if result.get('success'):
            logger.info(f"✅ works_to_packages: Обработано {result.get('works_processed', 0)} работ в {result.get('batches_processed', 0)} батчах")
        else:
            logger.error(f"❌ works_to_packages: {result.get('error')}")

    async def test_counter(self):
        """Тест агента counter"""
        logger.info("🧪 Тестирование counter")

        agent = WorkVolumeCalculator()
        result = await agent.process(self.test_project_path)

        self.results['counter'] = {
            'success': result.get('success', False),
            'packages_calculated': result.get('packages_calculated', 0),
            'error': result.get('error')
        }

        if result.get('success'):
            logger.info(f"✅ counter: Рассчитано {result.get('packages_calculated', 0)} пакетов")
        else:
            logger.error(f"❌ counter: {result.get('error')}")

    async def test_scheduler_and_staffer(self):
        """Тест агента scheduler_and_staffer"""
        logger.info("🧪 Тестирование scheduler_and_staffer")

        agent = SchedulerAndStaffer(batch_size=8)  # Меньший батч для тестов
        result = await agent.process(self.test_project_path)

        self.results['scheduler_and_staffer'] = {
            'success': result.get('success', False),
            'packages_scheduled': result.get('packages_scheduled', 0),
            'workforce_valid': result.get('workforce_valid', False),
            'error': result.get('error')
        }

        if result.get('success'):
            logger.info(f"✅ scheduler_and_staffer: Запланировано {result.get('packages_scheduled', 0)} пакетов, персонал валиден: {result.get('workforce_valid')}")
        else:
            logger.error(f"❌ scheduler_and_staffer: {result.get('error')}")

    async def run_all_tests(self):
        """Запускает все тесты последовательно"""
        logger.info(f"🚀 Запуск железобетонных тестов на проекте: {self.test_project_path}")

        # Проверяем что проект существует
        if not os.path.exists(self.test_project_path):
            logger.error(f"❌ Тестовый проект не найден: {self.test_project_path}")
            return self.results

        # Проверяем true.json
        true_json_path = os.path.join(self.test_project_path, "true.json")
        if not os.path.exists(true_json_path):
            logger.error(f"❌ Файл true.json не найден: {true_json_path}")
            return self.results

        try:
            # Тестируем агенты по порядку
            await self.test_work_packager()
            await self.test_works_to_packages()
            await self.test_counter()
            await self.test_scheduler_and_staffer()

        except Exception as e:
            logger.error(f"❌ Критическая ошибка при тестировании: {e}")
            self.results['critical_error'] = str(e)

        # Выводим итоговую сводку
        self._print_summary()

        return self.results

    def _print_summary(self):
        """Выводит итоговую сводку тестов"""
        logger.info("📊 === ИТОГОВАЯ СВОДКА ТЕСТОВ ===")

        total_tests = 0
        passed_tests = 0

        for agent_name, result in self.results.items():
            if agent_name == 'critical_error':
                continue

            total_tests += 1
            status = "✅ ПРОШЕЛ" if result.get('success') else "❌ ПРОВАЛЕН"
            error_msg = f" ({result.get('error')})" if result.get('error') else ""

            logger.info(f"  {agent_name}: {status}{error_msg}")

            if result.get('success'):
                passed_tests += 1

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        logger.info(f"📈 Успешность: {passed_tests}/{total_tests} ({success_rate:.1f}%)")

        if 'critical_error' in self.results:
            logger.error(f"💥 Критическая ошибка: {self.results['critical_error']}")

async def main():
    """Главная функция для запуска тестов"""

    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Путь к тестовому проекту
    test_project_path = "/home/imort/Herzog_v3/projects/34975055/841377b4"

    # Создаем тестер и запускаем тесты
    tester = AgentTester(test_project_path)
    results = await tester.run_all_tests()

    # Возвращаем код выхода
    success_count = sum(1 for r in results.values() if isinstance(r, dict) and r.get('success'))
    total_count = len([r for r in results.values() if isinstance(r, dict) and 'success' in r])

    return 0 if success_count == total_count else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)