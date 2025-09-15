#!/usr/bin/env python3
"""
Упрощенное тестирование всех 4 AI агентов с Claude API
Использует публичные функции агентов
"""

import asyncio
import json
import logging
import os
import tempfile
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Минимальные тестовые данные
TEST_DATA = {
    "meta": {
        "user_id": "test_user",
        "project_id": "test_claude_agents",
        "current_stage": "3_prepared"
    },
    "directives": {
        "target_package_count": 3,
        "project_timeline": {
            "start_date": "2024-01-01",
            "end_date": "2024-02-01",
            "total_weeks": 4
        },
        "workforce": {"min": 5, "max": 10, "average": 8},
        "special_instructions": {
            "work_packager": "создай 3 пакета работ",
            "counter": "считай объемы точно",
            "scheduler": "равномерно распределяй по неделям"
        }
    },
    "timeline_blocks": [
        {"week_id": 1, "start_date": "2024-01-01", "end_date": "2024-01-07", "days_count": 7},
        {"week_id": 2, "start_date": "2024-01-08", "end_date": "2024-01-14", "days_count": 7},
        {"week_id": 3, "start_date": "2024-01-15", "end_date": "2024-01-21", "days_count": 7},
        {"week_id": 4, "start_date": "2024-01-22", "end_date": "2024-01-28", "days_count": 7}
    ],
    "work_items": [
        {
            "id": "work_001",
            "name": "Демонтаж перегородки",
            "classification": "work",
            "unit": "м²",
            "quantity": 20.0,
            "unit_cost": 500.0,
            "total_cost": 10000.0,
            "category": "demolition"
        },
        {
            "id": "work_002",
            "name": "Штукатурка стен",
            "classification": "work",
            "unit": "м²",
            "quantity": 40.0,
            "unit_cost": 800.0,
            "total_cost": 32000.0,
            "category": "finishing"
        },
        {
            "id": "work_003",
            "name": "Покраска стен",
            "classification": "work",
            "unit": "м²",
            "quantity": 40.0,
            "unit_cost": 300.0,
            "total_cost": 12000.0,
            "category": "finishing"
        }
    ]
}

async def test_agent(agent_name, agent_function, input_file, test_number):
    """Универсальная функция для тестирования агента"""
    print(f"\n🎯 === ТЕСТ {test_number}: {agent_name.upper()} ===")

    try:
        start_time = asyncio.get_event_loop().time()

        # Запускаем агент
        result = await agent_function(input_file)

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        if result and result.get('success'):
            print(f"✅ {agent_name} успешен!")
            print(f"⏱️  Время выполнения: {duration:.2f} сек")

            # Показываем результат
            if 'result' in result and result['result']:
                data = result['result']
                if isinstance(data, dict):
                    if 'packages' in data:
                        print(f"📦 Создано пакетов: {len(data['packages'])}")
                    if 'work_items' in data:
                        print(f"📋 Обработано работ: {len(data['work_items'])}")
                    if 'timeline_blocks' in data:
                        print(f"📅 Временных блоков: {len(data['timeline_blocks'])}")

            # Логирование через Claude
            try:
                from src.shared.claude_client import claude_client
                stats = claude_client.get_usage_stats()
                print(f"💰 Общая стоимость Claude: ~${stats['estimated_cost']:.4f}")
                print(f"📊 Общие токены: {stats['total_input_tokens'] + stats['total_output_tokens']}")
            except:
                pass

            return True, result.get('result')

        else:
            error = result.get('error', 'Unknown error') if result else 'No result'
            print(f"❌ {agent_name} ошибка: {error}")
            return False, None

    except Exception as e:
        print(f"💥 Критическая ошибка {agent_name}: {e}")
        import traceback
        traceback.print_exc()
        return False, None

async def main():
    """Главная функция - тестируем все агенты"""
    print("🚀 === ТЕСТИРОВАНИЕ ВСЕХ CLAUDE АГЕНТОВ ===")
    print(f"🧪 Тестовый режим: {os.getenv('CLAUDE_TEST_MODE', 'true')}")

    # Сбрасываем статистику Claude
    try:
        from src.shared.claude_client import claude_client
        claude_client.reset_usage_stats()
    except:
        pass

    # Создаем временный файл с тестовыми данными
    temp_dir = tempfile.mkdtemp(prefix="claude_test_")
    temp_file = os.path.join(temp_dir, "truth.json")

    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(TEST_DATA, f, ensure_ascii=False, indent=2)

        print(f"📄 Тестовые данные: {temp_file}")

        # Тест 1: Work Packager
        try:
            from src.ai_agents.work_packager import run_work_packager
            success1, result1 = await test_agent("work_packager", run_work_packager, temp_file, 1)
        except ImportError as e:
            print(f"❌ Не удалось импортировать work_packager: {e}")
            success1 = False

        if not success1:
            print("\n❌ ТЕСТЫ ОСТАНОВЛЕНЫ НА WORK PACKAGER")
            return

        # Сохраняем результат для следующего агента
        stage4_file = os.path.join(temp_dir, "stage4_packaged.json")
        with open(stage4_file, 'w', encoding='utf-8') as f:
            json.dump(result1, f, ensure_ascii=False, indent=2)

        # Тест 2: Works to Packages
        try:
            from src.ai_agents.works_to_packages import run_works_to_packages
            success2, result2 = await test_agent("works_to_packages", run_works_to_packages, stage4_file, 2)
        except ImportError as e:
            print(f"❌ Не удалось импортировать works_to_packages: {e}")
            success2 = False

        if not success2:
            print("\n❌ ТЕСТЫ ОСТАНОВЛЕНЫ НА WORKS TO PACKAGES")
            return

        # Сохраняем результат для следующего агента
        stage5_file = os.path.join(temp_dir, "stage5_works2packages.json")
        with open(stage5_file, 'w', encoding='utf-8') as f:
            json.dump(result2, f, ensure_ascii=False, indent=2)

        # Тест 3: Counter
        try:
            from src.ai_agents.counter import run_counter
            success3, result3 = await test_agent("counter", run_counter, stage5_file, 3)
        except ImportError as e:
            print(f"❌ Не удалось импортировать counter: {e}")
            success3 = False

        if not success3:
            print("\n❌ ТЕСТЫ ОСТАНОВЛЕНЫ НА COUNTER")
            return

        # Сохраняем результат для следующего агента
        stage6_file = os.path.join(temp_dir, "stage6_counted.json")
        with open(stage6_file, 'w', encoding='utf-8') as f:
            json.dump(result3, f, ensure_ascii=False, indent=2)

        # Тест 4: Scheduler and Staffer
        try:
            from src.ai_agents.scheduler_and_staffer import run_scheduler_and_staffer
            success4, result4 = await test_agent("scheduler_and_staffer", run_scheduler_and_staffer, stage6_file, 4)
        except ImportError as e:
            print(f"❌ Не удалось импортировать scheduler_and_staffer: {e}")
            success4 = False

        # Итоговые результаты
        print(f"\n🎯 === ИТОГОВЫЕ РЕЗУЛЬТАТЫ ===")

        total_tests = 4
        passed_tests = sum([success1, success2, success3, success4])

        print(f"✅ Пройдено тестов: {passed_tests}/{total_tests}")

        if passed_tests == total_tests:
            print("🎉 ВСЕ АГЕНТЫ РАБОТАЮТ С CLAUDE!")
        else:
            print("⚠️  НЕ ВСЕ АГЕНТЫ ПРОШЛИ ТЕСТ")

        # Финальная статистика Claude
        try:
            from src.shared.claude_client import claude_client
            stats = claude_client.get_usage_stats()
            print(f"\n💰 === ФИНАЛЬНАЯ СТАТИСТИКА CLAUDE ===")
            print(f"Всего запросов: {stats['total_requests']}")
            print(f"Входные токены: {stats['total_input_tokens']}")
            print(f"Выходные токены: {stats['total_output_tokens']}")
            print(f"Общая стоимость: ~${stats['estimated_cost']:.4f}")
        except Exception as e:
            print(f"⚠️  Не удалось получить статистику Claude: {e}")

        if success4 and result4:
            print(f"\n📋 === ФИНАЛЬНЫЙ РЕЗУЛЬТАТ ===")
            final_file = os.path.join(temp_dir, "final_result.json")
            with open(final_file, 'w', encoding='utf-8') as f:
                json.dump(result4, f, ensure_ascii=False, indent=2)
            print(f"📁 Сохранено в: {final_file}")

            # Показываем краткий обзор
            if isinstance(result4, dict):
                if 'packages' in result4:
                    packages = result4['packages']
                    print(f"📦 Финальных пакетов: {len(packages)}")
                    if packages:
                        print(f"📋 Первый пакет: {packages[0].get('name', 'Unnamed')}")

    finally:
        # Очистка временных файлов
        import shutil
        try:
            shutil.rmtree(temp_dir)
            print(f"\n🧹 Временные файлы очищены: {temp_dir}")
        except:
            print(f"\n⚠️  Не удалось очистить: {temp_dir}")

if __name__ == "__main__":
    # Устанавливаем тестовый режим
    os.environ['CLAUDE_TEST_MODE'] = 'true'

    asyncio.run(main())