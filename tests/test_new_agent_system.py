#!/usr/bin/env python3
"""
Тест новой системы агентов с разделением на group_creator и group_assigner
"""

import sys
import os
import json
import logging

# Добавляем путь к модулям
sys.path.append('/home/imort/Herzog_v3')

from src.ai_agents.agent_runner import run_agent, run_pipeline

def create_test_project_data():
    """Создает тестовый project_data.json из существующих классифицированных данных"""
    
    # Читаем классифицированные данные
    classified_file = "/home/imort/Herzog_v3/projects/34975055/d19120ef/2_classified/classified_estimates.json"
    with open(classified_file, 'r', encoding='utf-8') as f:
        classified_data = json.load(f)
    
    # Фильтруем ТОЛЬКО работы для project_data.json
    work_items_only = [item for item in classified_data if item.get('classification') == 'Работа']
    print(f"📋 Отфильтровано {len(work_items_only)} работ из {len(classified_data)} позиций")
    
    # Создаем базовый project_data.json
    project_data = {
        "meta": {
            "user_id": "34975055",
            "project_id": "d19120ef", 
            "created_at": "2025-09-04",
            "source_files": ["КР - ЛСР по Методике 2020 (РМ)1.xlsx"]
        },
        "directives": {
            "target_work_count": 15,
            "project_timeline": {
                "start_date": "2024-01-01",
                "end_date": "2024-06-30"
            },
            "workforce_range": {"min": 10, "max": 20},
            "conceptualizer": "всю электрику в один блок, демонтаж отдельно",
            "strategist": "растяни демонтаж на весь первый месяц",
            "accountant": "при объединении считай точно",
            "foreman": "на отделку кинь максимум людей"
        },
        "timeline_blocks": [],  # Будет заполнено позже
        "work_items": work_items_only
    }
    
    # Генерируем недельные блоки (26 недель для полугода)
    from datetime import datetime, timedelta
    start_date = datetime(2024, 1, 1)
    
    for week_num in range(1, 27):
        week_start = start_date + timedelta(weeks=week_num-1)
        week_end = week_start + timedelta(days=6)
        
        project_data["timeline_blocks"].append({
            "week_id": week_num,
            "start_date": week_start.strftime("%Y-%m-%d"),
            "end_date": week_end.strftime("%Y-%m-%d"),
            "calendar_week": week_start.isocalendar()[1]
        })
    
    # Сохраняем в папку 3_prepared
    prepared_dir = "/home/imort/Herzog_v3/projects/34975055/d19120ef/3_prepared"
    os.makedirs(prepared_dir, exist_ok=True)
    
    output_file = os.path.join(prepared_dir, "project_data.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Создан тестовый project_data.json: {output_file}")
    return output_file

def test_group_creator():
    """Тестирует агента group_creator"""
    project_dir = "/home/imort/Herzog_v3/projects/34975055/d19120ef"
    
    print("🧪 Тестирование агента group_creator...")
    
    success = run_agent("group_creator", project_dir)
    
    if success:
        # Проверяем результат
        result_file = os.path.join(project_dir, "4.1_grouped", "project_data.json")
        if os.path.exists(result_file):
            with open(result_file, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
            
            work_groups = result_data.get('work_groups', [])
            print(f"✅ Создано {len(work_groups)} групп работ:")
            for group in work_groups:
                print(f"  - {group.get('name')} (UUID: {group.get('uuid', 'N/A')})")
        
        return True
    else:
        print("❌ Ошибка в работе group_creator")
        return False

def test_group_assigner():
    """Тестирует агента group_assigner"""
    project_dir = "/home/imort/Herzog_v3/projects/34975055/d19120ef"
    
    print("\n🧪 Тестирование агента group_assigner...")
    
    success = run_agent("group_assigner", project_dir)
    
    if success:
        # Проверяем результат
        result_file = os.path.join(project_dir, "4_conceptualized", "project_data.json")
        if os.path.exists(result_file):
            with open(result_file, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
            
            work_items = result_data.get('work_items', [])
            assigned_works = [item for item in work_items 
                            if item.get('classification') == 'Работа' and 'group_uuid' in item]
            
            print(f"✅ Назначены группы для {len(assigned_works)} работ")
            
            # Группируем по UUID групп
            group_assignments = {}
            for work in assigned_works:
                group_uuid = work.get('group_uuid')
                if group_uuid not in group_assignments:
                    group_assignments[group_uuid] = []
                group_assignments[group_uuid].append(work.get('name', 'N/A'))
            
            print(f"📊 Распределение по группам:")
            for group_uuid, works in group_assignments.items():
                print(f"  - {group_uuid[:8]}...: {len(works)} работ")
        
        return True
    else:
        print("❌ Ошибка в работе group_assigner")
        return False

def main():
    """Основная функция тестирования"""
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 Запуск теста новой системы агентов")
    
    try:
        # Создаем тестовые данные
        create_test_project_data()
        
        # Тестируем первого агента
        success1 = test_group_creator()
        
        if success1:
            # Тестируем второго агента
            success2 = test_group_assigner()
            
            if success2:
                print("\n🎉 Оба агента работают успешно!")
                return True
        
        print("\n💥 Тестирование провалено")
        return False
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)