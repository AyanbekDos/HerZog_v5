#!/usr/bin/env python3
"""
Тестирование отрефакторенных AI-агентов для проверки работы pattern "system_instruction + user_prompt"
"""

import asyncio
import json
import os
import sys
import logging
from typing import Dict, Any

# Добавляем путь к проекту
sys.path.insert(0, '/home/imort/Herzog_v3')

from src.ai_agents.counter import WorkVolumeCalculator
from src.ai_agents.works_to_packages import WorksToPackagesAssigner
from src.ai_agents.scheduler_and_staffer import SchedulerAndStaffer

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_counter_format_prompt():
    """Тестирует новый _format_prompt метод агента Counter"""
    print("\n🧪 Тестирование Counter._format_prompt")

    agent = WorkVolumeCalculator()

    # Создаем тестовые данные
    input_data = {
        'package': {
            'package_id': 'pkg_001',
            'name': 'Демонтажные работы'
        },
        'works': [
            {'id': 'work_001', 'name': 'Демонтаж перегородок', 'unit': 'м²', 'quantity': 45.5}
        ],
        'user_directive': 'считай площади точно'
    }

    # Загружаем промпт
    prompt_template = agent._load_prompt()

    try:
        # Тестируем новый формат возврата (кортеж)
        system_instruction, user_prompt = agent._format_prompt(input_data, prompt_template)

        print(f"✅ System instruction получена: {len(system_instruction)} символов")
        print(f"✅ User prompt получен: {len(user_prompt)} символов")

        # Проверяем что user_prompt валидный JSON
        user_data = json.loads(user_prompt)

        assert 'package' in user_data, "Отсутствует ключ 'package' в user_prompt"
        assert 'works' in user_data, "Отсутствует ключ 'works' в user_prompt"
        assert 'user_directive' in user_data, "Отсутствует ключ 'user_directive' в user_prompt"

        print("✅ Counter._format_prompt работает корректно")
        return True

    except Exception as e:
        print(f"❌ Ошибка в Counter._format_prompt: {e}")
        return False

async def test_works_to_packages_format_prompt():
    """Тестирует новый _format_prompt метод агента WorksToPackagesAssigner"""
    print("\n🧪 Тестирование WorksToPackagesAssigner._format_prompt")

    agent = WorksToPackagesAssigner()

    # Создаем тестовые данные
    input_data = {
        'work_packages': [
            {'package_id': 'pkg_001', 'name': 'Демонтажные работы'}
        ],
        'batch_works': [
            {'id': 'work_001', 'name': 'Демонтаж перегородок', 'code': '01-01-001'}
        ],
        'batch_number': 1
    }

    # Загружаем промпт
    prompt_template = agent._load_prompt()

    try:
        # Тестируем новый формат возврата (кортеж)
        system_instruction, user_prompt = agent._format_prompt(input_data, prompt_template)

        print(f"✅ System instruction получена: {len(system_instruction)} символов")
        print(f"✅ User prompt получен: {len(user_prompt)} символов")

        # Проверяем что user_prompt валидный JSON
        user_data = json.loads(user_prompt)

        assert 'work_packages' in user_data, "Отсутствует ключ 'work_packages' в user_prompt"
        assert 'batch_works' in user_data, "Отсутствует ключ 'batch_works' в user_prompt"
        assert 'batch_number' in user_data, "Отсутствует ключ 'batch_number' в user_prompt"

        print("✅ WorksToPackagesAssigner._format_prompt работает корректно")
        return True

    except Exception as e:
        print(f"❌ Ошибка в WorksToPackagesAssigner._format_prompt: {e}")
        return False

async def test_scheduler_format_prompt():
    """Тестирует новый _format_prompt метод агента SchedulerAndStaffer"""
    print("\n🧪 Тестирование SchedulerAndStaffer._format_prompt")

    agent = SchedulerAndStaffer()

    # Создаем тестовые данные
    input_data = {
        'work_packages': [
            {
                'package_id': 'pkg_001',
                'package_name': 'Демонтажные работы',
                'total_volume': {'quantity': 150.0, 'unit': 'м²'}
            }
        ],
        'timeline_blocks': [
            {'week_id': 1, 'start_date': '2024-01-01', 'end_date': '2024-01-07'}
        ],
        'workforce_range': {'min': 10, 'max': 20},
        'user_directive': 'первый месяц только демонтаж'
    }

    # Загружаем промпт
    prompt_template = agent._load_prompt()

    try:
        # Тестируем новый формат возврата (кортеж)
        system_instruction, user_prompt = agent._format_prompt(input_data, prompt_template)

        print(f"✅ System instruction получена: {len(system_instruction)} символов")
        print(f"✅ User prompt получен: {len(user_prompt)} символов")

        # Проверяем что user_prompt валидный JSON
        user_data = json.loads(user_prompt)

        assert 'work_packages' in user_data, "Отсутствует ключ 'work_packages' в user_prompt"
        assert 'timeline_blocks' in user_data, "Отсутствует ключ 'timeline_blocks' в user_prompt"
        assert 'workforce_range' in user_data, "Отсутствует ключ 'workforce_range' в user_prompt"
        assert 'user_directive' in user_data, "Отсутствует ключ 'user_directive' в user_prompt"

        print("✅ SchedulerAndStaffer._format_prompt работает корректно")
        return True

    except Exception as e:
        print(f"❌ Ошибка в SchedulerAndStaffer._format_prompt: {e}")
        return False

async def main():
    """Главная функция тестирования"""
    print("🚀 Начинаем тестирование отрефакторенных агентов")

    results = []

    # Тестируем каждый агент
    results.append(await test_counter_format_prompt())
    results.append(await test_works_to_packages_format_prompt())
    results.append(await test_scheduler_format_prompt())

    # Выводим результаты
    print("\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"✅ Пройдено тестов: {sum(results)}")
    print(f"❌ Провалено тестов: {len(results) - sum(results)}")

    if all(results):
        print("\n🎉 ВСЕ АГЕНТЫ ОТРЕФАКТОРЕНЫ УСПЕШНО!")
        print("✅ Паттерн 'system_instruction + user_prompt' применен ко всем агентам")
        print("✅ Ошибки RECITATION должны быть устранены")
    else:
        print("\n⚠️ ЕСТЬ ПРОБЛЕМЫ В РЕФАКТОРИНГЕ!")
        print("❌ Некоторые агенты требуют доработки")
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)