#!/usr/bin/env python3
"""
Тест агента work_packager.py
Проверяет создание укрупненных пакетов работ
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

from src.ai_agents.work_packager import WorkPackager
from tests.mock_gemini_client import mock_gemini_client

# Подменяем реальный gemini_client на мок для тестирования
import src.ai_agents.work_packager
src.ai_agents.work_packager.gemini_client = mock_gemini_client

class TestWorkPackager:
    
    def __init__(self):
        self.test_project_path = None
    
    def setup_test_project(self):
        """Создает тестовый проект с mock данными"""
        
        # Создаем временную папку для тестирования
        self.test_project_path = tempfile.mkdtemp(prefix='test_herzog_')
        
        # Создаем mock true.json
        mock_truth_data = {
            "metadata": {
                "project_id": "test_project",
                "project_name": "Тестовый проект",
                "pipeline_status": [
                    {"agent_name": "work_packager", "status": "pending"}
                ]
            },
            "project_inputs": {
                "target_work_package_count": 8,
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
                "work_packages": []
            }
        }
        
        truth_path = os.path.join(self.test_project_path, "true.json")
        with open(truth_path, 'w', encoding='utf-8') as f:
            json.dump(mock_truth_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Создан тестовый проект: {self.test_project_path}")
        return self.test_project_path
    
    async def test_work_packager(self):
        """Основной тест работы агента"""
        
        print("🧪 === ТЕСТ WORK_PACKAGER ===")
        
        # Настраиваем тестовый проект
        project_path = self.setup_test_project()
        
        try:
            # Создаем агента
            agent = WorkPackager()
            
            # Запускаем обработку
            print("🔄 Запуск агента work_packager...")
            result = await agent.process(project_path)
            
            # Проверяем результат
            if result.get('success'):
                print("✅ Агент выполнен успешно")
                print(f"📊 Создано пакетов: {result.get('work_packages_created', 0)}")
                
                # Проверяем обновленный true.json
                truth_path = os.path.join(project_path, "true.json")
                with open(truth_path, 'r', encoding='utf-8') as f:
                    updated_truth = json.load(f)
                
                work_packages = updated_truth.get('results', {}).get('work_packages', [])
                
                print(f"📋 Созданные пакеты работ:")
                for i, pkg in enumerate(work_packages, 1):
                    print(f"  {i}. {pkg.get('package_id')}: {pkg.get('name')}")
                    print(f"     {pkg.get('description', '')}")
                
                # Проверяем папку агента
                agent_folder = os.path.join(project_path, "4_work_packager")
                if os.path.exists(agent_folder):
                    files = os.listdir(agent_folder)
                    print(f"📁 Созданы файлы: {files}")
                
                # Базовые валидации
                assert len(work_packages) > 0, "Не создано ни одного пакета работ"
                assert len(work_packages) <= 10, "Создано слишком много пакетов"
                
                for pkg in work_packages:
                    assert 'package_id' in pkg, "Отсутствует package_id"
                    assert 'name' in pkg, "Отсутствует name"
                    assert 'description' in pkg, "Отсутствует description"
                    assert pkg['package_id'].startswith('pkg_'), "Неверный формат package_id"
                
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
    
    async def test_input_extraction(self):
        """Тест извлечения входных данных"""
        
        print("🧪 === ТЕСТ ИЗВЛЕЧЕНИЯ ДАННЫХ ===")
        
        project_path = self.setup_test_project()
        
        try:
            agent = WorkPackager()
            
            # Загружаем true.json
            truth_path = os.path.join(project_path, "true.json")
            with open(truth_path, 'r', encoding='utf-8') as f:
                truth_data = json.load(f)
            
            # Тестируем извлечение данных
            input_data = agent._extract_input_data(truth_data)
            
            print("📊 Извлеченные данные:")
            print(f"  - Работ для обработки: {len(input_data['source_work_items'])}")
            print(f"  - Целевое количество пакетов: {input_data['target_work_package_count']}")
            print(f"  - Директива пользователя: '{input_data['user_directive']}'")
            
            # Валидации
            assert len(input_data['source_work_items']) == 12, "Неверное количество работ"
            assert input_data['target_work_package_count'] == 8, "Неверное целевое количество"
            assert 'электрику' in input_data['user_directive'], "Директива не извлечена"
            
            print("✅ Извлечение данных работает корректно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования извлечения: {e}")
            return False
            
        finally:
            if self.test_project_path and os.path.exists(self.test_project_path):
                shutil.rmtree(self.test_project_path)
    
    async def test_prompt_loading(self):
        """Тест загрузки промпта"""
        
        print("🧪 === ТЕСТ ЗАГРУЗКИ ПРОМПТА ===")
        
        try:
            agent = WorkPackager()
            
            # Тестируем загрузку промпта
            prompt = agent._load_prompt()
            
            print(f"📝 Загружен промпт, длина: {len(prompt)} символов")
            
            # Проверяем наличие ключевых элементов
            assert '{source_work_items}' in prompt, "Отсутствует placeholder для работ"
            assert '{target_work_package_count}' in prompt, "Отсутствует placeholder для количества"
            assert '{user_directive}' in prompt, "Отсутствует placeholder для директивы"
            
            # Тестируем форматирование промпта
            mock_input = {
                'source_work_items': [{'id': '1', 'name': 'Test'}],
                'target_work_package_count': 5,
                'user_directive': 'test directive',
                'total_work_items': 1
            }
            
            formatted = agent._format_prompt(mock_input, prompt)
            
            assert 'test directive' in formatted, "Директива не подставлена"
            assert '5' in formatted, "Количество не подставлено"
            
            print("✅ Промпт загружается и форматируется корректно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования промпта: {e}")
            return False

async def run_all_tests():
    """Запуск всех тестов"""
    
    print("🚀 Запуск тестов work_packager.py")
    print("=" * 50)
    
    tester = TestWorkPackager()
    
    tests = [
        ("Извлечение входных данных", tester.test_input_extraction),
        ("Загрузка и форматирование промпта", tester.test_prompt_loading),
        ("Полный процесс агента", tester.test_work_packager)
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