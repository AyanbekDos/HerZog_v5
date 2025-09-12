#!/usr/bin/env python3
"""
Запуск всех тестов системы HerZog v3.0
Тестирует все четыре агента по отдельности и интеграционно
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

def run_test_file(test_file):
    """Запускает один тестовый файл и возвращает результат"""
    
    print(f"\n{'='*60}")
    print(f"🧪 ЗАПУСК ТЕСТА: {test_file}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Запускаем тест как subprocess
        result = subprocess.run([
            sys.executable, test_file
        ], capture_output=True, text=True, timeout=60)
        
        duration = time.time() - start_time
        
        # Выводим результат
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        
        print(f"\n⏱️ Время выполнения: {duration:.1f}с")
        
        if success:
            print(f"✅ ТЕСТ {test_file} ПРОЙДЕН")
        else:
            print(f"❌ ТЕСТ {test_file} ПРОВАЛЕН (код возврата: {result.returncode})")
        
        return success, duration
        
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print(f"⏰ ТЕСТ {test_file} ПРЕВЫСИЛ ЛИМИТ ВРЕМЕНИ ({duration:.1f}с)")
        return False, duration
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"💥 ОШИБКА ЗАПУСКА ТЕСТА {test_file}: {e}")
        return False, duration

def main():
    """Главная функция запуска всех тестов"""
    
    print("🚀 ЗАПУСК ВСЕХ ТЕСТОВ СИСТЕМЫ HERZOG v3.0")
    print("=" * 60)
    
    tests_dir = Path(__file__).parent
    
    # Список тестов в порядке выполнения
    test_files = [
        "test_work_packager.py",
        "test_works_to_packages.py", 
        "test_counter.py",
        "test_scheduler_and_staffer.py",
        "test_full_pipeline.py"
    ]
    
    results = []
    total_start_time = time.time()
    
    # Запускаем каждый тест
    for test_file in test_files:
        test_path = tests_dir / test_file
        
        if not test_path.exists():
            print(f"⚠️ ТЕСТ НЕ НАЙДЕН: {test_file}")
            results.append((test_file, False, 0))
            continue
        
        success, duration = run_test_file(str(test_path))
        results.append((test_file, success, duration))
    
    total_duration = time.time() - total_start_time
    
    # Выводим сводку результатов
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_file, success, duration in results:
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        print(f"  {test_file:<30} {status} ({duration:.1f}с)")
        
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📈 СТАТИСТИКА:")
    print(f"  ✅ Успешных тестов: {passed}")
    print(f"  ❌ Провалившихся тестов: {failed}")
    print(f"  📊 Всего тестов: {len(results)}")
    print(f"  ⏱️ Общее время: {total_duration:.1f}с")
    
    success_rate = (passed / len(results)) * 100 if results else 0
    print(f"  🎯 Процент успешности: {success_rate:.1f}%")
    
    if passed == len(results):
        print(f"\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print(f"✅ Система HerZog v3.0 готова к использованию")
        sys.exit(0)
    else:
        print(f"\n⚠️ ЕСТЬ ПРОВАЛИВШИЕСЯ ТЕСТЫ!")
        print(f"🔧 Требуется исправление перед использованием")
        sys.exit(1)

if __name__ == "__main__":
    main()