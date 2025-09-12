"""
Отдельный модуль для запуска пайплайна без циклических импортов
"""

import logging
import asyncio
from typing import Dict

logger = logging.getLogger(__name__)

async def launch_pipeline(project_path: str) -> Dict:
    """
    Запуск главного пайплайна HerZog v3.0
    
    Args:
        project_path: Путь к проекту
        
    Returns:
        Результат выполнения пайплайна
    """
    try:
        logger.info(f"🚀 Запуск пайплайна для проекта: {project_path}")
        
        # Импортируем пайплайн
        from .main_pipeline import run_pipeline
        
        # Запускаем пайплайн
        result = await run_pipeline(project_path)
        
        logger.info(f"📊 Пайплайн завершен: success={result.get('success')}")
        
        return result
        
    except Exception as e:
        logger.error(f"💥 Ошибка в pipeline_launcher: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'project_path': project_path
        }