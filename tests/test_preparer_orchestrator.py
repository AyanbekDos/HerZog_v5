#!/usr/bin/env python3
"""
Тест для проверки что preparer.py правильно работает как оркестратор
Проверяем вызовы classifier.py и timeline_blocks.py
"""

import json
import tempfile
import os
import sys
sys.path.append('/home/imort/Herzog_v3')

from src.data_processing.preparer import prepare_project_data

def test_preparer_orchestrator():
    """Тест что preparer правильно вызывает другие модули"""
    
    # Создаем тестовые raw_estimates.json (как после extractor)
    test_raw_estimates = [
        {
            'internal_id': 'work-1',
            'source_file': 'test.xlsx',
            'position_num': '1',
            'code': 'ГЭСН46-02-009-02',
            'name': 'Отбивка штукатурки',
            'unit': '100 м2',
            'quantity': '7.77'
        },
        {
            'internal_id': 'material-1',
            'source_file': 'test.xlsx',
            'position_num': '2',
            'code': 'ФСБЦ-14.4.01.02-0012',
            'name': 'Смесь сухая штукатурная',
            'unit': 'кг',
            'quantity': '1000'
        },
        {
            'internal_id': 'work-2',
            'source_file': 'test.xlsx', 
            'position_num': '3',
            'code': 'ГЭСН46-01-001-01',
            'name': 'Демонтаж перегородок',
            'unit': '100 м2',
            'quantity': '5.5'
        }
    ]
    
    test_directives = {
        'target_work_count': 10,
        'project_timeline': {
            'start_date': '01.02.2024',
            'end_date': '29.02.2024'  # Один месяц = 4 недели
        },
        'workforce_range': {'min': 5, 'max': 15},
        'directives': {
            'conceptualizer': 'Группировать логично',
            'strategist': 'Планировать последовательно'
        }
    }
    
    # Создаем временные файлы
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f1:
        json.dump(test_raw_estimates, f1, ensure_ascii=False, indent=2)
        raw_estimates_file = f1.name
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f2:
        json.dump(test_directives, f2, ensure_ascii=False, indent=2)
        directives_file = f2.name
    
    try:
        print("🎭 Тестирую preparer как оркестратор...")
        print(f"📄 Raw estimates: {len(test_raw_estimates)} позиций")
        print(f"📅 Диапазон: 01.02.2024 - 29.02.2024")
        
        # Вызываем оркестратор
        result = prepare_project_data(raw_estimates_file, directives_file)
        
        # Проверяем структуру результата
        print(f"\n📊 Результат оркестрации:")
        print(f"   Work items: {len(result.get('work_items', []))}")
        print(f"   Timeline blocks: {len(result.get('timeline_blocks', []))}")
        print(f"   Meta total_work_items: {result.get('meta', {}).get('total_work_items', 0)}")
        
        # Проверяем что classifier сработал правильно
        work_items = result.get('work_items', [])
        for i, item in enumerate(work_items):
            original = item.get('original_data', {})
            classification = original.get('classification')
            name = original.get('name', 'Без названия')
            print(f"   {i+1}. {name} - {classification}")
            
            if classification != 'Работа':
                print(f"❌ ОШИБКА: classifier не отработал - позиция не работа!")
                return False
        
        # Проверяем что timeline_blocks сработал правильно
        timeline_blocks = result.get('timeline_blocks', [])
        if len(timeline_blocks) != 4:  # Февраль 2024 = 4 недели
            print(f"❌ ОШИБКА: timeline_blocks вернул {len(timeline_blocks)} недель, ожидали 4")
            return False
        
        # Проверяем структуру project_data
        required_keys = ['meta', 'directives', 'timeline_blocks', 'work_items', 'processing_status', 'groups_data']
        for key in required_keys:
            if key not in result:
                print(f"❌ ОШИБКА: отсутствует ключ {key} в project_data")
                return False
        
        # Проверяем что работ именно 2 (отфильтрованы материалы)
        expected_works = 2
        actual_works = len(work_items)
        
        if actual_works == expected_works:
            print(f"✅ Оркестратор работает правильно!")
            print(f"   - Вызвал classifier.py ✓")
            print(f"   - Отфильтровал только работы ({actual_works} из {len(test_raw_estimates)}) ✓")
            print(f"   - Вызвал timeline_blocks.py ({len(timeline_blocks)} недель) ✓")
            print(f"   - Собрал project_data.json с правильной структурой ✓")
            return True
        else:
            print(f"❌ Ошибка в количестве работ: ожидали {expected_works}, получили {actual_works}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании оркестратора: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Чистим временные файлы
        try:
            os.unlink(raw_estimates_file)
            os.unlink(directives_file)
        except:
            pass

if __name__ == "__main__":
    success = test_preparer_orchestrator()
    if success:
        print("\n🎉 PREPARER-ОРКЕСТРАТОР работает правильно!")
    else:
        print("\n💥 Есть проблемы с оркестратором!")
        sys.exit(1)