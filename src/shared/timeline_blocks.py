"""
Модуль для формирования временной сетки по неделям (БЛОКАМ) с учетом праздников РФ
Создает структуру недель с понедельника по пятницу, исключая праздничные дни
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import holidays

# Получаем официальные праздники РФ через библиотеку holidays
def get_russian_holidays(year: int):
    """Получает официальные праздники РФ для указанного года"""
    return holidays.Russia(years=year)

class TimelineBlockGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._holidays_cache = {}  # Кэш для праздников по годам
        
    def generate_weekly_blocks(
        self, 
        start_date: str, 
        end_date: str, 
        max_workers_per_week: int = 15
    ) -> Dict[str, Any]:
        """
        Генерирует временные блоки (недели) с понедельника по пятницу
        
        Args:
            start_date: дата начала в формате YYYY-MM-DD
            end_date: дата окончания в формате YYYY-MM-DD
            max_workers_per_week: максимальное количество рабочих в неделю
            
        Returns:
            Dict с метаданными проекта и списком блоков
        """
        
        # Парсинг входных дат (поддерживаем оба формата)
        try:
            start_dt = datetime.strptime(start_date, "%d.%m.%Y").date()
        except ValueError:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            
        try:
            end_dt = datetime.strptime(end_date, "%d.%m.%Y").date()
        except ValueError:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        if start_dt > end_dt:
            raise ValueError("Дата начала не может быть позже даты окончания")
            
        blocks = []
        block_id = 1
        current_date = start_dt
        
        while current_date <= end_dt:
            # Найти начало недели (понедельник)
            monday = current_date - timedelta(days=current_date.weekday())
            # Если это первый блок, начать с фактической даты начала
            block_start = max(monday, start_dt)
            
            # Найти конец недели (пятница)
            friday = monday + timedelta(days=4)  # пятница = понедельник + 4 дня
            # Если это последний блок, закончить фактической датой окончания
            block_end = min(friday, end_dt)
            
            # Рассчитать рабочие дни с учетом праздников
            working_days, excluded_holidays = self._calculate_working_days(
                block_start, block_end
            )
            
            # Создать блок только если есть рабочие дни
            if working_days > 0:
                block = {
                    "block_id": block_id,
                    "start_date": block_start.strftime("%Y-%m-%d"),
                    "end_date": block_end.strftime("%Y-%m-%d"),
                    "working_days": working_days,
                    "excluded_holidays": excluded_holidays,
                    "calendar_days": (block_end - block_start).days + 1,
                    "is_partial_start": block_start > monday,
                    "is_partial_end": block_end < friday
                }
                blocks.append(block)
                block_id += 1
            
            # Переход к следующей неделе
            current_date = friday + timedelta(days=3)  # следующий понедельник
            
        result = {
            "project_metadata": {
                "start_date": start_date,
                "end_date": end_date,
                "total_blocks": len(blocks),
                "max_workers_per_week": max_workers_per_week,
                "created_at": datetime.now().isoformat() + "Z"
            },
            "blocks": blocks
        }
        
        self.logger.info(f"Сгенерировано {len(blocks)} блоков с {start_date} по {end_date}")
        return result
    
    def _calculate_working_days(self, start_date, end_date) -> tuple[int, List[str]]:
        """
        Рассчитывает количество рабочих дней исключая выходные и праздники
        
        Returns:
            tuple: (количество_рабочих_дней, список_исключенных_праздников)
        """
        working_days = 0
        excluded_holidays = []
        current = start_date
        
        while current <= end_date:
            # Проверяем, не выходной ли день (суббота=5, воскресенье=6)
            if current.weekday() < 5:  # понедельник=0, пятница=4
                # Проверяем, не праздник ли
                date_str = current.strftime("%Y-%m-%d")
                year = current.year
                
                # Получаем праздники для года с кэшированием
                if year not in self._holidays_cache:
                    self._holidays_cache[year] = get_russian_holidays(year)
                
                russian_holidays = self._holidays_cache[year]
                if current in russian_holidays:
                    excluded_holidays.append(date_str)
                else:
                    working_days += 1
            
            current += timedelta(days=1)
            
        return working_days, excluded_holidays
    
    def save_timeline_config(self, user_id: int, config: Dict[str, Any]) -> str:
        """
        Сохраняет конфигурацию временной сетки для пользователя
        
        Returns:
            str: путь к сохраненному файлу
        """
        # Создаем директорию если не существует
        sessions_dir = "/home/imort/Herzog_v2claude/data/sessions"
        os.makedirs(sessions_dir, exist_ok=True)
        
        filepath = f"{sessions_dir}/user_{user_id}_timeline.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"Сохранена конфигурация timeline для пользователя {user_id}")
        return filepath
    
    def load_timeline_config(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Загружает сохраненную конфигурацию временной сетки
        
        Returns:
            Optional[Dict]: конфигурация или None если файл не найден
        """
        filepath = f"/home/imort/Herzog_v2claude/data/sessions/user_{user_id}_timeline.json"
        
        if not os.path.exists(filepath):
            return None
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.logger.info(f"Загружена конфигурация timeline для пользователя {user_id}")
            return config
        except Exception as e:
            self.logger.error(f"Ошибка загрузки конфигурации для пользователя {user_id}: {e}")
            return None
    
    def format_blocks_summary(self, timeline_config: Dict[str, Any]) -> str:
        """
        Форматирует блоки в читаемый вид для отправки пользователю
        
        Returns:
            str: отформатированный текст с описанием блоков
        """
        blocks = timeline_config["blocks"]
        metadata = timeline_config["project_metadata"]
        
        summary = f"📅 *График проекта*\n"
        summary += f"Период: {metadata['start_date']} — {metadata['end_date']}\n"
        summary += f"Всего блоков: {metadata['total_blocks']}\n"
        summary += f"Макс. рабочих в неделю: {metadata['max_workers_per_week']}\n\n"
        
        for block in blocks:
            start_formatted = datetime.strptime(block['start_date'], "%Y-%m-%d").strftime("%d %b %y")
            end_formatted = datetime.strptime(block['end_date'], "%Y-%m-%d").strftime("%d %b %y")
            
            summary += f"*Блок {block['block_id']}*: "
            summary += f"{start_formatted} — {end_formatted}, "
            summary += f"{block['working_days']} рабочих дн"
            
            if block['excluded_holidays']:
                summary += f" (праздники: {', '.join([datetime.strptime(h, '%Y-%m-%d').strftime('%d.%m') for h in block['excluded_holidays']])})"
            
            summary += "\n"
        
        return summary

# Функции для backward compatibility
def generate_weekly_blocks(start_date: str, end_date: str, max_workers_per_week: int = 15) -> Dict[str, Any]:
    """Wrapper функция для совместимости"""
    generator = TimelineBlockGenerator()
    return generator.generate_weekly_blocks(start_date, end_date, max_workers_per_week)

def save_timeline_config(user_id: int, config: Dict[str, Any]) -> str:
    """Wrapper функция для совместимости"""
    generator = TimelineBlockGenerator()
    return generator.save_timeline_config(user_id, config)

def load_timeline_config(user_id: int) -> Optional[Dict[str, Any]]:
    """Wrapper функция для совместимости"""  
    generator = TimelineBlockGenerator()
    return generator.load_timeline_config(user_id)

# Тестирование модуля
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generator = TimelineBlockGenerator()
    
    # Тестовый пример: 2 сентября 2025 - 9 октября 2025
    test_config = generator.generate_weekly_blocks(
        start_date="2025-09-02",
        end_date="2025-10-09", 
        max_workers_per_week=15
    )
    
    print("Тестовая конфигурация временных блоков:")
    print(json.dumps(test_config, ensure_ascii=False, indent=2))
    
    print("\nФорматированный вывод:")
    print(generator.format_blocks_summary(test_config))