#!/usr/bin/env python3
"""
Тест для проверки фильтрации в preparer.py
Проверяем что в project_data.json попадают только работы
"""

import json
import tempfile
import os
import sys
sys.path.append('/home/imort/Herzog_v3')

from src.data_processing.preparer import prepare_project_data

def test_preparer_filtering():
    """Тест фильтрации: только работы должны попасть в project_data.json"""
    
    # Создаем тестовые данные с работами, материалами и "иное"
    test_classified_data = [
        {
            'internal_id': 'work-1',
            'classification': 'Работа',
            'source_file': 'test.xlsx',
            'position_num': '1',
            'code': 'ГЭСН46-02-009-02',
            'name': 'Отбивка штукатурки',
            'unit': '100 м2',
            'quantity': '7.77'
        },
        {
            'internal_id': 'material-1',
            'classification': 'Материал', 
            'source_file': 'test.xlsx',
            'position_num': '2',
            'code': 'ФСБЦ-14.4.01.02-0012',
            'name': 'Смесь сухая штукатурная',
            'unit': 'кг',
            'quantity': '1000'
        },
        {
            'internal_id': 'work-2',
            'classification': 'Работа',
            'source_file': 'test.xlsx', 
            'position_num': '3',
            'code': 'ГЭСН46-01-001-01',
            'name': 'Демонтаж перегородок',
            'unit': '100 м2',
            'quantity': '5.5'
        },
        {
            'internal_id': 'other-1',
            'classification': 'Иное',
            'source_file': 'test.xlsx',
            'position_num': '4', 
            'code': 'НР-001',
            'name': 'Накладные расходы',
            'unit': '%',
            'quantity': '15'
        }
    ]
    
    test_directives = {
        'target_work_count': 15,
        'project_timeline': {
            'start_date': '01.01.2024',
            'end_date': '31.01.2024'
        },
        'workforce_range': {'min': 10, 'max': 20}
    }
    
    # Создаем временные файлы
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f1:
        json.dump(test_classified_data, f1, ensure_ascii=False, indent=2)
        classified_file = f1.name
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f2:
        json.dump(test_directives, f2, ensure_ascii=False, indent=2)
        directives_file = f2.name
    
    try:
        # Тестируем preparer
        result = prepare_project_data(classified_file, directives_file)
        
        print(f"📊 Исходных позиций всего: {len(test_classified_data)}")
        print(f"   - Работ: {len([x for x in test_classified_data if x['classification'] == 'Работа'])}")
        print(f"   - Материалов: {len([x for x in test_classified_data if x['classification'] == 'Материал'])}")
        print(f"   - Иное: {len([x for x in test_classified_data if x['classification'] == 'Иное'])}")
        
        work_items = result.get('work_items', [])
        print(f"\n🎯 В project_data.json попало позиций: {len(work_items)}")
        
        # Проверяем что все позиции - работы
        for i, item in enumerate(work_items):
            original = item.get('original_data', {})
            classification = original.get('classification')
            name = original.get('name', 'Без названия')
            print(f"   {i+1}. {name} - {classification}")
            
            if classification != 'Работа':
                print(f"❌ ОШИБКА: позиция {i+1} не является работой!")
                return False
        
        # Проверяем мета-данные
        meta = result.get('meta', {})
        total_work_items = meta.get('total_work_items', 0)
        
        print(f"\n📋 Метаданные:")
        print(f"   total_work_items: {total_work_items}")
        print(f"   timeline_blocks: {meta.get('total_timeline_blocks', 0)}")
        
        if total_work_items == 2:  # Ожидаем 2 работы
            print("✅ Фильтрация работает правильно!")
            return True
        else:
            print(f"❌ Ошибка в метаданных: ожидали 2 работы, получили {total_work_items}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False
        
    finally:
        # Чистим временные файлы
        try:
            os.unlink(classified_file)
            os.unlink(directives_file)
        except:
            pass

if __name__ == "__main__":
    success = test_preparer_filtering()
    if success:
        print("\n🎉 Все тесты пройдены!")
    else:
        print("\n💥 Есть проблемы с фильтрацией!")
        sys.exit(1)