#!/usr/bin/env python3
"""
Полная диагностика всех агентов системы
Проверяет каждый агент отдельно и выявляет проблемы
"""

import asyncio
import os
import json
import traceback
from typing import Dict, Any

def print_separator(title: str):
    """Красивый разделитель"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def check_input_data_structure(agent_name: str, input_data: Dict):
    """Проверяет структуру входных данных для агента"""
    print(f"\n🔍 Проверка структуры input_data для {agent_name}:")

    if not input_data:
        print("❌ input_data пустой!")
        return False

    print(f"✅ Ключи в input_data: {list(input_data.keys())}")

    for key, value in input_data.items():
        if isinstance(value, list):
            print(f"  📋 {key}: список из {len(value)} элементов")
        elif isinstance(value, dict):
            print(f"  📚 {key}: словарь с {len(value)} ключами")
        else:
            print(f"  📝 {key}: {type(value).__name__} = {value}")

    return True

async def test_work_packager():
    """Тестирует work_packager агент"""
    print_separator("ТЕСТИРОВАНИЕ WORK_PACKAGER")

    try:
        # Импорты
        from src.ai_agents.work_packager import WorkPackager

        # Проект для тестирования
        project_path = "/home/imort/Herzog_v3/projects/34975055/b41f5b27"
        truth_path = os.path.join(project_path, "true.json")

        if not os.path.exists(truth_path):
            print(f"❌ Файл true.json не найден: {truth_path}")
            return False

        # Загружаем truth.json
        with open(truth_path, 'r', encoding='utf-8') as f:
            truth_data = json.load(f)

        print(f"✅ Загружен truth.json: {len(truth_data)} ключей")

        # Создаем агент и тестируем извлечение данных
        agent = WorkPackager()

        # Тестируем _extract_input_data
        input_data = agent._extract_input_data(truth_data)

        if not check_input_data_structure("work_packager", input_data):
            return False

        # Проверяем обязательные ключи
        required_keys = ['source_work_items', 'target_work_package_count', 'user_directive']
        missing_keys = [key for key in required_keys if key not in input_data]

        if missing_keys:
            print(f"❌ Отсутствуют ключи: {missing_keys}")
            return False

        print("✅ Все обязательные ключи присутствуют")

        # Тестируем создание debug_data
        try:
            debug_data = {
                "work_items": input_data['source_work_items'],
                "user_directive": input_data['user_directive'],
                "target_package_count": input_data['target_work_package_count'],
                "meta": {
                    "works_count": len(input_data['source_work_items']),
                    "target_packages": input_data['target_work_package_count']
                }
            }
            print("✅ debug_data создается успешно")
            print(f"📊 Работ: {debug_data['meta']['works_count']}, целевое количество пакетов: {debug_data['meta']['target_packages']}")
        except Exception as e:
            print(f"❌ Ошибка создания debug_data: {e}")
            return False

        print("🎉 work_packager прошел все проверки!")
        return True

    except Exception as e:
        print(f"❌ Критическая ошибка в work_packager: {e}")
        print(f"🔍 Трассировка: {traceback.format_exc()}")
        return False

async def test_counter():
    """Тестирует counter агент"""
    print_separator("ТЕСТИРОВАНИЕ COUNTER")

    try:
        from src.ai_agents.counter import WorkVolumeCalculator

        project_path = "/home/imort/Herzog_v3/projects/34975055/f77f33ea"  # Проект с данными counter
        truth_path = os.path.join(project_path, "true.json")

        if not os.path.exists(truth_path):
            print(f"❌ Файл true.json не найден: {truth_path}")
            return False

        with open(truth_path, 'r', encoding='utf-8') as f:
            truth_data = json.load(f)

        work_packages = truth_data.get('results', {}).get('work_packages', [])
        source_work_items = truth_data.get('source_work_items', [])

        print(f"✅ Пакетов работ: {len(work_packages)}")
        print(f"✅ Исходных работ: {len(source_work_items)}")

        # Проверяем что работы имеют package_id
        works_with_packages = [w for w in source_work_items if w.get('package_id')]
        print(f"✅ Работ с назначенными пакетами: {len(works_with_packages)}")

        if not works_with_packages:
            print("❌ Нет работ с назначенными пакетами!")
            return False

        print("🎉 counter данные готовы к обработке!")
        return True

    except Exception as e:
        print(f"❌ Критическая ошибка в counter: {e}")
        print(f"🔍 Трассировка: {traceback.format_exc()}")
        return False

async def test_works_to_packages():
    """Тестирует works_to_packages агент"""
    print_separator("ТЕСТИРОВАНИЕ WORKS_TO_PACKAGES")

    try:
        from src.ai_agents.works_to_packages import WorksToPackagesAssigner

        project_path = "/home/imort/Herzog_v3/projects/34975055/b41f5b27"  # Новый проект
        truth_path = os.path.join(project_path, "true.json")

        if not os.path.exists(truth_path):
            print(f"❌ Файл true.json не найден: {truth_path}")
            return False

        with open(truth_path, 'r', encoding='utf-8') as f:
            truth_data = json.load(f)

        work_packages = truth_data.get('results', {}).get('work_packages', [])
        source_work_items = truth_data.get('source_work_items', [])

        print(f"✅ Пакетов работ: {len(work_packages)}")
        print(f"✅ Исходных работ: {len(source_work_items)}")

        if not work_packages:
            print("❌ Нет пакетов работ! Сначала должен отработать work_packager")
            return False

        print("🎉 works_to_packages данные готовы к обработке!")
        return True

    except Exception as e:
        print(f"❌ Критическая ошибка в works_to_packages: {e}")
        print(f"🔍 Трассировка: {traceback.format_exc()}")
        return False

async def test_scheduler():
    """Тестирует scheduler_and_staffer агент"""
    print_separator("ТЕСТИРОВАНИЕ SCHEDULER_AND_STAFFER")

    try:
        from src.ai_agents.scheduler_and_staffer import SchedulerAndStaffer

        project_path = "/home/imort/Herzog_v3/projects/34975055/f77f33ea"  # Проект с полными данными
        truth_path = os.path.join(project_path, "true.json")

        if not os.path.exists(truth_path):
            print(f"❌ Файл true.json не найден: {truth_path}")
            return False

        with open(truth_path, 'r', encoding='utf-8') as f:
            truth_data = json.load(f)

        work_packages = truth_data.get('results', {}).get('work_packages', [])
        timeline_blocks = truth_data.get('timeline_blocks', [])

        print(f"✅ Пакетов работ: {len(work_packages)}")
        print(f"✅ Временных блоков: {len(timeline_blocks)}")

        # Проверяем что пакеты имеют volume_data
        packages_with_calcs = [p for p in work_packages if 'volume_data' in p]
        print(f"✅ Пакетов с расчетами: {len(packages_with_calcs)}")

        if not packages_with_calcs:
            print("❌ Пакеты не имеют volume_data! Сначала должен отработать counter")
            return False

        print("🎉 scheduler_and_staffer данные готовы к обработке!")
        return True

    except Exception as e:
        print(f"❌ Критическая ошибка в scheduler: {e}")
        print(f"🔍 Трассировка: {traceback.format_exc()}")
        return False

async def main():
    """Главная функция диагностики"""
    print_separator("🚀 ПОЛНАЯ ДИАГНОСТИКА АГЕНТОВ СИСТЕМЫ")

    results = {}

    # Тестируем каждый агент
    results['work_packager'] = await test_work_packager()
    results['counter'] = await test_counter()
    results['works_to_packages'] = await test_works_to_packages()
    results['scheduler'] = await test_scheduler()

    # Итоговый отчет
    print_separator("📊 ИТОГОВЫЙ ОТЧЕТ")

    success_count = sum(results.values())
    total_count = len(results)

    for agent, success in results.items():
        status = "✅ УСПЕШНО" if success else "❌ ОШИБКА"
        print(f"{agent:20} {status}")

    print(f"\n🎯 ИТОГО: {success_count}/{total_count} агентов готовы к работе")

    if success_count == total_count:
        print("🎉 ВСЕ АГЕНТЫ РАБОТАЮТ КОРРЕКТНО!")
    else:
        print("⚠️  ЕСТЬ ПРОБЛЕМЫ! Смотри детали выше.")

if __name__ == "__main__":
    asyncio.run(main())