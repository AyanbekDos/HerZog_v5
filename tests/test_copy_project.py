#!/usr/bin/env python3
"""
Тестирование функции копирования проекта до определенного этапа
"""

import os
import sys
import shutil
import tempfile

# Добавляем путь к модулям Herzog
sys.path.append('/home/imort/Herzog_v3')

from src.telegram_bot.handlers import _copy_project_files_up_to_stage

def test_copy_function():
    """Тестирует функцию копирования файлов проекта"""
    
    source_project = "/home/imort/Herzog_v3/projects/34975055/da1ac471"
    
    print(f"🧪 Тестирование копирования проекта из: {source_project}")
    
    # Создаем временную папку для тестирования
    with tempfile.TemporaryDirectory() as temp_dir:
        target_project = os.path.join(temp_dir, "test_project")
        os.makedirs(target_project, exist_ok=True)
        
        # Тестируем разные этапы
        test_stages = ["0", "3", "5", "6", "8"]
        
        for stage in test_stages:
            print(f"\n🔄 Тестирование этапа {stage}...")
            
            # Очищаем папку назначения
            if os.path.exists(target_project):
                shutil.rmtree(target_project)
            os.makedirs(target_project)
            
            # Копируем файлы
            success = _copy_project_files_up_to_stage(source_project, target_project, stage)
            
            if success:
                # Проверяем что скопировалось
                copied_folders = []
                for item in os.listdir(target_project):
                    if os.path.isdir(os.path.join(target_project, item)):
                        copied_folders.append(item)
                
                copied_folders.sort()
                print(f"   ✅ Успешно скопированы папки: {copied_folders}")
                
                # Проверяем true.json
                truth_file = os.path.join(target_project, "true.json")
                if os.path.exists(truth_file):
                    file_size = os.path.getsize(truth_file)
                    print(f"   📄 true.json скопирован: {file_size} байт")
                else:
                    print("   ⚠️ true.json не найден")
                    
            else:
                print(f"   ❌ Ошибка копирования этапа {stage}")
    
    print(f"\n🎯 Тестирование завершено!")

if __name__ == "__main__":
    test_copy_function()