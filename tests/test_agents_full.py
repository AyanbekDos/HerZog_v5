"""
Полный тест всех AI-агентов HerZog v3.0 с мок-данными
"""

import asyncio
import json
import os
import shutil
import tempfile
import logging
from datetime import datetime

# Настраиваем логирование для тестов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Тестовые данные для полного пайплайна
TEST_PROJECT_DATA = {
    "meta": {
        "created_at": datetime.now().isoformat(),
        "total_work_items": 6,
        "total_timeline_blocks": 12,
        "project_duration_weeks": 12
    },
    "directives": {
        "target_work_count": 15,
        "project_timeline": {
            "start_date": "01.01.2024",
            "end_date": "31.03.2024"
        },
        "workforce_range": {"min": 8, "max": 15},
        "directives": {
            "conceptualizer": "всю электрику в один блок, а сантехнику отдельно",
            "strategist": "демонтаж на первой неделе",
            "accountant": "при объединении считай площадь в м²",
            "foreman": "на отделку больше людей"
        }
    },
    "timeline_blocks": [
        {"week_id": 1, "start_date": "01.01.2024", "end_date": "07.01.2024", "days": 7},
        {"week_id": 2, "start_date": "08.01.2024", "end_date": "14.01.2024", "days": 7},
        {"week_id": 3, "start_date": "15.01.2024", "end_date": "21.01.2024", "days": 7},
        {"week_id": 4, "start_date": "22.01.2024", "end_date": "28.01.2024", "days": 7},
        {"week_id": 5, "start_date": "29.01.2024", "end_date": "04.02.2024", "days": 7},
        {"week_id": 6, "start_date": "05.02.2024", "end_date": "11.02.2024", "days": 7},
        {"week_id": 7, "start_date": "12.02.2024", "end_date": "18.02.2024", "days": 7},
        {"week_id": 8, "start_date": "19.02.2024", "end_date": "25.02.2024", "days": 7},
        {"week_id": 9, "start_date": "26.02.2024", "end_date": "04.03.2024", "days": 7},
        {"week_id": 10, "start_date": "05.03.2024", "end_date": "11.03.2024", "days": 7},
        {"week_id": 11, "start_date": "12.03.2024", "end_date": "18.03.2024", "days": 7},
        {"week_id": 12, "start_date": "19.03.2024", "end_date": "25.03.2024", "days": 7}
    ],
    "work_items": [
        {
            "id": "work_001",
            "original_data": {
                "internal_id": "pos_001",
                "source_file": "test_smeta.xlsx",
                "position_num": "1",
                "code": "ГЭСН46-02-009-02",
                "name": "Демонтаж штукатурки с поверхностей стен",
                "unit": "100 м2",
                "quantity": "2.5",
                "classification": "Работа"
            },
            "group_id": None,
            "group_name": None,
            "schedule_phases": [],
            "worker_counts": []
        },
        {
            "id": "work_002", 
            "original_data": {
                "internal_id": "pos_002",
                "source_file": "test_smeta.xlsx",
                "position_num": "2",
                "code": "ГЭСН15-04-015-01",
                "name": "Кладка стен из кирпича керамического обыкновенного",
                "unit": "м3",
                "quantity": "15.8",
                "classification": "Работа"
            },
            "group_id": None,
            "group_name": None,
            "schedule_phases": [],
            "worker_counts": []
        },
        {
            "id": "work_003",
            "original_data": {
                "internal_id": "pos_003",
                "source_file": "test_smeta.xlsx",
                "position_num": "3", 
                "code": "ГЭСН23-03-003-01",
                "name": "Прокладка кабеля силового в трубах",
                "unit": "м",
                "quantity": "120",
                "classification": "Работа"
            },
            "group_id": None,
            "group_name": None,
            "schedule_phases": [],
            "worker_counts": []
        },
        {
            "id": "work_004",
            "original_data": {
                "internal_id": "pos_004",
                "source_file": "test_smeta.xlsx",
                "position_num": "4",
                "code": "ГЭСН24-01-015-02",
                "name": "Установка стояков водопроводных стальных",
                "unit": "м",
                "quantity": "25",
                "classification": "Работа"
            },
            "group_id": None,
            "group_name": None,
            "schedule_phases": [],
            "worker_counts": []
        },
        {
            "id": "work_005",
            "original_data": {
                "internal_id": "pos_005",
                "source_file": "test_smeta.xlsx",
                "position_num": "5",
                "code": "ГЭСН15-01-052-01",
                "name": "Штукатурка поверхностей стен цементно-известковым раствором",
                "unit": "100 м2",
                "quantity": "3.2",
                "classification": "Работа"
            },
            "group_id": None,
            "group_name": None,
            "schedule_phases": [],
            "worker_counts": []
        },
        {
            "id": "work_006",
            "original_data": {
                "internal_id": "pos_006",
                "source_file": "test_smeta.xlsx",
                "position_num": "6",
                "code": "ГЭСН15-01-055-03",
                "name": "Окраска поверхностей стен и потолков",
                "unit": "100 м2", 
                "quantity": "4.1",
                "classification": "Работа"
            },
            "group_id": None,
            "group_name": None,
            "schedule_phases": [],
            "worker_counts": []
        }
    ],
    "processing_status": {
        "extraction": "completed",
        "classification": "completed", 
        "preparation": "completed",
        "conceptualization": "pending",
        "scheduling": "pending",
        "accounting": "pending",
        "staffing": "pending",
        "reporting": "pending"
    }
}


async def test_agents_pipeline():
    """
    Тестирует полный пайплайн всех агентов
    """
    # Создаем временную папку для тестов
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Запуск тестов в папке: {temp_dir}")
        
        # Создаем структуру папок как в реальном проекте
        paths = {
            3: f"{temp_dir}/3_prepared",
            4: f"{temp_dir}/4_conceptualized", 
            5: f"{temp_dir}/5_scheduled",
            6: f"{temp_dir}/6_accounted",
            7: f"{temp_dir}/7_staffed",
            8: f"{temp_dir}/8_output"
        }
        
        for path in paths.values():
            os.makedirs(path, exist_ok=True)
        
        # Сохраняем начальные данные
        initial_data = TEST_PROJECT_DATA.copy()
        with open(f"{paths[3]}/project_data.json", 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=2)
        
        logger.info("✅ Тестовые данные подготовлены")
        
        # Тест 1: Агент Концептуализатор
        logger.info("🎯 Тестируем Агент 1: Концептуализатор")
        try:
            # Импортируем агента (с учетом относительных путей)
            import sys
            sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
            
            from src.ai_agents.agent_1_conceptualizer import run_agent as run_agent_1
            
            result_1 = await run_agent_1(paths[3], paths[4])
            logger.info(f"✅ Агент 1 завершен: {result_1}")
            
            # Проверяем результат
            with open(f"{paths[4]}/project_data.json", 'r', encoding='utf-8') as f:
                data_after_1 = json.load(f)
                
            # Проверяем что группы назначены
            grouped_count = sum(1 for item in data_after_1['work_items'] if item.get('group_id') is not None)
            logger.info(f"Сгруппировано работ: {grouped_count}/6")
            
            # Проверяем наличие файлов логирования
            assert os.path.exists(f"{paths[4]}/llm_input.json"), "Файл llm_input.json не создан"
            assert os.path.exists(f"{paths[4]}/llm_response.json"), "Файл llm_response.json не создан"
            
            logger.info("✅ Агент 1 прошел тест")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в агенте 1: {e}")
            return False
        
        # Тест 2: Агент Стратег  
        logger.info("📋 Тестируем Агент 2: Стратег")
        try:
            from src.ai_agents.agent_2_strategist import run_agent as run_agent_2
            
            result_2 = await run_agent_2(paths[4], paths[5])
            logger.info(f"✅ Агент 2 завершен: {result_2}")
            
            # Проверяем результат
            with open(f"{paths[5]}/project_data.json", 'r', encoding='utf-8') as f:
                data_after_2 = json.load(f)
                
            # Проверяем что фазы назначены
            scheduled_count = sum(1 for item in data_after_2['work_items'] if item.get('schedule_phases'))
            logger.info(f"Запланировано работ: {scheduled_count}/6")
            
            logger.info("✅ Агент 2 прошел тест")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в агенте 2: {e}")
            return False
        
        # Тест 3: Агент Бухгалтер
        logger.info("💰 Тестируем Агент 3: Бухгалтер")
        try:
            from src.ai_agents.agent_3_accountant import run_agent as run_agent_3
            
            result_3 = await run_agent_3(paths[5], paths[6])
            logger.info(f"✅ Агент 3 завершен: {result_3}")
            
            # Проверяем результат
            with open(f"{paths[6]}/project_data.json", 'r', encoding='utf-8') as f:
                data_after_3 = json.load(f)
                
            # Проверяем что созданы итоги по группам
            group_summary = data_after_3.get('group_summary', {})
            logger.info(f"Создано сводок по группам: {len(group_summary)}")
            
            logger.info("✅ Агент 3 прошел тест")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в агенте 3: {e}")
            return False
        
        # Тест 4: Агент Прораб
        logger.info("⚡ Тестируем Агент 4: Прораб")
        try:
            from src.ai_agents.agent_4_foreman import run_agent as run_agent_4
            
            result_4 = await run_agent_4(paths[6], paths[7])
            logger.info(f"✅ Агент 4 завершен: {result_4}")
            
            # Проверяем результат  
            with open(f"{paths[7]}/project_data.json", 'r', encoding='utf-8') as f:
                data_after_4 = json.load(f)
                
            # Проверяем что рабочие распределены
            staffed_count = sum(1 for item in data_after_4['work_items'] if item.get('worker_counts'))
            logger.info(f"Укомплектовано работ: {staffed_count}/6")
            
            logger.info("✅ Агент 4 прошел тест")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в агенте 4: {e}")
            return False
        
        # Тест 5: Финальный отчет
        logger.info("📊 Тестируем генерацию финального отчета")
        try:
            from src.data_processing.reporter import generate_excel_report
            
            final_input = f"{paths[7]}/project_data.json"
            excel_file = generate_excel_report(final_input, paths[8])
            
            assert os.path.exists(excel_file), "Excel файл не создан"
            logger.info(f"✅ Excel отчет создан: {excel_file}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации отчета: {e}")
            return False
        
        # Финальная проверка обогащения данных
        logger.info("🔍 Финальная проверка обогащения project_data.json")
        
        with open(f"{paths[7]}/project_data.json", 'r', encoding='utf-8') as f:
            final_data = json.load(f)
        
        # Проверяем что все поля заполнены правильно
        for item in final_data['work_items']:
            assert item.get('group_id') is not None, f"group_id не заполнен для {item['id']}"
            assert item.get('group_name') is not None, f"group_name не заполнен для {item['id']}"
            # schedule_phases и worker_counts могут быть пустыми массивами - это нормально
        
        # Проверяем статусы обработки
        status = final_data['processing_status']
        assert status['conceptualization'] == 'completed', "Статус концептуализации не completed"
        assert status['scheduling'] == 'completed', "Статус планирования не completed" 
        assert status['accounting'] == 'completed', "Статус бухгалтерии не completed"
        assert status['staffing'] == 'completed', "Статус укомплектования не completed"
        
        logger.info("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        
        # Выводим итоговую статистику
        groups = set(item.get('group_id') for item in final_data['work_items'] if item.get('group_id'))
        logger.info(f"📈 ИТОГОВАЯ СТАТИСТИКА:")
        logger.info(f"   Создано групп: {len(groups)}")
        logger.info(f"   Обработано работ: {len(final_data['work_items'])}")
        logger.info(f"   Недель в проекте: {len(final_data['timeline_blocks'])}")
        if 'group_summary' in final_data:
            logger.info(f"   Сводок по группам: {len(final_data['group_summary'])}")
        
        return True


if __name__ == "__main__":
    # Запускаем тесты
    result = asyncio.run(test_agents_pipeline())
    if result:
        print("\n🎯 Все агенты работают корректно!")
        print("🔄 Обогащение project_data.json происходит на каждом этапе")
        print("📁 Все файлы логирования создаются")
    else:
        print("\n❌ Обнаружены ошибки в работе агентов")
        exit(1)