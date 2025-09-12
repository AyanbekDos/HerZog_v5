#!/usr/bin/env python3
"""
Тест исправленного work_packager на реальном проекте
"""

import asyncio
import sys
import os

# Добавляем путь к модулям Herzog
sys.path.append('/home/imort/Herzog_v3')

from src.ai_agents.work_packager import run_work_packager

async def test_fixed_work_packager():
    """Тестируем исправленный work_packager"""
    
    print("🧪 Тестирование исправленного work_packager...")
    
    # Используем существующий проект 
    project_path = "/home/imort/Herzog_v3/projects/34975055/d490876a"
    
    if not os.path.exists(project_path):
        print(f"❌ Проект не найден: {project_path}")
        return False
    
    try:
        print(f"🔄 Запуск work_packager для проекта: {project_path}")
        
        result = await run_work_packager(project_path)
        
        if result['success']:
            packages_created = result.get('packages_created', 0)
            print(f"✅ Work_packager завершен успешно!")
            print(f"📊 Создано пакетов: {packages_created}")
            
            # Читаем обновленный true.json чтобы увидеть пакеты
            import json
            truth_path = os.path.join(project_path, "true.json")
            if os.path.exists(truth_path):
                with open(truth_path, 'r', encoding='utf-8') as f:
                    truth_data = json.load(f)
                
                work_packages = truth_data.get('results', {}).get('work_packages', [])
                print(f"📋 Найдено пакетов в true.json: {len(work_packages)}")
                
                for pkg in work_packages[:5]:  # Показываем первые 5
                    print(f"   - {pkg.get('package_id')}: {pkg.get('name')}")
            
            return True
            
        else:
            print(f"❌ Work_packager завершился с ошибкой: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_fixed_work_packager())