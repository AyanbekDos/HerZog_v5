"""
Универсальный оркестратор AI агентов системы HerZog v3.0
Управляет выполнением всех агентов по единой схеме
"""

import json
import logging
import os
import requests
from typing import Dict, Any
from dotenv import load_dotenv

# Старые импорты удалены - используем новую архитектуру

load_dotenv()

def load_prompt_template(prompt_file: str) -> str:
    """
    Загружает шаблон промпта из файла
    
    Args:
        prompt_file: Имя файла промпта
        
    Returns:
        Содержимое промпта
    """
    try:
        prompt_path = os.path.join(os.path.dirname(__file__), '../prompts', prompt_file)
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.error(f"Ошибка загрузки промпта {prompt_file}: {e}")
        raise

def call_gemini_api(prompt: str) -> str:
    """
    Вызывает Gemini API с промптом
    
    Args:
        prompt: Готовый промпт для LLM
        
    Returns:
        Ответ от LLM
    """
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("Не найден API ключ GEMINI_API_KEY")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 8192
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            raise Exception(f"Ошибка API Gemini: {response.status_code} - {response.text}")
            
    except Exception as e:
        logging.error(f"Ошибка при вызове Gemini API: {e}")
        raise

def run_agent(agent_name: str, project_dir: str) -> bool:
    """
    ОБНОВЛЕННАЯ ФУНКЦИЯ: Использует новую архитектуру true.json
    
    Args:
        agent_name: Имя агента из agent_config
        project_dir: Путь к директории проекта
        
    Returns:
        True если агент выполнен успешно
    """
    
    logging.warning(f"🔄 DEPRECATED: Функция run_agent устарела для агента '{agent_name}'")
    logging.warning("💡 Используйте main_pipeline.py для запуска новых агентов")
    
    # Для совместимости возвращаем False - новые агенты должны запускаться через main_pipeline
    return False

def run_pipeline(project_dir: str, start_from: str = "work_packager") -> bool:
    """
    DEPRECATED: Используется новая архитектура через main_pipeline.py
    
    Args:
        project_dir: Путь к директории проекта
        start_from: С какого агента начать выполнение
        
    Returns:
        True если все агенты выполнены успешно
    """
    
    logging.warning("🔄 Используется устаревшая функция run_pipeline. Переключаемся на main_pipeline.py")
    
    # Импортируем новую логику
    from ..main_pipeline import run_pipeline as new_run_pipeline
    import asyncio
    
    try:
        result = asyncio.run(new_run_pipeline(project_dir))
        return result.get('success', False)
    except Exception as e:
        logging.error(f"Ошибка в новом пайплайне: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    # Настройка логирования для тестирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) == 3:
        # Запуск с аргументами: agent_name project_dir
        agent_name = sys.argv[1]
        project_dir = sys.argv[2]
        print(f"🚀 Запуск агента '{agent_name}' для проекта {project_dir}")
        success = run_agent(agent_name, project_dir)
        print(f"Результат: {'✅ Успех' if success else '❌ Ошибка'}")
    else:
        # Тестирование на проекте
        test_project_dir = "/home/imort/Herzog_v3/projects/34975055/d19120ef"
        
        print("🧪 Тестирование agent_runner...")
        
        if os.path.exists(test_project_dir):
            # Тестируем только первого агента
            success = run_agent("1.1_group_creator", test_project_dir)
            print(f"Результат теста: {'✅ Успех' if success else '❌ Ошибка'}")
        else:
            print(f"❌ Тестовый проект не найден: {test_project_dir}")