#!/usr/bin/env python3
"""
Тест агента counter.py
Проверяет интеллектуальный расчет объемов для пакетов работ
"""

import json
import os
import sys
import asyncio
import tempfile
import shutil
from datetime import datetime

# Добавляем путь к модулям
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ai_agents.counter import WorkVolumeCalculator
from tests.mock_gemini_client import mock_gemini_client

# Подменяем реальный gemini_client на мок для тестирования
import src.ai_agents.counter
src.ai_agents.counter.gemini_client = mock_gemini_client

class TestCounter:
    
    def __init__(self):
        self.test_project_path = None
    
    def setup_test_project(self):
        """Создает тестовый проект с mock данными"""
        
        # Создаем временную папку для тестирования
        self.test_project_path = tempfile.mkdtemp(prefix='test_herzog_')
        
        # Создаем mock true.json с пакетами работ и назначенными работами
        mock_truth_data = {
            "metadata": {
                "project_id": "test_project",
                "project_name": "Тестовый проект",
                "pipeline_status": [
                    {"agent_name": "work_packager", "status": "completed"},
                    {"agent_name": "works_to_packages", "status": "completed"},
                    {"agent_name": "counter", "status": "pending"}
                ]
            },
            "project_inputs": {
                "target_work_package_count": 6,
                "agent_directives": {
                    "accountant": "при объединении полов считай только площадь"
                }
            },
            "source_work_items": [
                {
                    "id": "work_001",
                    "name": "Демонтаж перегородок кирпичных",
                    "code": "08.01.001",
                    "unit": "м²",
                    "quantity": 80.5,
                    "package_id": "pkg_001"
                },
                {
                    "id": "work_002",
                    "name": "Демонтаж покрытия пола линолеум",
                    "code": "08.02.015",
                    "unit": "м²",
                    "quantity": 120.0,
                    "package_id": "pkg_001"
                },
                {
                    "id": "work_003",
                    "name": "Прокладка кабеля ВВГ 3х2.5",
                    "code": "19.03.012",
                    "unit": "м",
                    "quantity": 250.0,
                    "package_id": "pkg_002"
                },
                {
                    "id": "work_004",
                    "name": "Установка розеток скрытых",
                    "code": "19.05.001",
                    "unit": "шт",
                    "quantity": 12.0,
                    "package_id": "pkg_002"
                },
                {
                    "id": "work_005",
                    "name": "Монтаж выключателей",
                    "code": "19.05.003",
                    "unit": "шт",
                    "quantity": 8.0,
                    "package_id": "pkg_002"
                },
                {
                    "id": "work_006",
                    "name": "Штукатурка стен цементным раствором",
                    "code": "15.01.001",
                    "unit": "м²",
                    "quantity": 180.0,
                    "package_id": "pkg_003"
                },
                {
                    "id": "work_007",
                    "name": "Покраска стен водоэмульсионной краской",
                    "code": "15.06.001",
                    "unit": "м²",
                    "quantity": 175.0,
                    "package_id": "pkg_003"
                },
                {
                    "id": "work_008",
                    "name": "Устройство стяжки цементной",
                    "code": "11.01.001",
                    "unit": "м²",
                    "quantity": 95.0,
                    "package_id": "pkg_004"
                },
                {
                    "id": "work_009",
                    "name": "Укладка ламината",
                    "code": "11.04.001",
                    "unit": "м²",
                    "quantity": 90.0,
                    "package_id": "pkg_004"
                }
            ],
            "results": {
                "work_packages": [
                    {
                        "package_id": "pkg_001",
                        "name": "Демонтаж конструкций",
                        "description": "Снос перегородок, демонтаж покрытий пола и потолка"
                    },
                    {
                        "package_id": "pkg_002",
                        "name": "Электромонтажные работы",
                        "description": "Прокладка кабелей, установка розеток и выключателей"
                    },
                    {
                        "package_id": "pkg_003",
                        "name": "Отделочные работы стен",
                        "description": "Штукатурка и покраска стен помещений"
                    },
                    {
                        "package_id": "pkg_004",
                        "name": "Устройство полов",
                        "description": "Стяжка и укладка напольных покрытий"
                    }
                ]
            }
        }
        
        truth_path = os.path.join(self.test_project_path, "true.json")
        with open(truth_path, 'w', encoding='utf-8') as f:
            json.dump(mock_truth_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Создан тестовый проект: {self.test_project_path}")
        return self.test_project_path
    
    async def test_counter_full_process(self):
        """Основной тест полного процесса расчета объемов"""
        
        print("🧪 === ТЕСТ COUNTER ПОЛНЫЙ ПРОЦЕСС ===")
        
        # Настраиваем тестовый проект
        project_path = self.setup_test_project()
        
        try:
            # Создаем агента
            agent = WorkVolumeCalculator()
            
            # Запускаем обработку
            print("🔄 Запуск агента counter...")
            result = await agent.process(project_path)
            
            # Проверяем результат
            if result.get('success'):
                print("✅ Агент выполнен успешно")
                print(f"📊 Обработано пакетов: {result.get('packages_calculated', 0)}")
                
                # Проверяем обновленный true.json
                truth_path = os.path.join(project_path, "true.json")
                with open(truth_path, 'r', encoding='utf-8') as f:
                    updated_truth = json.load(f)
                
                work_packages = updated_truth.get('results', {}).get('work_packages', [])
                
                print(f"📋 Расчеты объемов по пакетам:")
                for pkg in work_packages:
                    calculations = pkg.get('calculations', {})
                    unit = calculations.get('unit', 'н/д')
                    quantity = calculations.get('quantity', 0)
                    logic = calculations.get('calculation_logic', 'н/д')
                    
                    print(f"  {pkg['package_id']}: {pkg['name']}")
                    print(f"    Итоговый объем: {quantity} {unit}")
                    print(f"    Логика: {logic[:60]}...")
                
                # Проверяем папку агента
                agent_folder = os.path.join(project_path, "6_counter")
                if os.path.exists(agent_folder):
                    files = os.listdir(agent_folder)
                    pkg_files = [f for f in files if f.startswith('pkg_')]
                    print(f"📁 Созданы файлы пакетов: {len(pkg_files)} файлов")
                
                # Базовые валидации
                assert len(work_packages) == 4, "Неверное количество пакетов в результате"
                
                for pkg in work_packages:
                    assert 'calculations' in pkg, f"Пакет {pkg['package_id']} не имеет расчетов"
                    calc = pkg['calculations']
                    assert 'unit' in calc, f"Пакет {pkg['package_id']} не имеет единицы измерения"
                    assert 'quantity' in calc, f"Пакет {pkg['package_id']} не имеет количества"
                    assert calc['quantity'] > 0, f"Пакет {pkg['package_id']} имеет нулевое количество"
                
                # Проверяем статистику
                volume_stats = updated_truth.get('results', {}).get('volume_calculations', {})
                assert 'packages_calculated' in volume_stats, "Отсутствует статистика расчетов"
                
                print("✅ Все валидации пройдены")
                return True
                
            else:
                print(f"❌ Ошибка агента: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение в тесте: {e}")
            return False
        
        finally:
            # Очищаем тестовые данные
            if self.test_project_path and os.path.exists(self.test_project_path):
                shutil.rmtree(self.test_project_path)
                print(f"🧹 Удален тестовый проект: {self.test_project_path}")
    
    async def test_data_grouping(self):
        """Тест группировки работ по пакетам"""
        
        print("🧪 === ТЕСТ ГРУППИРОВКИ ДАННЫХ ===")
        
        project_path = self.setup_test_project()
        
        try:
            agent = WorkVolumeCalculator()
            
            # Загружаем true.json
            truth_path = os.path.join(project_path, "true.json")
            with open(truth_path, 'r', encoding='utf-8') as f:
                truth_data = json.load(f)
            
            work_packages = truth_data.get('results', {}).get('work_packages', [])
            source_work_items = truth_data.get('source_work_items', [])
            
            # Тестируем группировку
            packages_with_works = agent._group_works_by_packages(work_packages, source_work_items)
            
            print("📊 Группировка работ по пакетам:")
            for pkg_data in packages_with_works:
                pkg = pkg_data['package']
                works = pkg_data['works']
                print(f"  {pkg['package_id']}: {len(works)} работ")
                for work in works:
                    print(f"    - {work['name'][:40]}... ({work['quantity']} {work['unit']})")
            
            # Валидации
            assert len(packages_with_works) == 4, "Неверное количество групп"
            
            # Проверяем что все работы сгруппированы
            total_works = sum(len(pkg_data['works']) for pkg_data in packages_with_works)
            assert total_works == 9, "Не все работы сгруппированы"
            
            # Проверяем что у каждой работы есть необходимые поля
            for pkg_data in packages_with_works:
                for work in pkg_data['works']:
                    assert 'id' in work, "Работа не имеет id"
                    assert 'unit' in work, "Работа не имеет единицы измерения"
                    assert 'quantity' in work, "Работа не имеет количества"
            
            print("✅ Группировка данных работает корректно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования группировки: {e}")
            return False
            
        finally:
            if self.test_project_path and os.path.exists(self.test_project_path):
                shutil.rmtree(self.test_project_path)
    
    async def test_fallback_calculation(self):
        """Тест fallback расчетов"""
        
        print("🧪 === ТЕСТ FALLBACK РАСЧЕТОВ ===")
        
        project_path = self.setup_test_project()
        
        try:
            agent = WorkVolumeCalculator()
            
            # Тестируем fallback расчет
            test_package = {
                "package_id": "pkg_test",
                "name": "Тестовый пакет"
            }
            
            test_works = [
                {"name": "Работа 1", "unit": "м²", "quantity": 100.0},
                {"name": "Работа 2", "unit": "м²", "quantity": 150.0},
                {"name": "Работа 3", "unit": "шт", "quantity": 5.0}
            ]
            
            result = agent._create_fallback_calculation(test_package, test_works)
            
            print(f"📊 Fallback расчет:")
            calc = result.get('calculations', {})
            print(f"  Единица: {calc.get('unit')}")
            print(f"  Количество: {calc.get('quantity')}")
            print(f"  Логика: {calc.get('calculation_logic')}")
            
            # Валидации
            assert 'calculations' in result, "Результат не содержит расчеты"
            assert calc.get('unit') == 'м²', "Неверная единица измерения в fallback"
            assert calc.get('quantity') == 150.0, "Неверное количество в fallback (должно быть максимум)"
            
            print("✅ Fallback расчеты работают корректно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования fallback: {e}")
            return False
            
        finally:
            if self.test_project_path and os.path.exists(self.test_project_path):
                shutil.rmtree(self.test_project_path)
    
    async def test_error_handling(self):
        """Тест обработки ошибок"""
        
        print("🧪 === ТЕСТ ОБРАБОТКИ ОШИБОК ===")
        
        project_path = self.setup_test_project()
        
        try:
            # Удаляем назначения пакетов у работ
            truth_path = os.path.join(project_path, "true.json")
            with open(truth_path, 'r', encoding='utf-8') as f:
                truth_data = json.load(f)
            
            # Убираем package_id у всех работ
            for work in truth_data['source_work_items']:
                if 'package_id' in work:
                    del work['package_id']
            
            with open(truth_path, 'w', encoding='utf-8') as f:
                json.dump(truth_data, f, ensure_ascii=False, indent=2)
            
            agent = WorkVolumeCalculator()
            
            print("🔄 Запуск агента без назначений к пакетам...")
            result = await agent.process(project_path)
            
            # Ожидаем ошибку
            if not result.get('success'):
                print(f"✅ Ошибка корректно обработана: {result.get('error')}")
                assert "не назначены к пакетам" in result.get('error', ''), "Неверное сообщение об ошибке"
                return True
            else:
                print("❌ Ожидалась ошибка, но агент завершился успешно")
                return False
                
        except Exception as e:
            print(f"❌ Неожиданная ошибка в тесте: {e}")
            return False
            
        finally:
            if self.test_project_path and os.path.exists(self.test_project_path):
                shutil.rmtree(self.test_project_path)

async def run_all_tests():
    """Запуск всех тестов"""
    
    print("🚀 Запуск тестов counter.py")
    print("=" * 50)
    
    tester = TestCounter()
    
    tests = [
        ("Группировка данных по пакетам", tester.test_data_grouping),
        ("Fallback расчеты", tester.test_fallback_calculation),
        ("Полный процесс расчета объемов", tester.test_counter_full_process),
        ("Обработка ошибок", tester.test_error_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Тест: {test_name}")
        print("-" * 30)
        
        try:
            success = await test_func()
            results.append((test_name, success))
            
            if success:
                print(f"✅ {test_name}: ПРОЙДЕН")
            else:
                print(f"❌ {test_name}: ПРОВАЛЕН")
                
        except Exception as e:
            print(f"💥 {test_name}: ОШИБКА - {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
    
    passed = 0
    for test_name, success in results:
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        print(f"  {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Результат: {passed}/{len(results)} тестов пройдено")
    
    if passed == len(results):
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return True
    else:
        print("⚠️ Есть неудачные тесты!")
        return False

if __name__ == "__main__":
    # Запуск тестов
    asyncio.run(run_all_tests())