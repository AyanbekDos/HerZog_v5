"""
Модуль пошагового опроса пользователя для сбора директив проекта
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Dict, Any

class ProjectQuestionnaire:
    """Класс для управления пошаговым опросом пользователя"""
    
    def __init__(self):
        self.steps = [
            'files',           # Загрузка файлов смет
            'work_count',      # Количество строк в графике
            'timeline',        # Диапазон дат проекта  
            'workforce',       # Количество рабочих
            'conceptualizer',  # Директивы для концептуализатора
            'strategist',      # Директивы для стратега
            'accountant',      # Директивы для бухгалтера
            'foreman',         # Директивы для прораба
            'confirm'          # Подтверждение и запуск
        ]
    
    def get_current_step(self, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Получить текущий шаг опроса"""
        return context.user_data.get('current_step', 'files')
    
    def next_step(self, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Перейти к следующему шагу"""
        current = self.get_current_step(context)
        try:
            current_idx = self.steps.index(current)
            next_step = self.steps[current_idx + 1] if current_idx + 1 < len(self.steps) else 'confirm'
            context.user_data['current_step'] = next_step
            return next_step
        except ValueError:
            return 'files'
    
    def create_project_structure(self, user_id: int, project_id: str = None) -> str:
        """Создать структуру папок для проекта"""
        if not project_id:
            project_id = str(uuid.uuid4())[:8]
        
        project_path = f"projects/{user_id}/{project_id}"
        
        folders = [
            '0_input', '1_extracted', '2_classified', '3_prepared',
            '4_conceptualized', '5_scheduled', '6_accounted', 
            '7_staffed', '8_output'
        ]
        
        for folder in folders:
            os.makedirs(f"{project_path}/{folder}", exist_ok=True)
        
        return project_path
    
    def save_directives(self, context: ContextTypes.DEFAULT_TYPE, project_path: str):
        """Сохранить собранные директивы в файл"""
        directives = {
            'target_work_count': context.user_data.get('work_count', 15),
            'project_timeline': context.user_data.get('timeline', {}),
            'workforce_range': context.user_data.get('workforce', {}),
            'directives': {
                'conceptualizer': context.user_data.get('conceptualizer', ''),
                'strategist': context.user_data.get('strategist', ''), 
                'accountant': context.user_data.get('accountant', ''),
                'foreman': context.user_data.get('foreman', '')
            },
            'created_at': datetime.now().isoformat()
        }
        
        directives_path = f"{project_path}/0_input/directives.json"
        with open(directives_path, 'w', encoding='utf-8') as f:
            json.dump(directives, f, ensure_ascii=False, indent=2)
        
        return directives_path

# Сообщения для каждого шага
STEP_MESSAGES = {
    'files': "📁 **Шаг 1/8: Загрузка файлов**\n\nПришлите файлы сметы (.xlsx)\nМожете добавить несколько файлов или нажать /next для перехода к следующему шагу.",
    
    'work_count': "📊 **Шаг 2/8: Размер графика**\n\nУкажите желаемое количество строк в итоговом графике\n(например: 15)",
    
    'timeline': "📅 **Шаг 3/8: Временные рамки**\n\nУкажите диапазон дат проекта\nФормат: ДД.ММ.ГГГГ - ДД.ММ.ГГГГ\n(например: 01.01.2024 - 30.06.2024)",
    
    'workforce': "👷 **Шаг 4/8: Трудовые ресурсы**\n\nУкажите количество рабочих на площадке\nМожно диапазоном (например: 10-20) или точное число",
    
    'conceptualizer': "🎯 **Шаг 5/8: Группировка работ**\n\nЕсть ли особые указания по ГРУППИРОВКЕ работ?\n(Например: 'всю электрику в один блок, а полы не трогай')\n\nИли нажмите /skip для пропуска",
    
    'strategist': "📋 **Шаг 6/8: Планирование этапов**\n\nЕсть ли особые указания по ПЛАНИРОВАНИЮ этапов?\n(Например: 'растяни демонтаж на весь первый месяц')\n\nИли нажмите /skip для пропуска",
    
    'accountant': "💰 **Шаг 7/8: Подсчет объемов**\n\nЕсть ли особые указания по ПОДСЧЕТУ объемов?\n(Например: 'при объединении полов считай только площадь')\n\nИли нажмите /skip для пропуска",
    
    'foreman': "⚡ **Шаг 8/8: Распределение людей**\n\nЕсть ли особые указания по РАСПРЕДЕЛЕНИЮ людей?\n(Например: 'на отделку кинь максимум людей')\n\nИли нажмите /skip для пропуска",
    
    'confirm': "✅ **Готово к обработке!**\n\nВсе данные собраны. Нажмите /process для запуска обработки сметы."
}