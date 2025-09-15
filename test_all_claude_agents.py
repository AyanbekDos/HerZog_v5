#!/usr/bin/env python3
"""
Тестирование всех 4 AI агентов с Claude API
Проверяем работу каждого агента отдельно с минимальными данными
"""

import asyncio
import json
import logging
import os
import tempfile
import shutil
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Минимальные тестовые данные для каждого этапа
TEST_DATA_STAGE_3 = {
    "meta": {
        "user_id": "test_user",
        "project_id": "test_project_claude",
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
            "work_packager": "группируй похожие работы",
            "counter": "считай точно",
            "scheduler": "равномерно распределяй"
        }
    },
    "work_items": [
        {
            "id": "work_001",
            "name": "Демонтаж перегородки",
            "classification": "work",
            "unit": "м²",
            "quantity": 15.0,
            "unit_cost": 500.0,
            "total_cost": 7500.0,
            "category": "demolition"
        },
        {
            "id": "work_002",
            "name": "Штукатурка стен",
            "classification": "work",
            "unit": "м²",
            "quantity": 30.0,
            "unit_cost": 800.0,
            "total_cost": 24000.0,
            "category": "finishing"
        },
        {
            "id": "work_003",
            "name": "Покраска стен",
            "classification": "work",
            "unit": "м²",
            "quantity": 30.0,
            "unit_cost": 300.0,
            "total_cost": 9000.0,
            "category": "finishing"
        }
    ]
}

async def test_work_packager():
    """Тест агента work_packager"""
    print("\n🎯 === ТЕСТ 1: WORK PACKAGER ===")

    try:
        # Сначала заменяем import на Claude
        from src.shared.claude_client import claude_client as gemini_client

        # Импортируем модули агента
        from src.ai_agents.work_packager import _load_prompt, _save_result

        # Создаем временный файл
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(TEST_DATA_STAGE_3, f, ensure_ascii=False, indent=2)
            temp_file = f.name

        print(f"📄 Временный файл: {temp_file}")

        # Загружаем промт
        prompt = _load_prompt()
        print(f"✅ Промт загружен: {len(prompt)} символов")

        # Готовим данные
        with open(temp_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        data_json = json.dumps(data, ensure_ascii=False, indent=2)
        user_prompt = f"Данные проекта для группировки работ в пакеты:\n\n{data_json}\n\nСгруппируй работы согласно инструкциям."

        print(f"🔄 Отправляем запрос к Claude...")

        # Генерируем ответ через Claude
        result = await gemini_client.generate_response(
            prompt=user_prompt,
            agent_name="work_packager",
            system_instruction=prompt,
            max_retries=3
        )

        if result['success']:
            print(f"✅ Work Packager успешен!")
            print(f"📊 Токены: {result['usage_metadata']['total_token_count']}")
            print(f"💰 Стоимость: ~${result.get('estimated_cost', 0):.4f}")

            # Проверяем структуру
            response = result['response']
            if isinstance(response, dict):
                packages_key = 'packages' if 'packages' in response else 'work_packages'
                packages = response.get(packages_key, [])
                print(f"📦 Создано пакетов: {len(packages)}")

                # Сохраняем результат для следующего агента
                output_data = data.copy()
                output_data['packages'] = packages
                output_data['meta']['current_stage'] = "4_packaged"

                next_file = temp_file.replace('.json', '_packaged.json')
                with open(next_file, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, ensure_ascii=False, indent=2)

                os.unlink(temp_file)
                return next_file, result.get('estimated_cost', 0)

        else:
            print(f"❌ Work Packager ошибка: {result['error']}")
            os.unlink(temp_file)
            return None, 0

    except Exception as e:
        print(f"💥 Критическая ошибка Work Packager: {e}")
        import traceback
        traceback.print_exc()
        return None, 0

async def test_works_to_packages(input_file):
    """Тест агента works_to_packages"""
    print("\n🎯 === ТЕСТ 2: WORKS TO PACKAGES ===")

    if not input_file:
        print("❌ Нет входного файла от work_packager")
        return None, 0

    try:
        from src.shared.claude_client import claude_client as gemini_client

        # Читаем промт
        prompt_path = "src/prompts/works_to_packages_prompt.txt"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read()

        print(f"✅ Промт загружен: {len(prompt)} символов")

        # Готовим данные
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        data_json = json.dumps(data, ensure_ascii=False, indent=2)
        user_prompt = f"Данные проекта для преобразования в пакеты:\n\n{data_json}"

        print(f"🔄 Отправляем запрос к Claude...")

        result = await gemini_client.generate_response(
            prompt=user_prompt,
            agent_name="works_to_packages",
            system_instruction=prompt,
            max_retries=3
        )

        if result['success']:
            print(f"✅ Works to Packages успешен!")
            print(f"📊 Токены: {result['usage_metadata']['total_token_count']}")
            print(f"💰 Стоимость: ~${result.get('estimated_cost', 0):.4f}")

            # Сохраняем для следующего агента
            response = result['response']
            next_file = input_file.replace('_packaged.json', '_works2packages.json')

            with open(next_file, 'w', encoding='utf-8') as f:
                json.dump(response, f, ensure_ascii=False, indent=2)

            os.unlink(input_file)
            return next_file, result.get('estimated_cost', 0)

        else:
            print(f"❌ Works to Packages ошибка: {result['error']}")
            return None, 0

    except Exception as e:
        print(f"💥 Критическая ошибка Works to Packages: {e}")
        import traceback
        traceback.print_exc()
        return None, 0

async def test_counter(input_file):
    """Тест агента counter"""
    print("\n🎯 === ТЕСТ 3: COUNTER ===")

    if not input_file:
        print("❌ Нет входного файла от works_to_packages")
        return None, 0

    try:
        from src.shared.claude_client import claude_client as gemini_client

        # Читаем промт
        prompt_path = "src/prompts/counter_prompt.txt"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read()

        print(f"✅ Промт загружен: {len(prompt)} символов")

        # Готовим данные
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        data_json = json.dumps(data, ensure_ascii=False, indent=2)
        user_prompt = f"Данные проекта для подсчета объемов:\n\n{data_json}"

        print(f"🔄 Отправляем запрос к Claude...")

        result = await gemini_client.generate_response(
            prompt=user_prompt,
            agent_name="counter",
            system_instruction=prompt,
            max_retries=3
        )

        if result['success']:
            print(f"✅ Counter успешен!")
            print(f"📊 Токены: {result['usage_metadata']['total_token_count']}")
            print(f"💰 Стоимость: ~${result.get('estimated_cost', 0):.4f}")

            # Сохраняем для следующего агента
            response = result['response']
            next_file = input_file.replace('_works2packages.json', '_counted.json')

            with open(next_file, 'w', encoding='utf-8') as f:
                json.dump(response, f, ensure_ascii=False, indent=2)

            os.unlink(input_file)
            return next_file, result.get('estimated_cost', 0)

        else:
            print(f"❌ Counter ошибка: {result['error']}")
            return None, 0

    except Exception as e:
        print(f"💥 Критическая ошибка Counter: {e}")
        import traceback
        traceback.print_exc()
        return None, 0

async def test_scheduler_and_staffer(input_file):
    """Тест агента scheduler_and_staffer"""
    print("\n🎯 === ТЕСТ 4: SCHEDULER AND STAFFER ===")

    if not input_file:
        print("❌ Нет входного файла от counter")
        return None, 0

    try:
        from src.shared.claude_client import claude_client as gemini_client

        # Читаем промт
        prompt_path = "src/prompts/scheduler_and_staffer_prompt.txt"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read()

        print(f"✅ Промт загружен: {len(prompt)} символов")

        # Готовим данные
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        data_json = json.dumps(data, ensure_ascii=False, indent=2)
        user_prompt = f"Данные проекта для планирования:\n\n{data_json}"

        print(f"🔄 Отправляем запрос к Claude...")

        result = await gemini_client.generate_response(
            prompt=user_prompt,
            agent_name="scheduler_and_staffer",
            system_instruction=prompt,
            max_retries=3
        )

        if result['success']:
            print(f"✅ Scheduler and Staffer успешен!")
            print(f"📊 Токены: {result['usage_metadata']['total_token_count']}")
            print(f"💰 Стоимость: ~${result.get('estimated_cost', 0):.4f}")

            # Финальный результат
            response = result['response']
            final_file = input_file.replace('_counted.json', '_scheduled.json')

            with open(final_file, 'w', encoding='utf-8') as f:
                json.dump(response, f, ensure_ascii=False, indent=2)

            print(f"📁 Финальный результат: {final_file}")

            os.unlink(input_file)
            return final_file, result.get('estimated_cost', 0)

        else:
            print(f"❌ Scheduler and Staffer ошибка: {result['error']}")
            return None, 0

    except Exception as e:
        print(f"💥 Критическая ошибка Scheduler and Staffer: {e}")
        import traceback
        traceback.print_exc()
        return None, 0

async def main():
    """Главная функция - тестируем все агенты последовательно"""
    print("🚀 === ТЕСТИРОВАНИЕ ВСЕХ CLAUDE АГЕНТОВ ===")
    print(f"🧪 Тестовый режим: {os.getenv('CLAUDE_TEST_MODE', 'true')}")

    total_cost = 0.0

    # Тест 1: Work Packager
    file1, cost1 = await test_work_packager()
    total_cost += cost1

    if not file1:
        print("\n❌ ТЕСТЫ ОСТАНОВЛЕНЫ НА WORK PACKAGER")
        return

    # Тест 2: Works to Packages
    file2, cost2 = await test_works_to_packages(file1)
    total_cost += cost2

    if not file2:
        print("\n❌ ТЕСТЫ ОСТАНОВЛЕНЫ НА WORKS TO PACKAGES")
        return

    # Тест 3: Counter
    file3, cost3 = await test_counter(file2)
    total_cost += cost3

    if not file3:
        print("\n❌ ТЕСТЫ ОСТАНОВЛЕНЫ НА COUNTER")
        return

    # Тест 4: Scheduler and Staffer
    file4, cost4 = await test_scheduler_and_staffer(file3)
    total_cost += cost4

    # Итоговая статистика
    print(f"\n🎯 === ИТОГОВЫЕ РЕЗУЛЬТАТЫ ===")
    if file4:
        print("✅ ВСЕ 4 АГЕНТА РАБОТАЮТ С CLAUDE!")
        print(f"💰 Общая стоимость: ~${total_cost:.4f}")
        print(f"📁 Финальный файл: {file4}")

        # Показываем немного результата
        try:
            with open(file4, 'r', encoding='utf-8') as f:
                final_data = json.load(f)

            packages = final_data.get('packages', [])
            print(f"📦 Финальных пакетов: {len(packages)}")

            if packages:
                print(f"📋 Первый пакет: {packages[0].get('name', 'Unnamed')}")

        except Exception as e:
            print(f"⚠️  Не удалось прочитать финальный результат: {e}")

    else:
        print("❌ НЕ ВСЕ АГЕНТЫ ПРОШЛИ ТЕСТ")
        print(f"💰 Потрачено на тесты: ~${total_cost:.4f}")

    print(f"\n🧹 Очистка временных файлов...")
    # Убираем временные файлы если остались
    for temp_file in [file1, file2, file3, file4]:
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
                print(f"🗑️  Удален: {temp_file}")
            except:
                pass

if __name__ == "__main__":
    # Устанавливаем тестовый режим
    os.environ['CLAUDE_TEST_MODE'] = 'true'

    asyncio.run(main())