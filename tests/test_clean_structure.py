#!/usr/bin/env python3
"""
Тест что в project_data.json нет лишних полей group_id, group_name
"""

import json
import tempfile
import os
import sys
sys.path.append('/home/imort/Herzog_v3')

from src.data_processing.preparer import prepare_project_data

def test_clean_structure():
    """Проверяем что нет лишних null полей"""
    
    test_raw_estimates = [
        {
            'internal_id': 'work-1',
            'source_file': 'test.xlsx',
            'position_num': '1',
            'code': 'ГЭСН46-02-009-02',
            'name': 'Отбивка штукатурки',
            'unit': '100 м2',
            'quantity': '7.77'
        }
    ]
    
    test_directives = {
        'target_work_count': 10,
        'project_timeline': {
            'start_date': '01.01.2024',
            'end_date': '07.01.2024'
        },
        'workforce_range': {'min': 5, 'max': 15}
    }
    
    # Временные файлы
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f1:
        json.dump(test_raw_estimates, f1, ensure_ascii=False)
        raw_estimates_file = f1.name
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f2:
        json.dump(test_directives, f2, ensure_ascii=False)
        directives_file = f2.name
    
    try:
        result = prepare_project_data(raw_estimates_file, directives_file)
        
        work_items = result.get('work_items', [])
        print(f"📋 Проверяю структуру работ...")
        
        for i, work_item in enumerate(work_items):
            print(f"   Work {i+1}:")
            for key, value in work_item.items():
                print(f"     {key}: {type(value).__name__}")
                if key == 'original_data':
                    for subkey, subvalue in value.items():
                        print(f"       {subkey}: {subvalue}")
                
            # Проверяем что нет group_id и group_name
            if 'group_id' in work_item:
                print(f"❌ НАЙДЕНО ДЕРЬМО: group_id = {work_item['group_id']}")
                return False
            if 'group_name' in work_item:
                print(f"❌ НАЙДЕНО ДЕРЬМО: group_name = {work_item['group_name']}")
                return False
        
        print("✅ Структура чистая - нет лишних null полей!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        try:
            os.unlink(raw_estimates_file)
            os.unlink(directives_file)
        except:
            pass

if __name__ == "__main__":
    success = test_clean_structure()
    if success:
        print("\n🎉 Структура чистая!")
    else:
        print("\n💩 Есть лишние поля!")
        sys.exit(1)