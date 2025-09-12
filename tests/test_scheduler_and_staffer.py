#!/usr/bin/env python3
"""
Тест агента scheduler_and_staffer.py
Проверяет создание календарного плана и распределение персонала
"""

import json
import os
import sys
import asyncio
import tempfile
import shutil
from datetime import datetime, timedelta

# Добавляем путь к модулям
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ai_agents.scheduler_and_staffer import SchedulerAndStaffer
from tests.mock_gemini_client import mock_gemini_client

# Подменяем реальный gemini_client на мок для тестирования
import src.ai_agents.scheduler_and_staffer
src.ai_agents.scheduler_and_staffer.gemini_client = mock_gemini_client

class TestSchedulerAndStaffer:
    
    def __init__(self):
        self.test_project_path = None
    
    def setup_test_project(self):
        """Создает тестовый проект с mock данными"""
        
        # Создаем временную папку для тестирования
        self.test_project_path = tempfile.mkdtemp(prefix='test_herzog_')
        
        # Создаем временные блоки (4 недели)
        start_date = datetime(2024, 1, 1)
        timeline_blocks = []
        
        for week in range(1, 5):
            week_start = start_date + timedelta(weeks=week-1)
            week_end = week_start + timedelta(days=6)
            
            timeline_blocks.append({
                "week_id": week,
                "start_date": week_start.strftime("%Y-%m-%d"),
                "end_date": week_end.strftime("%Y-%m-%d")
            })
        
        # Создаем mock true.json с полными данными
        mock_truth_data = {
            "metadata": {
                "project_id": "test_project",
                "project_name": "Тестовый проект",
                "pipeline_status": [
                    {"agent_name": "work_packager", "status": "completed"},
                    {"agent_name": "works_to_packages", "status": "completed"},
                    {"agent_name": "counter", "status": "completed"},
                    {"agent_name": "scheduler_and_staffer", "status": "pending"}
                ]
            },
            "project_inputs": {
                "target_work_package_count": 4,
                "workforce_range": {
                    "min": 5,
                    "max": 15
                },
                "agent_directives": {
                    "strategist": "растяни демонтаж на первые две недели",
                    "foreman": "на электрику выдели максимум 4 человека"
                }
            },
            "timeline_blocks": timeline_blocks,
            "source_work_items": [
                {
                    "id": "work_001",
                    "name": "Демонтаж перегородок кирпичных",
                    "code": "08.01.001",
                    "package_id": "pkg_001"
                },
                {
                    "id": "work_002",
                    "name": "Прокладка кабеля ВВГ 3х2.5",
                    "code": "19.03.012",
                    "package_id": "pkg_002"
                }
            ],
            "results": {
                "work_packages": [
                    {
                        "package_id": "pkg_001",
                        "name": "Демонтаж конструкций",
                        "description": "Снос перегородок, демонтаж покрытий пола и потолка",
                        "calculations": {
                            "unit": "м²",
                            "quantity": 120.0,
                            "calculation_logic": "Применено правило максимума",
                            "source_works_count": 2
                        }
                    },
                    {
                        "package_id": "pkg_002",
                        "name": "Электромонтажные работы",
                        "description": "Прокладка кабелей, установка розеток и выключателей",
                        "calculations": {
                            "unit": "м",
                            "quantity": 250.0,
                            "calculation_logic": "Сумма всех кабельных линий",
                            "source_works_count": 3
                        }
                    }
                ]
            }
        }
        
        truth_path = os.path.join(self.test_project_path, "true.json")
        with open(truth_path, 'w', encoding='utf-8') as f:
            json.dump(mock_truth_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Создан тестовый проект: {self.test_project_path}")
        return self.test_project_path
    
    async def test_scheduler_full_process(self):
        """Основной тест полного процесса планирования"""
        
        print("🧪 === ТЕСТ SCHEDULER_AND_STAFFER ПОЛНЫЙ ПРОЦЕСС ===")
        
        # Настраиваем тестовый проект
        project_path = self.setup_test_project()
        
        try:
            # Создаем агента
            agent = SchedulerAndStaffer()
            
            # Запускаем обработку
            print("🔄 Запуск агента scheduler_and_staffer...")
            result = await agent.process(project_path)
            
            # Проверяем результат
            if result.get('success'):
                print("✅ Агент выполнен успешно")
                print(f"📊 Запланировано пакетов: {result.get('packages_scheduled', 0)}")
                print(f"👥 Валидация персонала: {result.get('workforce_valid', False)}")
                
                # Проверяем обновленный true.json
                truth_path = os.path.join(project_path, "true.json")
                with open(truth_path, 'r', encoding='utf-8') as f:
                    updated_truth = json.load(f)
                
                work_packages = updated_truth.get('results', {}).get('work_packages', [])
                schedule_info = updated_truth.get('results', {}).get('schedule', {})
                staffing_info = updated_truth.get('results', {}).get('staffing', {})
                
                print(f"📅 Календарный план по пакетам:")
                for pkg in work_packages:
                    schedule_blocks = pkg.get('schedule_blocks', [])
                    progress_per_block = pkg.get('progress_per_block', {})
                    staffing_per_block = pkg.get('staffing_per_block', {})
                    
                    print(f"  {pkg['package_id']}: {pkg['name']}")
                    print(f"    Недели: {schedule_blocks}")
                    print(f"    Прогресс: {progress_per_block}")
                    print(f"    Персонал: {staffing_per_block}")
                
                print(f"📊 Сводная информация:")
                print(f"  Общее количество пакетов: {schedule_info.get('total_packages', 0)}")
                print(f"  Длительность проекта: {schedule_info.get('project_duration_weeks', 0)} недель")
                print(f"  Пиковая нагрузка: {staffing_info.get('peak_workforce', 0)} человек")
                
                # Проверяем папку агента
                agent_folder = os.path.join(project_path, "7_scheduler_and_staffer")
                if os.path.exists(agent_folder):
                    files = os.listdir(agent_folder)
                    print(f"📁 Созданы файлы: {files}")
                
                # Базовые валидации
                assert len(work_packages) == 2, "Неверное количество пакетов в результате"
                
                for pkg in work_packages:
                    # Проверяем наличие календарного плана
                    assert 'schedule_blocks' in pkg, f"Пакет {pkg['package_id']} не имеет календарного плана"
                    assert 'progress_per_block' in pkg, f"Пакет {pkg['package_id']} не имеет прогресса"
                    assert 'staffing_per_block' in pkg, f"Пакет {pkg['package_id']} не имеет назначений персонала"
                    
                    # Проверяем что прогресс в сумме 100%
                    progress = pkg['progress_per_block']
                    total_progress = sum(int(v) for v in progress.values())
                    assert 90 <= total_progress <= 110, f"Прогресс пакета {pkg['package_id']} не равен ~100%: {total_progress}%"
                    
                    # Проверяем что есть персонал на каждую неделю работ
                    staffing = pkg['staffing_per_block']
                    for week in pkg['schedule_blocks']:
                        week_str = str(week)
                        assert week_str in staffing, f"Пакет {pkg['package_id']} не имеет персонала на неделю {week}"
                        assert staffing[week_str] > 0, f"Пакет {pkg['package_id']} имеет 0 персонала на неделю {week}"
                
                # Проверяем сводную статистику
                assert 'schedule' in updated_truth['results'], "Отсутствует сводная информация о календарном плане"
                assert 'staffing' in updated_truth['results'], "Отсутствует сводная информация о персонале"
                
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
    
    async def test_workforce_validation(self):
        """Тест валидации ограничений по персоналу"""
        
        print("🧪 === ТЕСТ ВАЛИДАЦИИ ПЕРСОНАЛА ===")
        
        project_path = self.setup_test_project()
        
        try:
            agent = SchedulerAndStaffer()
            
            # Создаем тестовые данные с нарушением лимитов
            test_packages = [
                {
                    "package_id": "pkg_001",
                    "name": "Пакет 1",
                    "schedule_blocks": [1, 2],
                    "staffing_per_block": {"1": 10, "2": 8}  # Всего в неделю 1: 18 человек (превышение)
                },
                {
                    "package_id": "pkg_002", 
                    "name": "Пакет 2",
                    "schedule_blocks": [1, 3],
                    "staffing_per_block": {"1": 8, "3": 5}
                }
            ]
            
            timeline_blocks = [{"week_id": i} for i in range(1, 5)]
            workforce_range = {"min": 5, "max": 15}
            
            # Тестируем валидацию
            validation = agent._validate_workforce_constraints(test_packages, timeline_blocks, workforce_range)
            
            print(f"📊 Результат валидации:")
            print(f"  Валиден: {validation['valid']}")
            print(f"  Нарушения: {validation['violations']}")
            print(f"  Недельные итоги: {validation['weekly_totals']}")
            
            # Должно быть нарушение на неделе 1 (10+8=18 > 15)
            assert not validation['valid'], "Валидация должна была выявить нарушение"
            assert len(validation['violations']) > 0, "Должно быть хотя бы одно нарушение"
            assert '18' in str(validation['violations']), "Должно быть указано превышение до 18 человек"
            
            print("✅ Валидация персонала работает корректно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования валидации: {e}")
            return False
            
        finally:
            if self.test_project_path and os.path.exists(self.test_project_path):
                shutil.rmtree(self.test_project_path)
    
    async def test_schedule_validation(self):
        """Тест валидации календарного плана"""
        
        print("🧪 === ТЕСТ ВАЛИДАЦИИ КАЛЕНДАРНОГО ПЛАНА ===")
        
        project_path = self.setup_test_project()
        
        try:
            agent = SchedulerAndStaffer()
            
            # Тестируем валидацию и исправление пакета
            test_package = {
                "package_id": "pkg_001",
                "name": "Тестовый пакет",
                "schedule_blocks": [1, 2, 5],  # Неделя 5 не существует (только 4 недели)
                "progress_per_block": {"1": 40, "2": 30, "5": 30},  # Итого 100%
                "staffing_per_block": {"1": 8, "2": 6, "5": 4}
            }
            
            timeline_blocks = [{"week_id": i} for i in range(1, 5)]  # Недели 1-4
            
            # Валидируем пакет
            validated_package = agent._validate_and_fix_package_schedule(test_package, timeline_blocks)
            
            print(f"📊 Результат валидации пакета:")
            print(f"  Исходные недели: {test_package['schedule_blocks']}")
            print(f"  Валидные недели: {validated_package['schedule_blocks']}")
            print(f"  Прогресс: {validated_package['progress_per_block']}")
            print(f"  Персонал: {validated_package['staffing_per_block']}")
            
            # Неделя 5 должна быть удалена
            assert 5 not in validated_package['schedule_blocks'], "Неделя 5 должна быть удалена"
            assert len(validated_package['schedule_blocks']) == 2, "Должно остаться 2 недели"
            
            # Прогресс должен быть пересчитан
            total_progress = sum(validated_package['progress_per_block'].values())
            assert total_progress == 100, f"Общий прогресс должен быть 100%, получено {total_progress}"
            
            # Персонал должен соответствовать оставшимся неделям
            for week in validated_package['schedule_blocks']:
                week_str = str(week)
                assert week_str in validated_package['staffing_per_block'], f"Отсутствует персонал для недели {week}"
            
            print("✅ Валидация календарного плана работает корректно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования валидации плана: {e}")
            return False
            
        finally:
            if self.test_project_path and os.path.exists(self.test_project_path):
                shutil.rmtree(self.test_project_path)
    
    async def test_error_handling(self):
        """Тест обработки ошибок"""
        
        print("🧪 === ТЕСТ ОБРАБОТКИ ОШИБОК ===")
        
        project_path = self.setup_test_project()
        
        try:
            # Удаляем расчеты у пакетов работ
            truth_path = os.path.join(project_path, "true.json")
            with open(truth_path, 'r', encoding='utf-8') as f:
                truth_data = json.load(f)
            
            # Убираем calculations у всех пакетов
            for pkg in truth_data['results']['work_packages']:
                if 'calculations' in pkg:
                    del pkg['calculations']
            
            with open(truth_path, 'w', encoding='utf-8') as f:
                json.dump(truth_data, f, ensure_ascii=False, indent=2)
            
            agent = SchedulerAndStaffer()
            
            print("🔄 Запуск агента без расчетов объемов...")
            result = await agent.process(project_path)
            
            # Ожидаем ошибку
            if not result.get('success'):
                print(f"✅ Ошибка корректно обработана: {result.get('error')}")
                assert "не имеют расчетов объемов" in result.get('error', ''), "Неверное сообщение об ошибке"
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
    
    print("🚀 Запуск тестов scheduler_and_staffer.py")
    print("=" * 50)
    
    tester = TestSchedulerAndStaffer()
    
    tests = [
        ("Валидация персонала", tester.test_workforce_validation),
        ("Валидация календарного плана", tester.test_schedule_validation),
        ("Полный процесс планирования", tester.test_scheduler_full_process),
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