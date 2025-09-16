"""
НОВЫЙ Модуль PREPARER v3.0 для HerZog v3.0
Подготавливает данные в эталонной структуре, убирает legacy артефакты
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any
import os

from ..shared.timeline_blocks import generate_weekly_blocks
from ..shared.truth_initializer_v3 import truth_manager

logger = logging.getLogger(__name__)

class PreparerV3:
    """
    Новый preparer под эталонную структуру v3.0
    Создает ЧИСТУЮ структуру без legacy артефактов
    """

    def __init__(self):
        self.agent_name = "preparer"

    def prepare_project(self, project_name: str, source_file: str, user_id: str,
                       extracted_data: List[Dict], classified_data: List[Dict],
                       project_config: Dict[str, Any], output_dir: str) -> str:
        """
        Создает новый проект в эталонной структуре v3.0

        Args:
            project_name: Название проекта
            source_file: Исходный файл
            user_id: ID пользователя
            extracted_data: Сырые данные от extractor
            classified_data: Классифицированные данные
            project_config: Конфигурация проекта
            output_dir: Папка для сохранения

        Returns:
            Путь к true.json
        """
        logger.info(f"🔄 Создание проекта v3.0: {project_name}")

        # Создаем базовую структуру проекта
        truth_data = truth_manager.create_project(
            project_name=project_name,
            source_file=source_file,
            user_id=user_id,
            project_config=project_config
        )

        # Генерируем временные блоки
        timeline_blocks = self._generate_timeline_blocks(project_config.get("timeline", {}))
        truth_data["configuration"]["timeline"]["blocks"] = timeline_blocks

        # Подготавливаем work_items в чистом формате
        work_items = self._prepare_work_items(classified_data)
        truth_manager.add_source_work_items(truth_data, work_items)

        # Обновляем статистику классификации
        classification_stats = self._calculate_classification_stats(classified_data)
        truth_manager.update_classifications(truth_data, classification_stats)

        # Создаем папку проекта
        project_path = os.path.join(output_dir, truth_data["project"]["id"])
        os.makedirs(project_path, exist_ok=True)

        # Обновляем статус preparer
        truth_manager.update_agent_status(truth_data, "preparer", "completed", {
            "timeline_blocks_created": len(timeline_blocks),
            "work_items_prepared": len(work_items),
            "classification_stats": classification_stats
        })

        # Сохраняем проект
        truth_path = truth_manager.save_project(truth_data, project_path)

        # Копируем в папку preparer для отладки
        preparer_folder = os.path.join(project_path, "3_prepared")
        os.makedirs(preparer_folder, exist_ok=True)
        truth_manager.copy_to_agent_folder(truth_data, preparer_folder)

        logger.info(f"✅ Проект v3.0 создан: {truth_path}")
        return truth_path

    def _generate_timeline_blocks(self, timeline_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Генерирует временные блоки для проекта
        """
        start_date = timeline_config.get("start_date")
        end_date = timeline_config.get("end_date")

        if not start_date or not end_date:
            logger.error("❌ Не указаны даты начала/окончания проекта")
            return []

        blocks = generate_weekly_blocks(start_date, end_date)

        # Конвертируем в формат v3.0
        timeline_blocks = []
        for i, block in enumerate(blocks, 1):
            timeline_blocks.append({
                "week_id": i,
                "start_date": block["start_date"],
                "end_date": block["end_date"],
                "working_days": block["working_days"],
                "calendar_days": block["calendar_days"],
                "holidays": block.get("excluded_holidays", []),
                "is_partial_start": block.get("is_partial_start", False),
                "is_partial_end": block.get("is_partial_end", False)
            })

        logger.info(f"📅 Создано {len(timeline_blocks)} временных блоков")
        return timeline_blocks

    def _prepare_work_items(self, classified_data: List[Dict]) -> List[Dict[str, Any]]:
        """
        Подготавливает work_items в чистом формате v3.0
        """
        work_items = []

        for item in classified_data:
            # Включаем только работы (убираем материалы и прочее)
            if item.get('classification') != 'Работа':
                continue

            work_item = {
                "id": item.get('id'),
                "source_file": item.get('source_file'),
                "code": item.get('code'),
                "name": item.get('name'),
                "unit": item.get('unit'),
                "quantity": self._safe_float(item.get('quantity')),
                "classification": item.get('classification'),
                "classification_reasoning": item.get('reasoning', ''),
                "assigned_package_id": None,  # Будет заполнено works_to_packages
                "extracted_at": None,  # Можно добавить timestamp от extractor
                "classified_at": datetime.now().isoformat(),
                "assigned_at": None   # Будет заполнено works_to_packages
            }

            work_items.append(work_item)

        logger.info(f"📋 Подготовлено {len(work_items)} работ")
        return work_items

    def _calculate_classification_stats(self, classified_data: List[Dict]) -> Dict[str, int]:
        """
        Подсчитывает статистику классификации
        """
        stats = {
            "work_items": 0,
            "materials": 0,
            "other_items": 0
        }

        for item in classified_data:
            classification = item.get('classification', '')
            if classification == 'Работа':
                stats["work_items"] += 1
            elif classification == 'Материал':
                stats["materials"] += 1
            else:
                stats["other_items"] += 1

        logger.info(f"📊 Статистика: {stats}")
        return stats

    def _safe_float(self, value) -> float:
        """
        Безопасное преобразование в float
        """
        try:
            if isinstance(value, str):
                # Заменяем запятую на точку для русских чисел
                value = value.replace(',', '.')
            return float(value)
        except (ValueError, TypeError):
            return 0.0

# Функция совместимости для старого API
def prepare_project_legacy(extracted_data, classified_data, project_inputs, project_id, output_dir):
    """
    Функция совместимости со старым API
    """
    preparer = PreparerV3()

    # Извлекаем конфигурацию из старого формата
    project_config = {
        "timeline": {
            "start_date": project_inputs.get("project_timeline", {}).get("start_date"),
            "end_date": project_inputs.get("project_timeline", {}).get("end_date"),
        },
        "workforce": project_inputs.get("workforce_range", {}),
        "targets": {
            "package_count": project_inputs.get("target_work_package_count", 15)
        },
        "directives": project_inputs.get("agent_directives", {})
    }

    # Извлекаем мета-данные
    project_name = project_inputs.get("project_name", "Безымянный проект")
    source_file = "unknown.xlsx"  # В старом API не было
    user_id = "unknown"  # В старом API не было

    return preparer.prepare_project(
        project_name=project_name,
        source_file=source_file,
        user_id=user_id,
        extracted_data=extracted_data,
        classified_data=classified_data,
        project_config=project_config,
        output_dir=output_dir
    )