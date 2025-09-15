#!/usr/bin/env python3
"""
Тест одного AI агента с Claude вместо Gemini
Берем work_packager как самый простой для начала
"""

import asyncio
import json
import logging
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Тестовые данные - очень маленький набор для экономии токенов
MINIMAL_TEST_DATA = {
    "meta": {
        "user_id": "test_user",
        "project_id": "test_project",
        "current_stage": "3_prepared"
    },
    "directives": {
        "target_package_count": 3,  # Очень мало пакетов
        "project_timeline": {
            "start_date": "2024-01-01",
            "end_date": "2024-02-01",
            "total_weeks": 4
        },
        "workforce": {"min": 5, "max": 10, "average": 8},
        "special_instructions": {
            "work_packager": "группируй похожие работы"
        }
    },
    "work_items": [
        {
            "id": "work_001",
            "name": "Демонтаж перегородки",
            "classification": "work",
            "unit": "м²",
            "quantity": 10.5,
            "unit_cost": 500.0,
            "total_cost": 5250.0,
            "category": "demolition"
        },
        {
            "id": "work_002",
            "name": "Штукатурка стен",
            "classification": "work",
            "unit": "м²",
            "quantity": 25.0,
            "unit_cost": 800.0,
            "total_cost": 20000.0,
            "category": "finishing"
        },
        {
            "id": "work_003",
            "name": "Покраска стен",
            "classification": "work",
            "unit": "м²",
            "quantity": 25.0,
            "unit_cost": 300.0,
            "total_cost": 7500.0,
            "category": "finishing"
        }
    ]
}

async def test_work_packager_with_claude():
    """Тест work_packager агента с Claude API"""
    print("🧪 === ТЕСТ WORK PACKAGER С CLAUDE ===")

    # Включаем тестовый режим для экономии
    os.environ['CLAUDE_TEST_MODE'] = 'true'

    try:
        # Создаем модифицированный work_packager, который использует Claude
        from src.shared.claude_client import ClaudeClient

        # Читаем промт для work_packager
        prompt_path = "src/prompts/work_packager_prompt.txt"
        if not os.path.exists(prompt_path):
            print(f"❌ Промт файл не найден: {prompt_path}")
            return False

        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_instruction = f.read()

        print(f"✅ Промт загружен: {len(system_instruction)} символов")

        # Создаем клиент и готовим данные
        client = ClaudeClient()
        test_data_json = json.dumps(MINIMAL_TEST_DATA, ensure_ascii=False, indent=2)

        print(f"✅ Тестовые данные подготовлены: {len(test_data_json)} символов")
        print(f"📊 Работ для группировки: {len(MINIMAL_TEST_DATA['work_items'])}")

        # Формируем промт для агента
        user_prompt = f"""
Данные проекта для группировки работ в пакеты:

{test_data_json}

Сгруппируй работы в логические пакеты согласно инструкциям.
"""

        print(f"\n🔄 Отправляем запрос к Claude...")
        print(f"🧪 Тестовый режим: {client.test_mode}")
        print(f"🎯 Модель: {client.model_name}")

        # Отправляем запрос
        result = await client.generate_response(
            prompt=user_prompt,
            agent_name="work_packager",
            system_instruction=system_instruction,
            max_retries=3
        )

        if result['success']:
            print("\n✅ Work Packager с Claude работает!")
            print(f"🤖 Модель: {result['model_used']}")
            print(f"📊 Токены: {result['usage_metadata']['total_token_count']}")
            print(f"💰 Стоимость: ~${result.get('estimated_cost', 0):.4f}")

            # Проверяем структуру ответа
            response = result['response']
            if isinstance(response, dict) and 'packages' in response:
                packages = response['packages']
                print(f"📦 Создано пакетов: {len(packages)}")

                for i, pkg in enumerate(packages[:2], 1):  # Показываем первые 2
                    print(f"   {i}. {pkg.get('name', 'Unnamed')} ({pkg.get('category', 'No category')})")

                print(f"\n📋 Полный ответ (первые 500 символов):")
                print(json.dumps(response, ensure_ascii=False, indent=2)[:500] + "...")

            else:
                print(f"⚠️  Неожиданная структура ответа: {type(response)}")
                print(f"📋 Ответ: {str(response)[:200]}...")

            # Статистика
            stats = client.get_usage_stats()
            print(f"\n📈 === ОБЩАЯ СТАТИСТИКА ===")
            print(f"Входные токены: {stats['total_input_tokens']}")
            print(f"Выходные токены: {stats['total_output_tokens']}")
            print(f"Общая стоимость: ~${stats['estimated_cost']:.4f}")

            return True

        else:
            print(f"❌ Ошибка work_packager: {result['error']}")
            if 'raw_text' in result and result['raw_text']:
                print(f"📋 Сырой ответ: {result['raw_text'][:300]}...")
            return False

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

async def compare_with_gemini():
    """Опционально сравним с Gemini для понимания разницы"""
    print("\n🔄 === СРАВНЕНИЕ С GEMINI (опционально) ===")

    try:
        from src.ai_agents.work_packager import run_work_packager
        import tempfile
        import os

        # Создаем временный файл с тестовыми данными
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(MINIMAL_TEST_DATA, f, ensure_ascii=False, indent=2)
            temp_file = f.name

        print(f"📄 Временный файл с данными: {temp_file}")

        # Запускаем оригинальный work_packager с Gemini
        print("🔄 Запуск Gemini work_packager...")
        gemini_result = await run_work_packager(temp_file)

        if gemini_result and gemini_result.get('success'):
            print("✅ Gemini work_packager тоже работает")
            print(f"📊 Создано пакетов: {len(gemini_result.get('result', {}).get('packages', []))}")
        else:
            print("❌ Gemini work_packager не работает или есть ошибки")
            if gemini_result:
                print(f"Ошибка: {gemini_result.get('error', 'Unknown')}")

        # Удаляем временный файл
        os.unlink(temp_file)

    except Exception as e:
        print(f"⚠️  Не удалось сравнить с Gemini: {e}")

if __name__ == "__main__":
    async def main():
        print("🚀 Тестируем AI агент с Claude...")

        success = await test_work_packager_with_claude()

        if success:
            print("\n✅ АГЕНТ С CLAUDE РАБОТАЕТ!")
            # await compare_with_gemini()  # Раскомментируй для сравнения
        else:
            print("\n❌ АГЕНТ С CLAUDE НЕ РАБОТАЕТ!")

        print(f"\n💡 Готово! Агент протестирован на минимальных данных.")

    asyncio.run(main())