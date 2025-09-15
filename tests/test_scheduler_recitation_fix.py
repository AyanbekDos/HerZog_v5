#!/usr/bin/env python3
"""
Тест исправления RECITATION ошибки в scheduler_and_staffer
"""

import asyncio
import json
import sys
import logging

sys.path.insert(0, '/home/imort/Herzog_v3')

from src.ai_agents.scheduler_and_staffer import SchedulerAndStaffer

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def test_scheduler_format_prompt():
    """Тестирует новое соление в scheduler_and_staffer"""
    print("\n🧪 Тестирование SchedulerAndStaffer с усиленным солением")

    agent = SchedulerAndStaffer()

    # Создаем тестовые данные (упрощенные)
    input_data = {
        'work_packages': [
            {
                'package_id': 'pkg_001',
                'package_name': 'Демонтажные работы',
                'total_volume': {'quantity': 150.0, 'unit': 'м²'},
                'source_works_count': 5,
                'complexity': 'medium'
            }
        ],
        'timeline_blocks': [
            {'week_id': 1, 'start_date': '2024-01-01', 'end_date': '2024-01-07'}
        ],
        'workforce_range': {'min': 10, 'max': 20},
        'user_directive': 'тестовая директива'
    }

    # Загружаем промпт
    prompt_template = agent._load_prompt()

    try:
        # Тестируем новый формат с солением
        system_instruction, user_prompt = agent._format_prompt(input_data, prompt_template)

        print(f"✅ System instruction получена: {len(system_instruction)} символов")
        print(f"✅ User prompt получен: {len(user_prompt)} символов")

        # Проверяем что user_prompt валидный JSON
        user_data = json.loads(user_prompt)

        # Проверяем наличие анти-RECITATION мета-данных
        assert '_meta' in user_data, "Отсутствует ключ '_meta' с анти-RECITATION данными"
        assert 'session_id' in user_data['_meta'], "Отсутствует session_id"
        assert 'timestamp' in user_data['_meta'], "Отсутствует timestamp"

        # Проверяем основные данные
        assert 'work_packages' in user_data, "Отсутствует ключ 'work_packages'"
        assert 'timeline_blocks' in user_data, "Отсутствует ключ 'timeline_blocks'"

        print("✅ Анти-RECITATION мета-данные добавлены")
        print(f"✅ Session ID: {user_data['_meta']['session_id']}")

        # Применяем соление к system_instruction
        salted_system_instruction = agent._add_salt_to_prompt(system_instruction)
        print(f"✅ Соленая system_instruction: {len(salted_system_instruction)} символов")

        # Проверяем что соление более агрессивное
        assert "TASK_ID" in salted_system_instruction, "Отсутствует TASK_ID в солении"
        assert "ANTI_RECITATION_SALT" in salted_system_instruction, "Отсутствует ANTI_RECITATION_SALT"

        print("🎉 SchedulerAndStaffer с усиленным солением готов!")
        return True

    except Exception as e:
        print(f"❌ Ошибка в тестировании: {e}")
        return False

async def main():
    """Главная функция тестирования"""
    print("🚀 Тест исправления RECITATION для scheduler_and_staffer")

    success = await test_scheduler_format_prompt()

    if success:
        print("\n✅ ИСПРАВЛЕНИЕ ГОТОВО К ТЕСТИРОВАНИЮ!")
        print("✅ Добавлено усиленное соление против RECITATION")
        print("✅ Добавлены мета-данные в user_prompt")
    else:
        print("\n❌ ЕСТЬ ПРОБЛЕМЫ В ИСПРАВЛЕНИИ!")

    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)