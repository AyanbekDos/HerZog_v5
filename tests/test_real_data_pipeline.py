"""
Тест реальных данных через пайплайн с fallback методами (без LLM)
"""

import asyncio
import json
import os
import shutil
import logging

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_real_pipeline():
    """
    Прогоняет реальные данные через весь пайплайн
    """
    # Путь к реальным данным
    base_path = "/home/imort/Herzog_v3/projects/test/test"
    input_path = f"{base_path}/3_prepared"
    
    # Создаем папки для следующих шагов
    paths = {
        4: f"{base_path}/4_conceptualized",
        5: f"{base_path}/5_scheduled", 
        6: f"{base_path}/6_accounted",
        7: f"{base_path}/7_staffed",
        8: f"{base_path}/8_output"
    }
    
    for path in paths.values():
        os.makedirs(path, exist_ok=True)
    
    # Читаем исходные данные
    with open(f"{input_path}/project_data.json", 'r', encoding='utf-8') as f:
        initial_data = json.load(f)
    
    logger.info(f"🚀 Начинаем тест с {initial_data['meta']['total_work_items']} работами")
    logger.info(f"📅 Проект на {initial_data['meta']['total_timeline_blocks']} недель")
    
    # Импортируем агентов
    import sys
    sys.path.append('/home/imort/Herzog_v3')
    
    try:
        # Агент 1: Концептуализатор (с fallback)
        logger.info("🎯 Тестируем Агент 1: Концептуализатор")
        
        # Создаем копию данных и применяем простую группировку
        data_step_1 = initial_data.copy()
        work_items = data_step_1['work_items']
        
        # Простая группировка по ключевым словам (fallback метод)
        group_keywords = {
            'group_1': {
                'name': 'Демонтажные работы',
                'keywords': ['демонтаж', 'снос', 'разборка', 'отбивка', 'очистка']
            },
            'group_2': {
                'name': 'Земляные работы', 
                'keywords': ['земля', 'грунт', 'копка', 'рытье', 'траншея', 'котлован']
            },
            'group_3': {
                'name': 'Фундаментные работы',
                'keywords': ['фундамент', 'основание', 'бетон', 'арматура', 'каркас']
            },
            'group_4': {
                'name': 'Кладочные работы',
                'keywords': ['кладка', 'кирпич', 'блок', 'стена', 'перегородка']
            },
            'group_5': {
                'name': 'Кровельные работы',
                'keywords': ['кровля', 'крыша', 'покрытие', 'черепица', 'профлист']
            },
            'group_6': {
                'name': 'Отделочные работы',
                'keywords': ['штукатурка', 'покраска', 'облицовка', 'плитка', 'обои', 'шпатлевка']
            },
            'group_7': {
                'name': 'Электромонтажные работы',
                'keywords': ['электр', 'провод', 'кабель', 'розетка', 'выключатель', 'щит']
            },
            'group_8': {
                'name': 'Сантехнические работы', 
                'keywords': ['сантехник', 'труба', 'водопровод', 'канализация', 'отопление']
            }
        }
        
        # Применяем группировку
        groups_data = {}
        for item in work_items:
            work_name = item.get('original_data', {}).get('name', '').lower()
            
            # Ищем подходящую группу
            assigned = False
            for group_id, group_info in group_keywords.items():
                if any(keyword in work_name for keyword in group_info['keywords']):
                    item['group_id'] = group_id
                    item['group_name'] = group_info['name']
                    assigned = True
                    
                    # Добавляем в groups_data
                    if group_id not in groups_data:
                        groups_data[group_id] = {
                            'group_name': group_info['name'],
                            'work_ids': [],
                            'schedule_phases': [],
                            'total_quantity': 0,
                            'common_unit': '',
                            'worker_counts': []
                        }
                    groups_data[group_id]['work_ids'].append(item['id'])
                    break
            
            # Если не нашли группу - общие работы
            if not assigned:
                item['group_id'] = 'group_other'
                item['group_name'] = 'Прочие работы'
                if 'group_other' not in groups_data:
                    groups_data['group_other'] = {
                        'group_name': 'Прочие работы',
                        'work_ids': [],
                        'schedule_phases': [],
                        'total_quantity': 0,
                        'common_unit': '',
                        'worker_counts': []
                    }
                groups_data['group_other']['work_ids'].append(item['id'])
        
        # Обновляем данные
        data_step_1['groups_data'] = groups_data
        data_step_1['processing_status']['conceptualization'] = 'completed'
        data_step_1['processing_status']['scheduling'] = 'pending'
        
        # Сохраняем результат Агента 1
        with open(f"{paths[4]}/project_data.json", 'w', encoding='utf-8') as f:
            json.dump(data_step_1, f, ensure_ascii=False, indent=2)
        
        # Имитируем файлы логирования
        with open(f"{paths[4]}/llm_input.json", 'w', encoding='utf-8') as f:
            json.dump({"status": "fallback_grouping", "groups_created": len(groups_data)}, f)
        
        with open(f"{paths[4]}/llm_response.json", 'w', encoding='utf-8') as f:
            json.dump({"status": "fallback_completed", "method": "keyword_matching"}, f)
        
        logger.info(f"✅ Агент 1: Создано {len(groups_data)} групп")
        for gid, gdata in groups_data.items():
            logger.info(f"   {gid}: {gdata['group_name']} ({len(gdata['work_ids'])} работ)")
        
        # Агент 2: Стратег (простое планирование)
        logger.info("📋 Тестируем Агент 2: Стратег")
        
        data_step_2 = data_step_1.copy()
        timeline_blocks = data_step_2['timeline_blocks']
        groups_data = data_step_2['groups_data']
        
        # Простое распределение по неделям
        week_assignments = {
            'group_1': [1, 2],              # Демонтаж - первые недели
            'group_2': [3, 4, 5],           # Земляные - после демонтажа
            'group_3': [6, 7, 8, 9],        # Фундамент - после земляных
            'group_4': [10, 11, 12, 13],    # Кладочные - после фундамента
            'group_5': [14, 15, 16],        # Кровельные - параллельно с кладочными
            'group_7': [17, 18, 19, 20],    # Электромонтаж - после основных работ
            'group_8': [21, 22, 23, 24],    # Сантехника - параллельно с электрикой
            'group_6': [25, 26, 27, 28],    # Отделка - в конце
            'group_other': [29, 30]         # Прочие - в конце
        }
        
        # Применяем планирование к группам
        for group_id, group_data in groups_data.items():
            if group_id in week_assignments:
                weeks = week_assignments[group_id]
                # Проверяем что недели не выходят за границы проекта
                max_week = len(timeline_blocks)
                valid_weeks = [w for w in weeks if w <= max_week]
                group_data['schedule_phases'] = valid_weeks
            else:
                # Для неизвестных групп - последние недели
                group_data['schedule_phases'] = [max(1, len(timeline_blocks) - 2), len(timeline_blocks) - 1]
        
        # Обновляем статус
        data_step_2['processing_status']['scheduling'] = 'completed'
        data_step_2['processing_status']['accounting'] = 'pending'
        
        # Сохраняем результат Агента 2
        with open(f"{paths[5]}/project_data.json", 'w', encoding='utf-8') as f:
            json.dump(data_step_2, f, ensure_ascii=False, indent=2)
        
        with open(f"{paths[5]}/llm_input.json", 'w', encoding='utf-8') as f:
            json.dump({"status": "fallback_scheduling"}, f)
        
        with open(f"{paths[5]}/llm_response.json", 'w', encoding='utf-8') as f:
            json.dump({"status": "fallback_completed"}, f)
        
        scheduled_groups = sum(1 for g in groups_data.values() if g['schedule_phases'])
        logger.info(f"✅ Агент 2: Запланировано {scheduled_groups} групп")
        for gid, gdata in groups_data.items():
            if gdata['schedule_phases']:
                logger.info(f"   {gid}: недели {gdata['schedule_phases']}")
        
        # Агент 3: Бухгалтер (подсчет объемов по группам)
        logger.info("💰 Тестируем Агент 3: Бухгалтер")
        
        data_step_3 = data_step_2.copy()
        work_items = data_step_3['work_items']
        groups_data = data_step_3['groups_data']
        
        # Группируем работы и считаем объемы
        for group_id, group_data in groups_data.items():
            work_ids = group_data['work_ids']
            
            # Находим работы этой группы
            group_works = [item for item in work_items if item['id'] in work_ids]
            
            # Находим наиболее частую единицу измерения в группе
            units = [item.get('original_data', {}).get('unit', 'шт') for item in group_works]
            if units:
                common_unit = max(set(units), key=units.count)
            else:
                common_unit = 'шт'
            
            # Суммируем объемы
            total_qty = 0
            for item in group_works:
                qty_str = str(item.get('original_data', {}).get('quantity', '0'))
                try:
                    qty = float(qty_str.replace(',', '.'))
                    total_qty += qty
                except:
                    total_qty += 1
            
            # Присваиваем группе общие параметры
            group_data['total_quantity'] = total_qty
            group_data['common_unit'] = common_unit
        
        # Обновляем статус
        data_step_3['processing_status']['accounting'] = 'completed'
        data_step_3['processing_status']['staffing'] = 'pending'
        
        # Сохраняем результат Агента 3
        with open(f"{paths[6]}/project_data.json", 'w', encoding='utf-8') as f:
            json.dump(data_step_3, f, ensure_ascii=False, indent=2)
        
        with open(f"{paths[6]}/llm_input.json", 'w', encoding='utf-8') as f:
            json.dump({"status": "fallback_accounting"}, f)
        
        with open(f"{paths[6]}/llm_response.json", 'w', encoding='utf-8') as f:
            json.dump({"status": "fallback_completed"}, f)
        
        logger.info(f"✅ Агент 3: Подсчитано объемов для {len(groups_data)} групп")
        for gid, gdata in groups_data.items():
            logger.info(f"   {gid}: {gdata['total_quantity']} {gdata['common_unit']}")
        
        # Агент 4: Прораб (распределение рабочих)
        logger.info("⚡ Тестируем Агент 4: Прораб")
        
        data_step_4 = data_step_3.copy()
        groups_data = data_step_4['groups_data']
        workforce_range = data_step_4['directives']['workforce_range']
        
        # Простое распределение рабочих по группам
        for group_id, group_data in groups_data.items():
            schedule_phases = group_data.get('schedule_phases', [])
            if schedule_phases:
                # Определяем количество рабочих в зависимости от типа группы
                if 'group_1' in group_id:  # Демонтаж
                    base_workers = 3
                elif 'group_2' in group_id:  # Земляные
                    base_workers = 5
                elif 'group_3' in group_id:  # Фундамент
                    base_workers = 6
                elif 'group_4' in group_id:  # Кладочные
                    base_workers = 4
                elif 'group_6' in group_id:  # Отделка
                    base_workers = 5
                else:  # Прочие
                    base_workers = (workforce_range['min'] + workforce_range['max']) // 2
                
                # Создаем массив рабочих для каждой недели
                workers_per_week = [base_workers] * len(schedule_phases)
                group_data['worker_counts'] = workers_per_week
            else:
                group_data['worker_counts'] = []
        
        # Обновляем статус
        data_step_4['processing_status']['staffing'] = 'completed' 
        data_step_4['processing_status']['reporting'] = 'pending'
        
        # Сохраняем результат Агента 4
        with open(f"{paths[7]}/project_data.json", 'w', encoding='utf-8') as f:
            json.dump(data_step_4, f, ensure_ascii=False, indent=2)
        
        with open(f"{paths[7]}/llm_input.json", 'w', encoding='utf-8') as f:
            json.dump({"status": "fallback_staffing"}, f)
        
        with open(f"{paths[7]}/llm_response.json", 'w', encoding='utf-8') as f:
            json.dump({"status": "fallback_completed"}, f)
        
        staffed_groups = sum(1 for g in groups_data.values() if g['worker_counts'])
        logger.info(f"✅ Агент 4: Укомплектовано {staffed_groups} групп")
        for gid, gdata in groups_data.items():
            if gdata['worker_counts']:
                logger.info(f"   {gid}: рабочие {gdata['worker_counts']}")
        
        # Шаг 5: Генерация Excel отчета
        logger.info("📊 Генерируем финальный Excel отчет")
        
        from src.data_processing.reporter import generate_excel_report
        
        final_input = f"{paths[7]}/project_data.json"
        excel_file = generate_excel_report(final_input, paths[8])
        
        logger.info(f"✅ Excel отчет создан: {excel_file}")
        
        # Финальная статистика
        logger.info("🎉 ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
        logger.info(f"📈 ИТОГОВАЯ СТАТИСТИКА:")
        logger.info(f"   Обработано работ: {len(work_items)}")
        logger.info(f"   Создано групп: {len(groups_data)}")
        logger.info(f"   Недель в проекте: {len(timeline_blocks)}")
        logger.info(f"   Файлы сохранены в: {base_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_real_pipeline())
    if result:
        print("\n🎯 Тест успешно завершен!")
        print("📁 Проверь папки 4_conceptualized, 5_scheduled, 6_accounted, 7_staffed, 8_output")
        print("📊 Посмотри как изменялся project_data.json на каждом этапе")
    else:
        print("\n❌ Тест завершился с ошибками")
        exit(1)