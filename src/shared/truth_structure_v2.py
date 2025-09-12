"""
Новая структура true.json v2.0 для лучшей читаемости
Иерархичная, понятная структура для людей и машин
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class TruthStructureV2:
    """
    Класс для создания и валидации новой структуры true.json v2.0
    
    Принципы новой структуры:
    1. Четкое разделение секций
    2. Человекочитаемость
    3. Машинная обрабатываемость  
    4. Иерархичность
    5. Минимализм (только необходимое)
    """
    
    @staticmethod
    def create_empty_structure(project_id: str, project_name: str, source_file: str) -> Dict[str, Any]:
        """
        Создает пустую структуру true.json v2.0
        """
        return {
            # 🏗️ МЕТАИНФОРМАЦИЯ
            "meta": {
                "structure_version": "2.0",
                "project_id": project_id,
                "project_name": project_name,
                "source_file_name": source_file,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            },
            
            # 👤 ВХОДНЫЕ ПАРАМЕТРЫ ПОЛЬЗОВАТЕЛЯ  
            "user_inputs": {
                "project_settings": {
                    "target_work_package_count": 10,
                    "timeline": {
                        "start_date": None,
                        "end_date": None
                    },
                    "workforce": {
                        "min_workers": 5,
                        "max_workers": 20
                    }
                },
                "agent_directives": {
                    "work_packager": "",
                    "works_to_packages": "",
                    "counter": "",
                    "scheduler_and_staffer": ""
                },
                "project_context": {
                    "project_type": "",
                    "building_type": "",
                    "location_type": "",
                    "season": "",
                    "special_conditions": []
                }
            },
            
            # ⏱️ ВРЕМЕННЫЕ БЛОКИ (НЕДЕЛИ)
            "timeline_blocks": [],
            
            # 📋 ИСХОДНЫЕ ДАННЫЕ ИЗ СМЕТЫ
            "source_data": {
                "total_work_items": 0,
                "work_items": []
            },
            
            # 🎯 РЕЗУЛЬТАТЫ ОБРАБОТКИ АГЕНТАМИ
            "results": {
                "work_packages": [],
                "volume_summary": {},
                "schedule_summary": {},
                "staffing_summary": {}
            },
            
            # 🔄 СТАТУС PIPELINE
            "pipeline": {
                "current_stage": "initialized",
                "agents_status": [],
                "last_successful_stage": None,
                "errors": []
            }
        }
    
    @staticmethod
    def restructure_old_format(old_truth: Dict[str, Any]) -> Dict[str, Any]:
        """
        Преобразует старый формат true.json в новый v2.0
        """
        # Извлекаем данные из старого формата
        old_meta = old_truth.get("metadata", {})
        old_inputs = old_truth.get("project_inputs", {})
        old_results = old_truth.get("results", {})
        old_timeline = old_truth.get("timeline_blocks", [])
        old_source = old_truth.get("source_work_items", [])
        old_pipeline = old_truth.get("metadata", {}).get("pipeline_status", [])
        
        # Создаем новую структуру
        new_structure = {
            # 🏗️ МЕТАИНФОРМАЦИЯ
            "meta": {
                "structure_version": "2.0",
                "project_id": old_meta.get("project_id", "unknown"),
                "project_name": old_inputs.get("project_name", "Безымянный проект"),
                "source_file_name": old_meta.get("source_file_name", "unknown.xlsx"),
                "created_at": old_meta.get("created_at", datetime.now().isoformat()),
                "last_updated": datetime.now().isoformat(),
                "migrated_from": "v1.0"
            },
            
            # 👤 ВХОДНЫЕ ПАРАМЕТРЫ ПОЛЬЗОВАТЕЛЯ
            "user_inputs": {
                "project_settings": {
                    "target_work_package_count": old_inputs.get("target_work_package_count", 10),
                    "timeline": {
                        "start_date": old_inputs.get("project_timeline", {}).get("start_date"),
                        "end_date": old_inputs.get("project_timeline", {}).get("end_date")
                    },
                    "workforce": {
                        "min_workers": old_inputs.get("workforce_range", {}).get("min", 5),
                        "max_workers": old_inputs.get("workforce_range", {}).get("max", 20)
                    }
                },
                "agent_directives": old_inputs.get("agent_directives", {}),
                "project_context": {
                    "project_type": old_inputs.get("external_context", {}).get("object_characteristics", {}).get("project_type", ""),
                    "building_type": old_inputs.get("external_context", {}).get("object_characteristics", {}).get("building_type", ""),
                    "location_type": old_inputs.get("external_context", {}).get("site_conditions", {}).get("location_type", ""),
                    "season": old_inputs.get("external_context", {}).get("climate_factors", {}).get("season", ""),
                    "special_conditions": old_inputs.get("external_context", {}).get("site_conditions", {}).get("work_time_restrictions", [])
                }
            },
            
            # ⏱️ ВРЕМЕННЫЕ БЛОКИ (унифицированные)
            "timeline_blocks": [
                {
                    "week_id": block.get("block_id", block.get("week_id", i+1)),
                    "start_date": block.get("start_date"),
                    "end_date": block.get("end_date"),
                    "working_days": block.get("working_days", 5),
                    "calendar_days": block.get("calendar_days", 7),
                    "holidays": block.get("excluded_holidays", [])
                }
                for i, block in enumerate(old_timeline)
            ],
            
            # 📋 ИСХОДНЫЕ ДАННЫЕ ИЗ СМЕТЫ (упрощенные)
            "source_data": {
                "total_work_items": len(old_source),
                "extraction_summary": {
                    "total_rows_processed": len(old_source),
                    "work_items_identified": len([item for item in old_source if item.get("is_work", True)]),
                    "material_items_identified": len([item for item in old_source if not item.get("is_work", True)])
                },
                # Сокращенная версия исходных данных (только ключевые поля)
                "work_items_summary": [
                    {
                        "id": item.get("id"),
                        "code": item.get("code"),
                        "name": item.get("name", "")[:50] + "..." if len(item.get("name", "")) > 50 else item.get("name", ""),
                        "unit": item.get("unit"),
                        "quantity": item.get("quantity"),
                        "assigned_package": item.get("package_id")
                    }
                    for item in old_source if item.get("is_work", True)
                ]
            },
            
            # 🎯 РЕЗУЛЬТАТЫ ОБРАБОТКИ АГЕНТАМИ
            "results": {
                "work_packages": old_results.get("work_packages", []),
                "volume_summary": old_results.get("volume_summary", {}),
                "schedule_summary": TruthStructureV2._extract_schedule_summary(old_results.get("work_packages", [])),
                "staffing_summary": TruthStructureV2._extract_staffing_summary(old_results.get("work_packages", []))
            },
            
            # 🔄 СТАТУС PIPELINE
            "pipeline": {
                "current_stage": TruthStructureV2._determine_current_stage(old_pipeline),
                "agents_status": [
                    {
                        "agent": status.get("agent_name"),
                        "status": status.get("status"),
                        "started": status.get("started_at"),
                        "completed": status.get("completed_at"),
                        "duration": TruthStructureV2._calculate_duration(
                            status.get("started_at"), 
                            status.get("completed_at")
                        )
                    }
                    for status in old_pipeline
                ],
                "last_successful_stage": TruthStructureV2._find_last_successful(old_pipeline),
                "errors": [
                    status.get("agent_name") 
                    for status in old_pipeline 
                    if status.get("status") == "error"
                ]
            }
        }
        
        return new_structure
    
    @staticmethod
    def _extract_schedule_summary(work_packages: List[Dict]) -> Dict[str, Any]:
        """Извлекает сводку по календарному планированию"""
        if not work_packages:
            return {}
        
        scheduled_packages = [
            pkg for pkg in work_packages 
            if pkg.get("schedule_blocks") or pkg.get("progress_per_block")
        ]
        
        return {
            "total_packages": len(work_packages),
            "scheduled_packages": len(scheduled_packages),
            "scheduling_completeness": len(scheduled_packages) / len(work_packages) * 100 if work_packages else 0
        }
    
    @staticmethod
    def _extract_staffing_summary(work_packages: List[Dict]) -> Dict[str, Any]:
        """Извлекает сводку по кадровому планированию"""
        if not work_packages:
            return {}
        
        staffed_packages = [
            pkg for pkg in work_packages 
            if pkg.get("staffing_per_block")
        ]
        
        return {
            "total_packages": len(work_packages),
            "staffed_packages": len(staffed_packages),
            "staffing_completeness": len(staffed_packages) / len(work_packages) * 100 if work_packages else 0
        }
    
    @staticmethod
    def _determine_current_stage(pipeline_status: List[Dict]) -> str:
        """Определяет текущую стадию pipeline"""
        if not pipeline_status:
            return "initialized"
        
        last_status = pipeline_status[-1]
        if last_status.get("status") == "error":
            return f"error_at_{last_status.get('agent_name', 'unknown')}"
        elif last_status.get("status") == "in_progress":
            return f"processing_{last_status.get('agent_name', 'unknown')}"
        elif last_status.get("status") == "completed":
            return f"completed_{last_status.get('agent_name', 'unknown')}"
        
        return "unknown"
    
    @staticmethod
    def _find_last_successful(pipeline_status: List[Dict]) -> Optional[str]:
        """Находит последнюю успешную стадию"""
        for status in reversed(pipeline_status):
            if status.get("status") == "completed":
                return status.get("agent_name")
        return None
    
    @staticmethod
    def _calculate_duration(start_time: Optional[str], end_time: Optional[str]) -> Optional[float]:
        """Вычисляет длительность выполнения агента в секундах"""
        if not start_time or not end_time:
            return None
        
        try:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            return (end - start).total_seconds()
        except:
            return None

    @staticmethod
    def validate_structure(truth_data: Dict[str, Any]) -> List[str]:
        """
        Валидирует структуру true.json v2.0
        Возвращает список ошибок (пустой список = структура валидна)
        """
        errors = []
        
        # Проверяем обязательные секции
        required_sections = ["meta", "user_inputs", "timeline_blocks", "source_data", "results", "pipeline"]
        for section in required_sections:
            if section not in truth_data:
                errors.append(f"Отсутствует обязательная секция: {section}")
        
        # Проверяем версию структуры
        if truth_data.get("meta", {}).get("structure_version") != "2.0":
            errors.append("Неверная версия структуры (ожидается 2.0)")
        
        # Проверяем целостность данных
        work_packages = truth_data.get("results", {}).get("work_packages", [])
        for pkg in work_packages:
            if not pkg.get("package_id"):
                errors.append(f"Пакет без package_id: {pkg.get('name', 'неизвестный')}")
        
        return errors


def migrate_truth_file(old_file_path: str, new_file_path: str) -> bool:
    """
    Миграция файла true.json из v1.0 в v2.0
    
    Args:
        old_file_path: Путь к старому файлу
        new_file_path: Путь для нового файла
        
    Returns:
        True если миграция успешна, False если ошибка
    """
    try:
        # Читаем старый файл
        with open(old_file_path, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
        
        # Преобразуем структуру
        new_data = TruthStructureV2.restructure_old_format(old_data)
        
        # Валидируем новую структуру
        errors = TruthStructureV2.validate_structure(new_data)
        if errors:
            print(f"⚠️ Предупреждения при миграции: {errors}")
        
        # Сохраняем новый файл
        with open(new_file_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Миграция завершена: {old_file_path} -> {new_file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        return False


if __name__ == "__main__":
    # Тестирование миграции на реальном файле
    test_old_file = "/home/imort/Herzog_v3/projects/34975055/a61b42bf/true.json"
    test_new_file = "/tmp/true_v2_migrated.json"
    
    if migrate_truth_file(test_old_file, test_new_file):
        print("🧪 Тестовая миграция успешна")
        
        # Показываем размеры файлов для сравнения
        import os
        old_size = os.path.getsize(test_old_file)
        new_size = os.path.getsize(test_new_file) 
        print(f"📊 Размер старого файла: {old_size:,} байт")
        print(f"📊 Размер нового файла: {new_size:,} байт")
        print(f"📊 Изменение размера: {((new_size - old_size) / old_size * 100):+.1f}%")
    else:
        print("❌ Тестовая миграция провалилась")