#!/usr/bin/env python3
"""
Тест полного пайплайна с исправлениями
"""

import asyncio
import sys
import os

# Добавляем путь к модулям Herzog
sys.path.append('/home/imort/Herzog_v3')

from src.ai_agents.counter import run_counter
from src.ai_agents.scheduler_and_staffer import run_scheduler_and_staffer
from src.data_processing.reporter_v3 import generate_multipage_excel_report

async def test_counter_and_scheduler():
    """Тестируем counter и scheduler_and_staffer с исправлениями"""
    
    print("🧪 Тестирование counter и scheduler_and_staffer с исправлениями...")
    
    # Используем существующий проект 
    project_path = "/home/imort/Herzog_v3/projects/34975055/d490876a"
    
    if not os.path.exists(project_path):
        print(f"❌ Проект не найден: {project_path}")
        return False
    
    try:
        # Шаг 1: Запускаем counter с исправленными лимитами токенов
        print(f"🔄 Запуск counter для проекта: {project_path}")
        counter_result = await run_counter(project_path)
        
        if not counter_result['success']:
            print(f"❌ Counter завершился с ошибкой: {counter_result.get('error')}")
            return False
        
        print(f"✅ Counter завершен успешно! Обработано пакетов: {counter_result.get('packages_processed', 0)}")
        
        # Шаг 2: Запускаем scheduler_and_staffer с обходом RECITATION
        print(f"🔄 Запуск scheduler_and_staffer для проекта: {project_path}")
        scheduler_result = await run_scheduler_and_staffer(project_path)
        
        if not scheduler_result['success']:
            print(f"❌ Scheduler_and_staffer завершился с ошибкой: {scheduler_result.get('error')}")
            return False
            
        print(f"✅ Scheduler_and_staffer завершен успешно! Обработано пакетов: {scheduler_result.get('packages_scheduled', 0)}")
        
        # Шаг 3: Генерируем Excel отчет
        print(f"🔄 Генерация Excel отчета...")
        try:
            truth_file = os.path.join(project_path, "true.json")
            output_folder = os.path.join(project_path, "8_output")
            os.makedirs(output_folder, exist_ok=True)
            
            excel_file = generate_multipage_excel_report(truth_file, output_folder)
            print(f"✅ Excel отчет создан: {excel_file}")
        except Exception as e:
            print(f"⚠️ Ошибка создания Excel: {e}")
        
        # Проверяем итоговые файлы
        output_folder = os.path.join(project_path, "8_output")
        if os.path.exists(output_folder):
            print(f"\n📁 Файлы в папке 8_output:")
            for file in os.listdir(output_folder):
                file_path = os.path.join(output_folder, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    print(f"   📄 {file} ({size} байт)")
        
        return True
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_counter_and_scheduler())