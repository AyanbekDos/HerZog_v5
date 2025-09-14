"""
Инициализатор файла true.json для системы HerZog v3.0
Создает единый источник правды из существующих данных проекта
"""

import json
import uuid
import os
from typing import Dict, List
from datetime import datetime

def create_true_json(project_path: str) -> bool:
    """
    Создает файл true.json из существующих данных проекта
    
    Args:
        project_path: Путь к папке проекта
        
    Returns:
        True если файл создан успешно
    """
    try:
        # Читаем подготовленные данные проекта (они уже содержат директивы)
        project_data_path = os.path.join(project_path, "3_prepared", "project_data.json")
        if not os.path.exists(project_data_path):
            raise FileNotFoundError(f"Не найден файл project_data: {project_data_path}")
        
        with open(project_data_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        # Директивы уже включены в project_data
        directives_data = project_data.get("directives", {})
        
        # Определяем project_id из пути или создаем новый
        project_id = os.path.basename(project_path)
        
        # Создаем true.json структуру
        truth_data = {
            "metadata": {
                "project_id": project_id,
                "project_name": directives_data.get("project_name", "Безымянный проект"),
                "source_file_name": directives_data.get("source_file_name", "estimate.xlsx"),
                "created_at": datetime.now().isoformat(),
                "pipeline_status": [
                    {"agent_name": "work_packager", "status": "pending"},
                    {"agent_name": "works_to_packages", "status": "pending"},
                    {"agent_name": "counter", "status": "pending"},
                    {"agent_name": "scheduler_and_staffer", "status": "pending"}
                ]
            },
            
            "project_inputs": {
                "target_work_package_count": directives_data.get("target_work_count", 15),
                "project_timeline": {
                    "start_date": directives_data.get("project_timeline", {}).get("start_date", "2025-09-01"),
                    "end_date": directives_data.get("project_timeline", {}).get("end_date", "2025-10-31")
                },
                "workforce_range": {
                    "min": directives_data.get("workforce_range", {}).get("min", 10),
                    "max": directives_data.get("workforce_range", {}).get("max", 20)
                },
                "agent_directives": directives_data.get("agent_directives", {
                    "work_packager": "",
                    "counter": "",
                    "scheduler_and_staffer": ""
                })
            },
            
            "timeline_blocks": project_data.get("timeline_blocks", []),
            
            "source_work_items": convert_work_items(project_data.get("work_items", [])),
            
            "results": {
                "work_packages": [],
                "schedule": {},
                "accounting": {},
                "staffing": {}
            }
        }
        
        # Сохраняем true.json в корень проекта
        truth_path = os.path.join(project_path, "true.json")
        with open(truth_path, 'w', encoding='utf-8') as f:
            json.dump(truth_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Создан true.json: {truth_path}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания true.json: {e}")
        return False

def convert_work_items(old_work_items: List[Dict]) -> List[Dict]:
    """
    Конвертирует work_items из старого формата в новый формат для true.json
    
    Args:
        old_work_items: Массив работ в старом формате
        
    Returns:
        Массив работ в новом формате
    """
    converted_items = []
    
    for item in old_work_items:
        # Создаем UUID если его нет
        item_id = item.get("id", str(uuid.uuid4()))
        
        converted_item = {
            "id": item_id,
            "source_file": item.get("source_file", "estimate.xlsx"),
            "code": item.get("code", ""),
            "name": item.get("name", ""),
            "unit": item.get("unit", ""),
            "quantity": item.get("quantity", 0.0)
        }
        
        converted_items.append(converted_item)
    
    return converted_items

def update_pipeline_status(truth_path: str, agent_name: str, new_status: str) -> bool:
    """
    Обновляет статус агента в pipeline_status
    
    Args:
        truth_path: Путь к файлу true.json
        agent_name: Имя агента
        new_status: Новый статус (pending/in_progress/completed)
        
    Returns:
        True если обновление успешно
    """
    try:
        # Читаем текущий true.json
        with open(truth_path, 'r', encoding='utf-8') as f:
            truth_data = json.load(f)
        
        # Находим и обновляем статус агента
        updated = False
        for i, agent in enumerate(truth_data["metadata"]["pipeline_status"]):
            if agent["agent_name"] == agent_name:
                truth_data["metadata"]["pipeline_status"][i]["status"] = new_status
                
                if new_status == "in_progress":
                    truth_data["metadata"]["pipeline_status"][i]["started_at"] = datetime.now().isoformat()
                elif new_status == "completed":
                    truth_data["metadata"]["pipeline_status"][i]["completed_at"] = datetime.now().isoformat()
                    
                    # Следующий агент остается pending - его активирует main_pipeline
                    # Не активируем автоматически
                
                updated = True
                break
        
        if updated:
            # Сохраняем обновленный файл
            with open(truth_path, 'w', encoding='utf-8') as f:
                json.dump(truth_data, f, ensure_ascii=False, indent=2)
            return True
        else:
            print(f"⚠️ Агент {agent_name} не найден в pipeline_status")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка обновления статуса: {e}")
        return False

def get_current_agent(truth_path: str) -> str:
    """
    Находит текущего активного агента (со статусом in_progress или первого pending)
    
    Args:
        truth_path: Путь к файлу true.json
        
    Returns:
        Имя текущего агента или None если все завершены
    """
    try:
        with open(truth_path, 'r', encoding='utf-8') as f:
            truth_data = json.load(f)
        
        # Ищем агента in_progress
        for agent in truth_data["metadata"]["pipeline_status"]:
            if agent["status"] == "in_progress":
                return agent["agent_name"]
        
        # Если нет in_progress, ищем первого pending
        for agent in truth_data["metadata"]["pipeline_status"]:
            if agent["status"] == "pending":
                return agent["agent_name"]
        
        # Все агенты завершены
        return None
        
    except Exception as e:
        print(f"❌ Ошибка поиска текущего агента: {e}")
        return None

if __name__ == "__main__":
    # Тестирование на реальном проекте
    test_project_path = "/home/imort/Herzog_v3/projects/34975055/d19120ef"
    
    if os.path.exists(test_project_path):
        print(f"🧪 Тестирование создания true.json для {test_project_path}")
        success = create_true_json(test_project_path)
        
        if success:
            truth_path = os.path.join(test_project_path, "true.json")
            current_agent = get_current_agent(truth_path)
            print(f"🎯 Текущий агент для запуска: {current_agent}")
        else:
            print("❌ Тест не прошел")
    else:
        print(f"❌ Тестовый проект не найден: {test_project_path}")