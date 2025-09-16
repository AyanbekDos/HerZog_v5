"""
НОВЫЙ Truth Initializer v3.0 для HerZog v3.0
Создает ЧИСТУЮ эталонную структуру без legacy артефактов
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class TruthManagerV3:
    """
    Менеджер эталонной структуры true.json v3.0
    Обеспечивает ЧИСТУЮ архитектуру без старых артефактов
    """

    def __init__(self):
        self.template_path = os.path.join(
            os.path.dirname(__file__), "truth_template_v3.json"
        )

    def create_project(self, project_name: str, source_file: str, user_id: str,
                      project_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создает новый проект с эталонной структурой v3.0

        Args:
            project_name: Название проекта
            source_file: Исходный файл (xlsx)
            user_id: ID пользователя
            project_config: Конфигурация (timeline, workforce, targets, directives)

        Returns:
            Чистая структура true.json v3.0
        """
        # Загружаем эталонный шаблон
        with open(self.template_path, 'r', encoding='utf-8') as f:
            truth_data = json.load(f)

        # Генерируем ID проекта
        project_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()

        # Заполняем базовую информацию о проекте
        truth_data["project"] = {
            "id": project_id,
            "name": project_name,
            "source_file": source_file,
            "created_at": now,
            "updated_at": now,
            "user_id": user_id,
            "status": "created"
        }

        # Применяем конфигурацию
        truth_data["configuration"].update(project_config)

        # Добавляем запись в audit log
        self._add_audit_log(truth_data, "system", "project_created", {
            "source_file": source_file,
            "project_id": project_id
        })

        logger.info(f"🆕 Создан проект v3.0: {project_name} (ID: {project_id})")
        return truth_data

    def update_agent_status(self, truth_data: Dict[str, Any], agent_name: str,
                           status: str, result_summary: Dict[str, Any] = None) -> None:
        """
        Обновляет статус агента в pipeline

        Args:
            truth_data: Структура true.json
            agent_name: Название агента
            status: Статус (pending, in_progress, completed, error)
            result_summary: Краткая сводка результатов
        """
        now = datetime.now().isoformat()

        agent_info = truth_data["pipeline"]["agents"].get(agent_name, {})

        if status == "in_progress":
            agent_info.update({
                "status": status,
                "started_at": now,
                "completed_at": None
            })
        elif status in ["completed", "error"]:
            agent_info.update({
                "status": status,
                "completed_at": now,
                "result_summary": result_summary or {}
            })
        else:
            agent_info["status"] = status

        truth_data["pipeline"]["agents"][agent_name] = agent_info
        truth_data["project"]["updated_at"] = now

        # Обновляем общий статус пайплайна
        if status == "completed":
            self._update_pipeline_stage(truth_data, agent_name)

        # Добавляем в audit log
        self._add_audit_log(truth_data, agent_name, f"agent_{status}", {
            "agent": agent_name,
            "result_summary": result_summary
        })

        logger.info(f"📊 Агент {agent_name}: {status}")

    def add_source_work_items(self, truth_data: Dict[str, Any], work_items: List[Dict[str, Any]]) -> None:
        """
        Добавляет исходные work_items от extractor
        """
        truth_data["source_data"]["work_items"] = work_items

        # Обновляем summary
        truth_data["project_summary"]["totals"]["work_items"] = len(work_items)

        logger.info(f"📋 Добавлено {len(work_items)} исходных работ")

    def update_classifications(self, truth_data: Dict[str, Any], classification_stats: Dict[str, int]) -> None:
        """
        Обновляет статистику классификации
        """
        totals = truth_data["project_summary"]["totals"]
        totals.update({
            "work_items": classification_stats.get("work_items", 0),
            "materials": classification_stats.get("materials", 0),
            "other_items": classification_stats.get("other_items", 0)
        })

        logger.info(f"🏷️ Обновлена статистика классификации: {classification_stats}")

    def set_project_hierarchy(self, truth_data: Dict[str, Any], hierarchy: List[Dict[str, Any]]) -> None:
        """
        Устанавливает иерархическую структуру проекта
        """
        truth_data["project_hierarchy"] = hierarchy

        # Подсчитываем категории и пакеты
        categories = len([item for item in hierarchy if item.get("type") == "category"])
        packages = len([item for item in hierarchy if item.get("type") == "package"])

        truth_data["project_summary"]["totals"].update({
            "categories": categories,
            "packages": packages
        })

        logger.info(f"🏗️ Установлена иерархия: {categories} категорий, {packages} пакетов")

    def update_timeline_summary(self, truth_data: Dict[str, Any], timeline_summary: Dict[str, Any]) -> None:
        """
        Обновляет сводку по календарному плану
        """
        truth_data["project_summary"]["timeline_summary"].update(timeline_summary)

        logger.info(f"📅 Обновлена сводка календарного плана")

    def save_project(self, truth_data: Dict[str, Any], project_path: str) -> str:
        """
        Сохраняет проект в файл true.json

        Returns:
            Путь к сохраненному файлу
        """
        truth_path = os.path.join(project_path, "true.json")

        # Обновляем timestamp
        truth_data["project"]["updated_at"] = datetime.now().isoformat()

        # Сохраняем файл
        with open(truth_path, 'w', encoding='utf-8') as f:
            json.dump(truth_data, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 Проект сохранен: {truth_path}")
        return truth_path

    def copy_to_agent_folder(self, truth_data: Dict[str, Any], agent_folder: str,
                            filename: str = "updated_true.json") -> str:
        """
        Копирует true.json в папку агента для отладки
        """
        agent_truth_path = os.path.join(agent_folder, filename)

        with open(agent_truth_path, 'w', encoding='utf-8') as f:
            json.dump(truth_data, f, ensure_ascii=False, indent=2)

        logger.info(f"📁 Скопирован в папку агента: {agent_truth_path}")
        return agent_truth_path

    def _update_pipeline_stage(self, truth_data: Dict[str, Any], completed_agent: str) -> None:
        """
        Обновляет общий статус пайплайна на основе завершенного агента
        """
        stage_mapping = {
            "extractor": "extracted",
            "classifier": "classified",
            "preparer": "prepared",
            "work_packager": "packaged",
            "works_to_packages": "assigned",
            "counter": "calculated",
            "scheduler": "completed"
        }

        if completed_agent in stage_mapping:
            truth_data["pipeline"]["current_stage"] = stage_mapping[completed_agent]

        # Если все агенты завершены, проект completed
        agents = truth_data["pipeline"]["agents"]
        if all(agent.get("status") == "completed" for agent in agents.values()):
            truth_data["pipeline"]["current_stage"] = "completed"
            truth_data["project"]["status"] = "completed"

    def _add_audit_log(self, truth_data: Dict[str, Any], agent: str, action: str, details: Dict[str, Any]) -> None:
        """
        Добавляет запись в audit log
        """
        truth_data["audit_log"].append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "details": details
        })

# Глобальный экземпляр менеджера
truth_manager = TruthManagerV3()

# Функции совместимости с существующим кодом
def update_pipeline_status(truth_path: str, agent_name: str, status: str, result_summary: Dict[str, Any] = None):
    """
    Функция совместимости для обновления статуса агента
    """
    try:
        with open(truth_path, 'r', encoding='utf-8') as f:
            truth_data = json.load(f)

        truth_manager.update_agent_status(truth_data, agent_name, status, result_summary)

        with open(truth_path, 'w', encoding='utf-8') as f:
            json.dump(truth_data, f, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ Ошибка обновления статуса {agent_name}: {e}")