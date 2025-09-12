#!/usr/bin/env python3
"""
Тест исправленного классификатора с обработкой неопределенных позиций через Gemini
"""

import sys
import os
import logging

# Добавляем путь к модулям
sys.path.append('/home/imort/Herzog_v3')

from src.data_processing.classifier import classify_estimates

def test_classifier():
    """Тестируем классификатор на реальных данных"""
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Путь к файлу с извлеченными данными  
    input_file = "/home/imort/Herzog_v3/projects/34975055/d19120ef/1_extracted/raw_estimates.json"
    
    print("🧪 Запуск теста классификатора...")
    print(f"📁 Входной файл: {input_file}")
    
    try:
        # Классифицируем данные
        classified_data = classify_estimates(input_file)
        
        # Статистика
        classifications = [item['classification'] for item in classified_data]
        work_count = classifications.count('Работа')
        material_count = classifications.count('Материал')
        other_count = classifications.count('Иное')
        unknown_count = classifications.count('Неопределенное')
        
        print("\n📊 Результаты классификации:")
        print(f"  Работ: {work_count}")
        print(f"  Материалов: {material_count}")
        print(f"  Иное: {other_count}")
        print(f"  Неопределенных: {unknown_count}")
        print(f"  Всего: {len(classified_data)}")
        
        if unknown_count == 0:
            print("✅ Все позиции успешно классифицированы!")
        else:
            print(f"⚠️  Осталось {unknown_count} неопределенных позиций")
            
        # Проверяем, созданы ли llm файлы
        project_dir = "/home/imort/Herzog_v3/projects/34975055/d19120ef"
        llm_input_path = f"{project_dir}/2_classified/llm_input.json"
        llm_response_path = f"{project_dir}/2_classified/llm_response.json"
        
        if os.path.exists(llm_input_path):
            print(f"✅ Создан llm_input.json")
        else:
            print(f"❌ Не найден llm_input.json")
            
        if os.path.exists(llm_response_path):
            print(f"✅ Создан llm_response.json")
        else:
            print(f"❌ Не найден llm_response.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_classifier()
    sys.exit(0 if success else 1)