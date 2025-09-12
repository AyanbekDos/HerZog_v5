"""
Модуль PREPARER для HerZog v3.0
Задача: ОРКЕСТРАТОР - вызывает classifier.py и timeline_blocks.py, собирает результаты (Шаг 3 пайплайна)
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any
import os

from ..shared.timeline_blocks import generate_weekly_blocks

logger = logging.getLogger(__name__)


def filter_works_from_classified(classified_data: List[Dict]) -> List[Dict]:
    """
    Простая фильтрация работ + добавление структуры для AI-агентов
    
    Args:
        classified_data: Результат classifier.classify_estimates()
        
    Returns:
        Список работ в формате для AI-агентов
    """
    import uuid
    
    work_items = []
    
    for item in classified_data:
        if item.get('classification') == 'Работа':
            # Используем единый ID без вложенности - плоская структура
            work_item = {
                'id': item.get('id'),
                'source_file': item.get('source_file'),
                'position_num': item.get('position_num'),
                'code': item.get('code'),
                'name': item.get('name'),
                'unit': item.get('unit'),
                'quantity': item.get('quantity'),
                'classification': item.get('classification')
                # Поля group_id, group_name добавят AI-агенты при необходимости
            }
            
            work_items.append(work_item)
    
    logger.info(f"Отфильтровано {len(work_items)} рабочих позиций из {len(classified_data)}")
    return work_items


def prepare_project_data(raw_estimates_file: str, directives_file: str) -> Dict[str, Any]:
    """
    ОРКЕСТРАТОР: Вызывает модули и собирает результаты в project_data.json
    
    Args:
        raw_estimates_file: Путь к файлу raw_estimates.json (из extractor)
        directives_file: Путь к файлу directives.json
        
    Returns:
        Единый словарь с данными проекта
    """
    
    logger.info("🎭 PREPARER: Начинаю оркестрацию модулей...")
    
    # ШАГ 1: Читаем уже готовые классифицированные данные
    logger.info("📋 Читаю классифицированные данные...")
    classified_file = raw_estimates_file.replace('1_extracted/raw_estimates.json', '2_classified/classified_estimates.json')
    
    with open(classified_file, 'r', encoding='utf-8') as f:
        classified_data = json.load(f)
    
    # ШАГ 2: Читаем директивы пользователя
    with open(directives_file, 'r', encoding='utf-8') as f:
        directives = json.load(f)
    
    logger.info(f"📄 Загружены директивы пользователя")
    
    # ШАГ 3: Фильтруем только работы для AI-агентов
    work_items = filter_works_from_classified(classified_data)
    
    # ШАГ 4: Вызываем TIMELINE_BLOCKS для создания недельных блоков
    timeline = directives.get('project_timeline', {})
    start_date = timeline.get('start_date', '01.01.2024')
    end_date = timeline.get('end_date', '31.12.2024')
    
    logger.info(f"📅 Вызываю TIMELINE_BLOCKS для диапазона {start_date} - {end_date}")
    timeline_result = generate_weekly_blocks(start_date, end_date)
    timeline_blocks = timeline_result['blocks']
    
    # ШАГ 5: Собираем единый project_data.json
    project_data = {
        'meta': {
            'created_at': datetime.now().isoformat(),
            'total_work_items': len(work_items),
            'total_timeline_blocks': len(timeline_blocks),
            'project_duration_weeks': len(timeline_blocks)
        },
        'directives': directives,
        'timeline_blocks': timeline_blocks,
        'work_items': work_items,
        'processing_status': {
            'extraction': 'completed',
            'classification': 'completed', 
            'preparation': 'completed',
            'conceptualization': 'pending',
            'scheduling': 'pending',
            'accounting': 'pending',
            'staffing': 'pending',
            'reporting': 'pending'
        },
        'groups_data': {}
    }
    
    logger.info(f"✅ PREPARER завершен: {len(work_items)} работ, {len(timeline_blocks)} недель")
    
    return project_data


def validate_project_data(project_data: Dict) -> bool:
    """
    Валидация подготовленных данных проекта
    
    Args:
        project_data: Словарь с данными проекта
        
    Returns:
        True если данные валидны
    """
    required_keys = ['meta', 'directives', 'timeline_blocks', 'work_items']
    
    for key in required_keys:
        if key not in project_data:
            logger.error(f"Отсутствует обязательное поле: {key}")
            return False
    
    if not project_data['work_items']:
        logger.error("Нет рабочих позиций для обработки")
        return False
    
    if not project_data['timeline_blocks']:
        logger.error("Не созданы временные блоки")
        return False
    
    # Проверяем структуру рабочих позиций
    for item in project_data['work_items']:
        required_item_keys = ['id', 'source_file', 'code', 'name']
        for key in required_item_keys:
            if key not in item:
                logger.error(f"Отсутствует поле {key} в рабочей позиции")
                return False
    
    logger.info("Валидация проектных данных успешна")
    return True


if __name__ == "__main__":
    import sys
    
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        # Режим реального использования - аргумент = путь к проекту
        project_dir = sys.argv[1]
        raw_estimates_file = os.path.join(project_dir, '1_extracted', 'raw_estimates.json')
        directives_file = os.path.join(project_dir, '0_input', 'directives.json')
        
        # Проверяем что файлы существуют
        if not os.path.exists(raw_estimates_file):
            logger.error(f"Не найден файл: {raw_estimates_file}")
            sys.exit(1)
            
        if not os.path.exists(directives_file):
            logger.error(f"Не найден файл: {directives_file}")
            sys.exit(1)
        
        # Запускаем обработку
        try:
            result = prepare_project_data(raw_estimates_file, directives_file)
            is_valid = validate_project_data(result)
            
            # Сохраняем результат
            output_file = os.path.join(project_dir, '3_prepared', 'project_data.json')
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Результат сохранен: {output_file}")
            print(f"Подготовка завершена. Валидность: {is_valid}")
            print(f"Рабочих позиций: {len(result['work_items'])}")
            print(f"Временных блоков: {len(result['timeline_blocks'])}")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке: {e}")
            sys.exit(1)
    
    else:
        # Режим тестирования - без аргументов
        logger.info("Режим тестирования preparer...")
        
        # Тестовые данные директив
        test_directives = {
            'target_work_count': 15,
            'project_timeline': {
                'start_date': '01.01.2024',
                'end_date': '30.06.2024'
            },
            'workforce_range': {'min': 10, 'max': 20}
        }
        
        # Тестовые классифицированные данные
        test_classified = [
            {
                'id': 'test-1',
                'classification': 'Работа',
                'name': 'Тестовая работа 1',
                'code': 'ГЭСН-001',
                'quantity': '100',
                'source_file': 'test.xlsx',
                'position_num': '1',
                'unit': 'м2'
            },
            {
                'id': 'test-2', 
                'classification': 'Материал',
                'name': 'Тестовый материал',
                'code': 'ФССЦ-001',
                'source_file': 'test.xlsx',
                'position_num': '2',
                'unit': 'кг',
                'quantity': '1000'
            }
        ]
        
        # Временные файлы для тестирования
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f1:
            json.dump(test_classified, f1, ensure_ascii=False)
            classified_file = f1.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f2:
            json.dump(test_directives, f2, ensure_ascii=False)
            directives_file = f2.name
        
        try:
            result = prepare_project_data(classified_file, directives_file)
            is_valid = validate_project_data(result)
            
            print(f"Подготовка завершена. Валидность: {is_valid}")
            print(f"Рабочих позиций: {len(result['work_items'])}")
            print(f"Временных блоков: {len(result['timeline_blocks'])}")
            
        finally:
            # Очистка временных файлов
            os.unlink(classified_file)
            os.unlink(directives_file)