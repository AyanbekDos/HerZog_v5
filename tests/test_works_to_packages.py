#!/usr/bin/env python3
"""
Тест агента works_to_packages.py
Проверяет распределение работ по пакетам с поддержкой батчинга
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

from src.ai_agents.works_to_packages import WorksToPackagesAssigner
from tests.mock_gemini_client import mock_gemini_client

# Подменяем реальный gemini_client на мок для тестирования
import src.ai_agents.works_to_packages
src.ai_agents.works_to_packages.gemini_client = mock_gemini_client

class TestWorksToPackages:
    
    def __init__(self):
        self.test_project_path = None
    
    def setup_test_project(self):
        """Создает тестовый проект с mock данными"""
        
        # Создаем временную папку для тестирования
        self.test_project_path = tempfile.mkdtemp(prefix='test_herzog_')
        
        # Создаем mock true.json с пакетами работ и детализированными работами
        mock_truth_data = {
            "metadata": {
                "project_id": "test_project",
                "project_name": "Тестовый проект",
                "pipeline_status": [
                    {"agent_name": "work_packager", "status": "completed"},
                    {"agent_name": "works_to_packages", "status": "pending"}
                ]
            },
            "project_inputs": {
                "target_work_package_count": 6,
                "agent_directives": {
                    "conceptualizer": "всю электрику объедини в один пакет"
                }
            },
            "source_work_items": [
                {
                    "id": "work_001",
                    "name": "Демонтаж перегородок кирпичных",
                    "code": "08.01.001"
                },
                {
                    "id": "work_002",
                    "name": "Демонтаж покрытия пола линолеум", 
                    "code": "08.02.015"
                },
                {
                    "id": "work_003",
                    "name": "Прокладка кабеля ВВГ 3х2.5",
                    "code": "19.03.012"
                },
                {
                    "id": "work_004",
                    "name": "Установка розеток скрытых",
                    "code": "19.05.001"
                },
                {
                    "id": "work_005",
                    "name": "Монтаж выключателей",
                    "code": "19.05.003"
                },
                {
                    "id": "work_006",
                    "name": "Штукатурка стен цементным раствором",
                    "code": "15.01.001"
                },
                {
                    "id": "work_007",
                    "name": "Покраска стен водоэмульсионной краской",
                    "code": "15.06.001"
                },
                {
                    "id": "work_008",
                    "name": "Устройство стяжки цементной",
                    "code": "11.01.001"
                },
                {
                    "id": "work_009",
                    "name": "Укладка ламината",
                    "code": "11.04.001"
                },
                {
                    "id": "work_010",
                    "name": "Монтаж подвесного потолка",
                    "code": "15.07.001"
                },
                {
                    "id": "work_011",
                    "name": "Прокладка труб водопровода",
                    "code": "18.01.001"
                },
                {
                    "id": "work_012",
                    "name": "Установка смесителя",
                    "code": "18.03.001"
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
                    },
                    {
                        "package_id": "pkg_005",
                        "name": "Работы по потолкам",
                        "description": "Монтаж подвесных и натяжных потолков"
                    },
                    {
                        "package_id": "pkg_006",
                        "name": "Сантехнические работы",
                        "description": "Прокладка труб и установка сантехники"
                    }
                ]
            }
        }
        
        truth_path = os.path.join(self.test_project_path, "true.json")
        with open(truth_path, 'w', encoding='utf-8') as f:
            json.dump(mock_truth_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Создан тестовый проект: {self.test_project_path}")
        return self.test_project_path
    
    async def test_works_to_packages_full(self):
        """Основной тест полного процесса распределения работ"""
        
        print("🧪 === ТЕСТ WORKS_TO_PACKAGES ПОЛНЫЙ ПРОЦЕСС ===")
        
        # Настраиваем тестовый проект
        project_path = self.setup_test_project()
        
        try:
            # Создаем агента
            agent = WorksToPackagesAssigner(batch_size=5)  # Маленький батч для тестирования
            
            # Запускаем обработку
            print("🔄 Запуск агента works_to_packages...")
            result = await agent.process(project_path)
            
            # Проверяем результат
            if result.get('success'):
                print("✅ Агент выполнен успешно")
                print(f"📊 Обработано работ: {result.get('works_processed', 0)}")
                print(f"📦 Обработано батчей: {result.get('batches_processed', 0)}")
                
                # Проверяем обновленный true.json
                truth_path = os.path.join(project_path, "true.json")
                with open(truth_path, 'r', encoding='utf-8') as f:
                    updated_truth = json.load(f)
                
                source_work_items = updated_truth.get('source_work_items', [])
                
                print(f"📋 Распределение работ по пакетам:")
                package_counts = {}
                
                for work in source_work_items:
                    package_id = work.get('package_id', 'НЕ_НАЗНАЧЕН')
                    work_name = work.get('name', 'Без названия')
                    print(f"  {work['id']}: {work_name[:40]}... → {package_id}")
                    
                    if package_id not in package_counts:
                        package_counts[package_id] = 0
                    package_counts[package_id] += 1
                
                print(f"📊 Статистика по пакетам:")
                for pkg_id, count in package_counts.items():
                    print(f"  {pkg_id}: {count} работ")
                
                # Проверяем папку агента
                agent_folder = os.path.join(project_path, "5_works_to_packages")
                if os.path.exists(agent_folder):
                    files = os.listdir(agent_folder)
                    batch_files = [f for f in files if f.startswith('batch_')]
                    print(f"📁 Созданы файлы батчей: {len(batch_files)} файлов")
                
                # Базовые валидации
                assert len(source_work_items) == 12, "Неверное количество работ в результате"
                
                works_with_packages = [w for w in source_work_items if w.get('package_id')]
                assert len(works_with_packages) == 12, "Не все работы назначены к пакетам"
                
                # Проверяем что все package_id существуют
                valid_packages = {'pkg_001', 'pkg_002', 'pkg_003', 'pkg_004', 'pkg_005', 'pkg_006'}
                for work in source_work_items:
                    assert work.get('package_id') in valid_packages, f"Неверный package_id: {work.get('package_id')}"
                
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
    
    async def test_batch_processing(self):
        """Тест батчинга больших объемов работ"""
        
        print("🧪 === ТЕСТ БАТЧИНГА ===")
        
        project_path = self.setup_test_project()
        
        try:
            # Добавляем больше работ для тестирования батчинга
            truth_path = os.path.join(project_path, "true.json")
            with open(truth_path, 'r', encoding='utf-8') as f:
                truth_data = json.load(f)
            
            # Добавляем еще работ (всего будет 22)
            extra_works = []
            for i in range(13, 23):
                extra_works.append({
                    "id": f"work_{i:03d}",
                    "name": f"Дополнительная работа {i}",
                    "code": f"99.99.{i:03d}"
                })
            
            truth_data['source_work_items'].extend(extra_works)
            
            with open(truth_path, 'w', encoding='utf-8') as f:
                json.dump(truth_data, f, ensure_ascii=False, indent=2)
            
            # Создаем агента с маленьким размером батча
            agent = WorksToPackagesAssigner(batch_size=6)  # Батчи по 6 работ
            
            print("🔄 Запуск агента с батчингом...")
            result = await agent.process(project_path)
            
            if result.get('success'):
                expected_batches = 22 // 6 + (1 if 22 % 6 > 0 else 0)  # 4 батча
                actual_batches = result.get('batches_processed', 0)
                
                print(f"📦 Ожидаемо батчей: {expected_batches}")
                print(f"📦 Фактически батчей: {actual_batches}")
                
                assert actual_batches == expected_batches, "Неверное количество батчей"
                
                # Проверяем что все работы обработаны
                with open(truth_path, 'r', encoding='utf-8') as f:
                    updated_truth = json.load(f)
                
                works_with_packages = [w for w in updated_truth['source_work_items'] if w.get('package_id')]
                assert len(works_with_packages) == 22, "Не все работы обработаны в батчах"
                
                print("✅ Батчинг работает корректно")
                return True
            else:
                print(f"❌ Ошибка агента батчинга: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка тестирования батчинга: {e}")
            return False
            
        finally:
            if self.test_project_path and os.path.exists(self.test_project_path):
                shutil.rmtree(self.test_project_path)
    
    async def test_error_handling(self):
        """Тест обработки ошибок"""
        
        print("🧪 === ТЕСТ ОБРАБОТКИ ОШИБОК ===")
        
        project_path = self.setup_test_project()
        
        try:
            # Удаляем пакеты работ чтобы спровоцировать ошибку
            truth_path = os.path.join(project_path, "true.json")
            with open(truth_path, 'r', encoding='utf-8') as f:
                truth_data = json.load(f)
            
            # Очищаем пакеты работ
            truth_data['results']['work_packages'] = []
            
            with open(truth_path, 'w', encoding='utf-8') as f:
                json.dump(truth_data, f, ensure_ascii=False, indent=2)
            
            agent = WorksToPackagesAssigner()
            
            print("🔄 Запуск агента без пакетов работ...")
            result = await agent.process(project_path)
            
            # Ожидаем ошибку
            if not result.get('success'):
                print(f"✅ Ошибка корректно обработана: {result.get('error')}")
                assert "Не найдены пакеты работ" in result.get('error', ''), "Неверное сообщение об ошибке"
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
    
    print("🚀 Запуск тестов works_to_packages.py")
    print("=" * 50)
    
    tester = TestWorksToPackages()
    
    tests = [
        ("Полный процесс распределения", tester.test_works_to_packages_full),
        ("Батчинг больших объемов", tester.test_batch_processing),
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