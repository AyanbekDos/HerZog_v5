#!/usr/bin/env python3
"""
Тестирование улучшенной системы обхода RECITATION
"""

import asyncio
import sys
import os

# Добавляем src в путь
sys.path.insert(0, '/home/imort/Herzog_v3')

from src.ai_agents.scheduler_and_staffer import run_scheduler_and_staffer

async def test_recitation_bypass():
    """Тест системы обхода RECITATION"""
    project_path = "/home/imort/Herzog_v3/projects/34975055/d490876a"
    
    print(f"🧪 Тестирование обхода RECITATION для проекта: {project_path}")
    
    if not os.path.exists(project_path):
        print(f"❌ Проект не найден: {project_path}")
        return
    
    try:
        result = await run_scheduler_and_staffer(project_path)
        
        if result.get('success', False):
            print("✅ УСПЕХ! Система обхода RECITATION работает!")
            print(f"📊 Результат: {result}")
        else:
            print("❌ НЕУДАЧА!")
            print(f"📊 Ошибка: {result.get('error', 'Неизвестная ошибка')}")
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_recitation_bypass())