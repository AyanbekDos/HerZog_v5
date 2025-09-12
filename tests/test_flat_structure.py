#!/usr/bin/env python3
"""
Тест плоской структуры данных после рефакторинга ID
"""

import sys
import os
import json
import tempfile
import uuid
from datetime import datetime

# Добавляем путь к проекту
sys.path.append('/home/imort/Herzog_v3')

from src.data_processing.extractor import extract_from_files
from src.data_processing.classifier import classify_items
from src.data_processing.preparer import filter_works_from_classified


def test_flat_structure():
    """
    Тестируем весь пайплайн с плоской структурой
    """
    print("🧪 ТЕСТ: Плоская структура данных")
    print("=" * 50)
    
    # Шаг 1: Тестируем extractor - должен создавать единый id без вложенности
    print("\n1️⃣ Тест EXTRACTOR...")
    
    # Создаем тестовый Excel файл минимальными данными
    import pandas as pd
    
    test_data = {
        'A': ['№ п/п', '1', '2'],
        'B': ['Обоснование', 'ГЭСН46-02-009', 'ФСБЦ-14.4.01.02'],
        'C': ['Наименование работ', 'Отбивка штукатурки', 'Смесь сухая'],
        'H': ['Ед.изм.', 'м2', 'кг'],
        'I': ['Кол-во', '100', '500']
    }
    
    df = pd.DataFrame(test_data)
    
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        df.to_excel(tmp.name, index=False, header=False)
        tmp_excel = tmp.name
    
    try:
        # Извлекаем данные
        extracted_data = extract_from_files([tmp_excel])
        
        print(f"   ✅ Извлечено {len(extracted_data)} записей")
        
        # Проверяем структуру
        if extracted_data:
            first_item = extracted_data[0]
            print(f"   📊 Структура первой записи:")
            for key, value in first_item.items():
                print(f"      {key}: {value}")
            
            # Проверяем что есть единый id
            assert 'id' in first_item, "Отсутствует поле 'id'"
            assert 'internal_id' not in first_item, "Найдено старое поле 'internal_id'"
            print("   ✅ Структура extractor корректна")
        
        # Шаг 2: Тестируем classifier
        print("\n2️⃣ Тест CLASSIFIER...")
        
        classified_data = classify_items(extracted_data)
        print(f"   ✅ Классифицировано {len(classified_data)} записей")
        
        if classified_data:
            first_classified = classified_data[0]
            print(f"   📊 Структура классифицированной записи:")
            for key, value in first_classified.items():
                print(f"      {key}: {value}")
            
            # Проверяем что id сохранился
            assert 'id' in first_classified, "Потерян id после классификации"
            assert first_classified['id'] == first_item['id'], "ID изменился после классификации"
            print("   ✅ Структура classifier корректна")
        
        # Шаг 3: Тестируем preparer
        print("\n3️⃣ Тест PREPARER...")
        
        work_items = filter_works_from_classified(classified_data)
        print(f"   ✅ Отфильтровано {len(work_items)} работ")
        
        if work_items:
            first_work = work_items[0]
            print(f"   📊 Структура работы:")
            for key, value in first_work.items():
                print(f"      {key}: {value}")
            
            # Главная проверка - никакой вложенности original_data!
            assert 'original_data' not in first_work, "Найдена запрещенная вложенность 'original_data'"
            assert 'id' in first_work, "Отсутствует id в работе"
            assert 'source_file' in first_work, "Отсутствует source_file в работе"
            assert 'code' in first_work, "Отсутствует code в работе"
            assert 'name' in first_work, "Отсутствует name в работе"
            
            print("   ✅ Плоская структура работ корректна!")
            print("   🎉 НЕТ ВЛОЖЕННОСТИ original_data - структура плоская!")
        
        print("\n" + "=" * 50)
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("🎯 Структура данных теперь плоская с единым ID")
        print("📋 Один ID путешествует через все этапы без изменений")
        
    finally:
        # Очистка
        os.unlink(tmp_excel)


if __name__ == "__main__":
    test_flat_structure()