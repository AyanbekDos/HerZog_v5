#!/usr/bin/env python3
"""
Отладка work_packager агента с Claude
Смотрим что именно возвращает Claude
"""

import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Простейшие данные
MINIMAL_DATA = {
    "meta": {
        "user_id": "debug_user",
        "project_id": "debug_project",
        "current_stage": "3_prepared"
    },
    "directives": {
        "target_package_count": 2,
        "project_timeline": {"start_date": "2024-01-01", "end_date": "2024-01-14", "total_weeks": 2},
        "workforce": {"min": 3, "max": 6, "average": 4},
        "special_instructions": {"work_packager": "создай 2 пакета"}
    },
    "timeline_blocks": [
        {"week_id": 1, "start_date": "2024-01-01", "end_date": "2024-01-07", "days_count": 7},
        {"week_id": 2, "start_date": "2024-01-08", "end_date": "2024-01-14", "days_count": 7}
    ],
    "packages": [],
    "work_items": [
        {
            "id": "work_001",
            "name": "Демонтаж",
            "classification": "work",
            "unit": "м²",
            "quantity": 10.0,
            "unit_cost": 500.0,
            "total_cost": 5000.0,
            "category": "demolition"
        },
        {
            "id": "work_002",
            "name": "Штукатурка",
            "classification": "work",
            "unit": "м²",
            "quantity": 20.0,
            "unit_cost": 800.0,
            "total_cost": 16000.0,
            "category": "finishing"
        }
    ]
}

async def debug_work_packager():
    """Отладка work_packager с логированием ответа Claude"""
    print("🔍 === ОТЛАДКА WORK PACKAGER ===")

    # Устанавливаем тестовый режим
    os.environ['CLAUDE_TEST_MODE'] = 'true'

    # Создаем временный проект
    temp_dir = tempfile.mkdtemp(prefix="debug_work_packager_")
    project_dir = Path(temp_dir) / "projects" / "debug_user" / "debug_project"
    project_dir.mkdir(parents=True, exist_ok=True)

    # Создаем true.json
    truth_file = project_dir / "true.json"
    with open(truth_file, 'w', encoding='utf-8') as f:
        json.dump(MINIMAL_DATA, f, ensure_ascii=False, indent=2)

    print(f"📄 Создан проект: {project_dir}")
    print(f"📄 truth.json: {truth_file}")

    try:
        # Напрямую тестируем через Claude клиент
        from src.shared.claude_client import claude_client

        # Загружаем промт work_packager
        prompt_path = "src/prompts/work_packager_prompt.txt"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()

        print(f"✅ Промт загружен: {len(system_prompt)} символов")

        # Готовим данные как делает агент
        data_for_prompt = json.dumps(MINIMAL_DATA, ensure_ascii=False, indent=2)
        user_prompt = f"Данные проекта для группировки работ в пакеты:\n\n{data_for_prompt}"

        print(f"🔄 Отправляем запрос Claude напрямую...")
        print(f"📝 Промт: {len(user_prompt)} символов")

        # Вызываем Claude
        result = await claude_client.generate_response(
            prompt=user_prompt,
            agent_name="work_packager",
            system_instruction=system_prompt,
            max_retries=3
        )

        print(f"\n📊 === РЕЗУЛЬТАТ CLAUDE ===")
        print(f"Успех: {result['success']}")
        print(f"Токены: {result.get('usage_metadata', {}).get('total_token_count', 'N/A')}")
        print(f"Стоимость: ~${result.get('estimated_cost', 0):.4f}")

        if result['success']:
            response = result['response']
            print(f"\n📋 Тип ответа: {type(response)}")

            if isinstance(response, dict):
                print(f"📋 Ключи в ответе: {list(response.keys())}")

                # Показываем полный ответ
                print(f"\n📄 === ПОЛНЫЙ ОТВЕТ CLAUDE ===")
                print(json.dumps(response, ensure_ascii=False, indent=2))

                # Проверяем ожидаемые поля
                expected_fields = ['results', 'metadata', 'packages', 'work_packages']
                for field in expected_fields:
                    if field in response:
                        print(f"✅ Найдено поле '{field}': {type(response[field])}")
                        if isinstance(response[field], list):
                            print(f"   Элементов: {len(response[field])}")
                    else:
                        print(f"❌ Отсутствует поле '{field}'")

            else:
                print(f"📋 Ответ не является dict: {str(response)[:200]}...")

        else:
            print(f"❌ Ошибка Claude: {result.get('error', 'Unknown')}")

        # Теперь тестируем через агент для сравнения
        print(f"\n🎯 === ТЕСТ ЧЕРЕЗ АГЕНТ ===")

        from src.ai_agents.work_packager import run_work_packager

        agent_result = await run_work_packager(str(project_dir))

        print(f"Агент успех: {agent_result.get('success', False) if agent_result else False}")
        if agent_result:
            print(f"Агент ошибка: {agent_result.get('error', 'No error')}")
            if 'result' in agent_result:
                print(f"Агент результат тип: {type(agent_result['result'])}")

    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Очистка
        import shutil
        try:
            shutil.rmtree(temp_dir)
            print(f"\n🧹 Очистка: {temp_dir}")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(debug_work_packager())