#!/usr/bin/env python3
"""
Симуляция команды /test с этапа 6 (counter)
"""

import os
import sys
import shutil
import tempfile

# Добавляем путь к модулям Herzog
sys.path.append('/home/imort/Herzog_v3')

from src.telegram_bot.handlers import _copy_project_files_up_to_stage

def simulate_test_stage_6():
    """Симулируем создание тестового проекта с этапа 6"""
    
    source_project = "/home/imort/Herzog_v3/projects/34975055/da1ac471"
    
    print("🧪 Симуляция команды /test с этапом 6 (counter)...")
    print(f"📁 Источник: {source_project}")
    
    # Создаем временную папку как если бы создал questionnaire.create_project_structure
    with tempfile.TemporaryDirectory() as temp_dir:
        target_project = os.path.join(temp_dir, "test_project")
        os.makedirs(target_project, exist_ok=True)
        
        print(f"📁 Цель: {target_project}")
        
        # Копируем файлы до этапа 6 (включительно)
        print("🔄 Копирование файлов...")
        success = _copy_project_files_up_to_stage(source_project, target_project, "6")
        
        if success:
            print("✅ Копирование успешно!")
            
            # Проверяем что скопировалось
            copied_folders = []
            for item in os.listdir(target_project):
                if os.path.isdir(os.path.join(target_project, item)):
                    copied_folders.append(item)
                    
            copied_folders.sort()
            print(f"📋 Скопированные папки: {copied_folders}")
            
            # Проверяем true.json
            truth_file = os.path.join(target_project, "true.json")
            if os.path.exists(truth_file):
                file_size = os.path.getsize(truth_file)
                print(f"📄 true.json: {file_size} байт")
                
                # Проверим сколько пакетов уже имеют volume_data
                import json
                with open(truth_file, 'r', encoding='utf-8') as f:
                    truth_data = json.load(f)
                
                work_packages = truth_data.get('results', {}).get('work_packages', [])
                packages_with_volume = [pkg for pkg in work_packages if 'volume_data' in pkg]
                
                print(f"📊 Пакетов всего: {len(work_packages)}")
                print(f"✅ С volume_data: {len(packages_with_volume)}")
                print(f"⏳ Осталось обработать: {len(work_packages) - len(packages_with_volume)}")
                
                # Проверим папку 6_counter
                counter_folder = os.path.join(target_project, "6_counter")
                if os.path.exists(counter_folder):
                    counter_files = os.listdir(counter_folder)
                    response_files = [f for f in counter_files if f.endswith('_response.json')]
                    print(f"📁 Файлов в 6_counter: {len(counter_files)}")
                    print(f"📋 Response файлов: {len(response_files)}")
                    
                    # Найдем последний обработанный и первый с ошибкой
                    success_responses = []
                    error_responses = []
                    
                    for resp_file in response_files:
                        resp_path = os.path.join(counter_folder, resp_file)
                        try:
                            with open(resp_path, 'r', encoding='utf-8') as f:
                                resp_data = json.load(f)
                                if resp_data.get('success'):
                                    success_responses.append(resp_file)
                                else:
                                    error_responses.append(resp_file)
                        except:
                            pass
                    
                    print(f"✅ Успешных ответов: {len(success_responses)}")
                    print(f"❌ Ошибок: {len(error_responses)}")
                    
                    if error_responses:
                        print(f"🚨 Первая ошибка в: {sorted(error_responses)[0]}")
            
            print(f"\n🎯 Результат:")
            print(f"   Тестовый проект готов к продолжению обработки")
            print(f"   Можно запустить pipeline с этапа 7 (scheduler_and_staffer)")
            print(f"   Counter частично обработал пакеты, можно продолжить")
                
        else:
            print("❌ Ошибка копирования!")

if __name__ == "__main__":
    simulate_test_stage_6()