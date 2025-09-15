#!/usr/bin/env python3
"""
Тест полного пайплайна с Claude агентами
Создает правильную структуру проекта как ожидают агенты
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

# Минимальные тестовые данные для этапа 3_prepared
TEST_DATA = {
    "metadata": {
        "user_id": "test_user_claude",
        "project_id": "test_project_claude",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "current_stage": "3_prepared",
        "stages_completed": ["1_extracted", "2_classified", "3_prepared"],
        "pipeline_status": [
            {"agent_name": "work_packager", "status": "pending"},
            {"agent_name": "works_to_packages", "status": "pending"},
            {"agent_name": "counter", "status": "pending"},
            {"agent_name": "scheduler_and_staffer", "status": "pending"}
        ]
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
            "work_packager": "создай ровно 3 пакета работ",
            "counter": "подсчитай объемы точно",
            "scheduler": "распредели равномерно по 4 неделям"
        }
    },
    "timeline_blocks": [
        {"week_id": 1, "start_date": "2024-01-01", "end_date": "2024-01-07", "days_count": 7},
        {"week_id": 2, "start_date": "2024-01-08", "end_date": "2024-01-14", "days_count": 7},
        {"week_id": 3, "start_date": "2024-01-15", "end_date": "2024-01-21", "days_count": 7},
        {"week_id": 4, "start_date": "2024-01-22", "end_date": "2024-01-28", "days_count": 7}
    ],
    "packages": [],  # Пустой, будет заполнен агентами
    "results": {
        "work_packages": []  # Поле которое ожидает агент work_packager
    },
    "source_work_items": [
        {
            "id": "work_001",
            "name": "Демонтаж кирпичной перегородки",
            "classification": "work",
            "unit": "м²",
            "quantity": 25.0,
            "unit_cost": 600.0,
            "total_cost": 15000.0,
            "category": "demolition",
            "original_data": {"source": "test"}
        },
        {
            "id": "work_002",
            "name": "Штукатурка стен цементная",
            "classification": "work",
            "unit": "м²",
            "quantity": 50.0,
            "unit_cost": 900.0,
            "total_cost": 45000.0,
            "category": "finishing",
            "original_data": {"source": "test"}
        },
        {
            "id": "work_003",
            "name": "Покраска стен водоэмульсионная",
            "classification": "work",
            "unit": "м²",
            "quantity": 50.0,
            "unit_cost": 350.0,
            "total_cost": 17500.0,
            "category": "finishing",
            "original_data": {"source": "test"}
        },
        {
            "id": "work_004",
            "name": "Устройство цементной стяжки",
            "classification": "work",
            "unit": "м²",
            "quantity": 80.0,
            "unit_cost": 1200.0,
            "total_cost": 96000.0,
            "category": "flooring",
            "original_data": {"source": "test"}
        }
    ]
}

def create_project_structure(base_dir, data):
    """Создает структуру проекта как ожидают агенты"""
    project_dir = Path(base_dir) / "projects" / data["metadata"]["user_id"] / data["metadata"]["project_id"]

    # Создаем все необходимые директории
    stages = ["0_input", "1_extracted", "2_classified", "3_prepared", "4_packaged", "5_counted", "6_scheduled", "7_output"]
    for stage in stages:
        stage_dir = project_dir / stage
        stage_dir.mkdir(parents=True, exist_ok=True)

    # Сохраняем true.json в корне проекта (как ожидают агенты)
    truth_file = project_dir / "true.json"
    with open(truth_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Также копируем в 3_prepared для совместимости
    truth_file_prepared = project_dir / "3_prepared" / "truth.json"
    with open(truth_file_prepared, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"📁 Создана структура проекта: {project_dir}")
    print(f"📄 truth.json сохранен: {truth_file}")

    return str(project_dir)

async def test_full_pipeline():
    """Тестируем полный пайплайн Claude агентов"""
    print("🚀 === ТЕСТ ПОЛНОГО ПАЙПЛАЙНА CLAUDE АГЕНТОВ ===")
    print(f"🧪 Тестовый режим: {os.getenv('CLAUDE_TEST_MODE', 'true')}")

    # Сбрасываем статистику Claude
    try:
        from src.shared.claude_client import claude_client
        claude_client.reset_usage_stats()
        print("📊 Статистика Claude сброшена")
    except Exception as e:
        print(f"⚠️  Не удалось сбросить статистику: {e}")

    # Создаем временную директорию
    base_temp_dir = tempfile.mkdtemp(prefix="claude_pipeline_")
    print(f"📂 Временная директория: {base_temp_dir}")

    try:
        # Создаем структуру проекта
        project_dir = create_project_structure(base_temp_dir, TEST_DATA)

        # Импортируем агенты
        try:
            from src.ai_agents.work_packager import run_work_packager
            from src.ai_agents.works_to_packages import run_works_to_packages
            from src.ai_agents.counter import run_counter
            from src.ai_agents.scheduler_and_staffer import run_scheduler_and_staffer
            print("✅ Все агенты импортированы")
        except ImportError as e:
            print(f"❌ Ошибка импорта агентов: {e}")
            return

        agents = [
            ("Work Packager", run_work_packager, "4_packaged"),
            ("Works to Packages", run_works_to_packages, "5_counted"),  # Исправлено: works_to_packages создает 5_counted
            ("Counter", run_counter, "6_scheduled"),  # Исправлено: counter создает 6_scheduled
            ("Scheduler and Staffer", run_scheduler_and_staffer, "7_output")  # scheduler создает финальный результат
        ]

        results = []
        total_time = 0

        for i, (agent_name, agent_func, expected_stage) in enumerate(agents, 1):
            print(f"\n🎯 === ТЕСТ {i}: {agent_name.upper()} ===")

            try:
                start_time = asyncio.get_event_loop().time()

                # Запускаем агент
                result = await agent_func(project_dir)

                end_time = asyncio.get_event_loop().time()
                duration = end_time - start_time
                total_time += duration

                if result and result.get('success'):
                    print(f"✅ {agent_name} успешен!")
                    print(f"⏱️  Время: {duration:.2f} сек")

                    # Проверяем что файл создан в нужной директории
                    expected_dir = Path(project_dir) / expected_stage
                    if expected_dir.exists():
                        files = list(expected_dir.glob("*.json"))
                        if files:
                            print(f"📁 Создан файл: {files[0].name}")
                        else:
                            print(f"⚠️  Нет JSON файлов в {expected_stage}")
                    else:
                        print(f"⚠️  Директория {expected_stage} не создана")

                    results.append((agent_name, True, duration))

                else:
                    error = result.get('error', 'Unknown error') if result else 'No result'
                    print(f"❌ {agent_name} ошибка: {error}")
                    if result and 'raw_text' in result:
                        print(f"📄 СЫРОЙ ОТВЕТ LLM:\n---\n{result['raw_text']}\n---")
                    results.append((agent_name, False, duration))
                    break  # Останавливаем при первой ошибке

            except Exception as e:
                print(f"💥 Критическая ошибка {agent_name}: {e}")
                import traceback
                traceback.print_exc()
                results.append((agent_name, False, 0))
                break

        # Итоговая статистика
        print(f"\n🎯 === ИТОГОВЫЕ РЕЗУЛЬТАТЫ ===")

        successful = sum(1 for _, success, _ in results if success)
        total = len(results)

        print(f"✅ Успешно: {successful}/{len(agents)}")
        print(f"⏱️  Общее время: {total_time:.2f} сек")

        # Статистика Claude
        try:
            from src.shared.claude_client import claude_client
            stats = claude_client.get_usage_stats()
            print(f"\n💰 === СТАТИСТИКА CLAUDE ===")
            print(f"Запросов: {stats['total_requests']}")
            print(f"Входные токены: {stats['total_input_tokens']}")
            print(f"Выходные токены: {stats['total_output_tokens']}")
            print(f"Общая стоимость: ~${stats['estimated_cost']:.4f}")

            if stats['total_requests'] > 0:
                avg_cost = stats['estimated_cost'] / stats['total_requests']
                print(f"📊 Средняя стоимость за запрос: ~${avg_cost:.4f}")

        except Exception as e:
            print(f"⚠️  Ошибка статистики: {e}")

        # Детали результатов
        print(f"\n📋 === ДЕТАЛИ ===")
        for name, success, duration in results:
            status = "✅" if success else "❌"
            print(f"{status} {name}: {duration:.2f} сек")

        if successful == len(agents):
            print(f"\n🎉 ВСЕ АГЕНТЫ РАБОТАЮТ С CLAUDE!")

            # Показываем структуру финальных файлов
            print(f"\n📁 === СОЗДАННЫЕ ФАЙЛЫ ===")
            for stage in ["4_packaged", "5_counted", "6_scheduled", "7_output"]:
                stage_dir = Path(project_dir) / stage
                if stage_dir.exists():
                    files = list(stage_dir.glob("*.json"))
                    if files:
                        print(f"{stage}: {files[0].name} ({files[0].stat().st_size} байт)")

        else:
            print(f"\n⚠️  Не все агенты прошли тест ({successful}/{len(agents)})")

    finally:
        # Очистка
        try:
            shutil.rmtree(base_temp_dir)
            print(f"\n🧹 Временные файлы очищены")
        except Exception as e:
            print(f"\n⚠️  Ошибка очистки: {e}")
            print(f"Папка осталась: {base_temp_dir}")

if __name__ == "__main__":
    # Принудительно устанавливаем тестовый режим
    os.environ['CLAUDE_TEST_MODE'] = 'true'

    asyncio.run(test_full_pipeline())
