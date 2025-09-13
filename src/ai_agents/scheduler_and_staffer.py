"""
Агент 4: "Супер-Планировщик" (scheduler_and_staffer.py)
Создает комплексный график работ: сроки, прогресс и распределение людей
"""

import json
import os
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict

# Импорты из нашей системы
from ..shared.gemini_client import gemini_client
from ..shared.truth_initializer import update_pipeline_status

logger = logging.getLogger(__name__)

class SchedulerAndStaffer:
    """
    Агент для создания финального календарного плана с распределением персонала
    Обеспечивает соблюдение лимитов по количеству рабочих
    """
    
    def __init__(self):
        self.agent_name = "scheduler_and_staffer"
    
    async def process(self, project_path: str) -> Dict[str, Any]:
        """
        Главный метод создания календарного плана и распределения персонала
        
        Args:
            project_path: Путь к папке проекта
            
        Returns:
            Результат обработки
        """
        try:
            logger.info(f"🔄 Запуск агента {self.agent_name}")
            
            # Загружаем true.json
            truth_path = os.path.join(project_path, "true.json")
            if not os.path.exists(truth_path):
                raise FileNotFoundError(f"Файл true.json не найден: {truth_path}")
            
            with open(truth_path, 'r', encoding='utf-8') as f:
                truth_data = json.load(f)
            
            # Обновляем статус агента
            update_pipeline_status(truth_path, self.agent_name, "in_progress")
            
            # Подготавливаем папку для работы агента
            agent_folder = os.path.join(project_path, "7_scheduler_and_staffer")
            os.makedirs(agent_folder, exist_ok=True)
            
            # Извлекаем входные данные
            work_packages = truth_data.get('results', {}).get('work_packages', [])
            timeline_blocks = truth_data.get('timeline_blocks', [])
            project_inputs = truth_data.get('project_inputs', {})
            
            if not work_packages:
                raise Exception("Не найдены пакеты работ с расчетами. Сначала должен быть запущен counter")
            
            # Проверяем что пакеты имеют volume_data
            packages_with_calcs = [p for p in work_packages if 'volume_data' in p]
            if not packages_with_calcs:
                raise Exception("Пакеты работ не имеют volume_data. Сначала должен быть запущен counter")
            
            logger.info(f"📊 Создание календарного плана для {len(packages_with_calcs)} пакетов")
            logger.info(f"📅 Временные блоки: {len(timeline_blocks)} недель")
            
            # Извлекаем параметры планирования
            workforce_range = project_inputs.get('workforce_range', {'min': 10, 'max': 20})
            user_directives = project_inputs.get('agent_directives', {})
            strategist_directive = user_directives.get('strategist', '')
            foreman_directive = user_directives.get('foreman', '')
            
            # Загружаем промпт
            prompt_template = self._load_prompt()
            
            # Подготавливаем компактные данные о пакетах для планирования
            compact_packages = self._prepare_compact_packages(packages_with_calcs, project_path)
            
            # Подготавливаем входные данные для AI
            input_data = {
                'work_packages': compact_packages,
                'timeline_blocks': timeline_blocks,
                'workforce_range': workforce_range,
                'strategist_directive': strategist_directive,
                'foreman_directive': foreman_directive
            }
            
            # Формируем запрос для LLM
            formatted_prompt = self._format_prompt(input_data, prompt_template)
            
            # ИСПРАВЛЕНО: Сохраняем входные данные С ПРОМПТОМ для отладки
            debug_input_data = {
                'input_data': input_data,
                'prompt_template': prompt_template,
                'formatted_prompt': formatted_prompt,
                'generated_at': datetime.now().isoformat(),
                'agent': self.agent_name
            }
            
            with open(os.path.join(agent_folder, "llm_input.json"), 'w', encoding='utf-8') as f:
                json.dump(debug_input_data, f, ensure_ascii=False, indent=2)
            
            # Вызываем Gemini API с указанием агента для оптимальной модели
            logger.info("📡 Отправка запроса в Gemini для календарного планирования (scheduler_and_staffer -> gemini-2.5-pro)")
            gemini_response = await gemini_client.generate_response(formatted_prompt, agent_name="scheduler_and_staffer")
            
            # Сохраняем ответ от LLM
            with open(os.path.join(agent_folder, "llm_response.json"), 'w', encoding='utf-8') as f:
                json.dump(gemini_response, f, ensure_ascii=False, indent=2)
            
            if not gemini_response.get('success', False):
                raise Exception(f"Ошибка Gemini API: {gemini_response.get('error', 'Неизвестная ошибка')}")
            
            # Обрабатываем ответ
            scheduled_packages = self._process_scheduling_response(
                gemini_response['response'], packages_with_calcs, timeline_blocks, workforce_range
            )
            
            # Валидируем ограничения по персоналу
            validation_result = self._validate_workforce_constraints(
                scheduled_packages, timeline_blocks, workforce_range
            )
            
            if not validation_result['valid']:
                logger.warning(f"⚠️ Нарушения ограничений по персоналу: {validation_result['violations']}")
                # Пытаемся автоматически исправить
                scheduled_packages = self._fix_workforce_constraints(
                    scheduled_packages, timeline_blocks, workforce_range
                )
            
            # Обновляем true.json с финальными результатами
            self._update_truth_data(truth_data, scheduled_packages, truth_path)
            
            # Обновляем статус на завершено
            update_pipeline_status(truth_path, self.agent_name, "completed")
            
            logger.info(f"✅ Агент {self.agent_name} завершен успешно")
            logger.info(f"📊 Создан календарный план для {len(scheduled_packages)} пакетов")
            
            return {
                'success': True,
                'packages_scheduled': len(scheduled_packages),
                'workforce_valid': validation_result['valid'],
                'agent': self.agent_name
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка агента {self.agent_name}: {e}")
            # Пытаемся обновить статус на ошибку
            try:
                update_pipeline_status(truth_path, self.agent_name, "error")
            except:
                pass
            
            return {
                'success': False,
                'error': str(e),
                'agent': self.agent_name
            }
    
    def _load_prompt(self) -> str:
        """
        Загружает промпт-шаблон для агента
        """
        prompt_path = os.path.join(
            os.path.dirname(__file__), "..", "prompts", "scheduler_and_staffer_prompt.txt"
        )
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"Промпт не найден: {prompt_path}, используем базовый")
            return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """
        Базовый промпт, если файл не найден
        """
        return """
Ты - супер-планировщик строительного проекта. Твоя задача - создать комплексный календарный план с распределением персонала.

ВХОДНЫЕ ДАННЫЕ:

ПАКЕТЫ РАБОТ С ОБЪЕМАМИ:
{work_packages}

ВРЕМЕННЫЕ БЛОКИ (НЕДЕЛИ):
{timeline_blocks}

ОГРАНИЧЕНИЯ ПО ПЕРСОНАЛУ:
- Минимум: {workforce_min} человек
- Максимум: {workforce_max} человек

ДИРЕКТИВЫ ПОЛЬЗОВАТЕЛЯ:
- По срокам: {strategist_directive}
- По персоналу: {foreman_directive}

ЗАДАЧА:
Для каждого пакета работ определи ТРИ аспекта:

1. ГРАФИК (schedule_blocks): массив ID недель когда выполняется пакет
2. ПРОГРЕСС (progress_per_block): % выполнения по неделям
3. ПЕРСОНАЛ (staffing_per_block): количество людей по неделям

ПРИНЦИПЫ ПЛАНИРОВАНИЯ:
1. ЛОГИКА СТРОИТЕЛЬСТВА: учитывай технологическую последовательность (демонтаж → конструкции → отделка)
2. ОГРАНИЧЕНИЯ ПЕРСОНАЛА: сумма людей по всем работам в неделю НЕ ДОЛЖНА превышать {workforce_max}
3. РЕАЛИСТИЧНОСТЬ: объемы и сроки должны соответствовать строительной практике
4. ДИРЕКТИВЫ: обязательно учитывай пожелания пользователя

ФОРМАТ ОТВЕТА (строго JSON):
{{
    "scheduled_packages": [
        {{
            "package_id": "pkg_001",
            "name": "Демонтаж конструкций",
            "calculations": {{...существующие расчеты...}},
            "schedule_blocks": [1, 2, 3],
            "progress_per_block": {{
                "1": 30,
                "2": 50, 
                "3": 20
            }},
            "staffing_per_block": {{
                "1": 8,
                "2": 12,
                "3": 6
            }}
        }}
    ]
}}

КРИТИЧЕСКИ ВАЖНО:
- Сумма progress_per_block должна быть 100% для каждого пакета
- Сумма людей в каждую неделю НЕ БОЛЕЕ {workforce_max} человек
- Учитывай директивы: "{strategist_directive}" и "{foreman_directive}"
"""
    
    def _format_prompt(self, input_data: Dict, prompt_template: str) -> str:
        """
        Форматирует промпт с подстановкой данных
        """
        return prompt_template.format(
            work_packages=json.dumps(input_data['work_packages'], ensure_ascii=False, indent=2),
            timeline_blocks=json.dumps(input_data['timeline_blocks'], ensure_ascii=False, indent=2),
            workforce_min=input_data['workforce_range']['min'],
            workforce_max=input_data['workforce_range']['max'],
            strategist_directive=input_data['strategist_directive'],
            foreman_directive=input_data['foreman_directive']
        )
    
    def _process_scheduling_response(self, llm_response: Any, original_packages: List[Dict],
                                   timeline_blocks: List[Dict], workforce_range: Dict) -> List[Dict]:
        """
        Обрабатывает ответ от LLM с календарным планом
        """
        try:
            if isinstance(llm_response, str):
                # Пробуем напрямую парсить
                response_data = json.loads(llm_response)
            else:
                response_data = llm_response
            
            scheduled_packages = response_data.get('scheduled_packages', [])
            
            # Валидируем и обогащаем каждый пакет
            validated_packages = []
            for pkg in scheduled_packages:
                validated_pkg = self._validate_and_fix_package_schedule(pkg, timeline_blocks)
                validated_packages.append(validated_pkg)
            
            logger.info(f"✅ Успешно обработано {len(validated_packages)} пакетов из ответа LLM")
            return validated_packages
            
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            logger.error(f"Ошибка парсинга ответа планировщика: {e}")
            
            # Диагностическая информация
            if isinstance(llm_response, str):
                response_length = len(llm_response)
                lines_count = llm_response.count('\n')
                logger.error(f"📏 Длина ответа: {response_length} символов, строк: {lines_count}")
                
                # Показываем последние 200 символов для диагностики
                tail = llm_response[-200:] if len(llm_response) > 200 else llm_response
                logger.error(f"📄 Последние 200 символов ответа: ...{tail}")
                
                # Пробуем починить обрезанный JSON
                fixed_response = self._try_fix_truncated_json(llm_response)
                if fixed_response:
                    try:
                        response_data = json.loads(fixed_response)
                        scheduled_packages = response_data.get('scheduled_packages', [])
                        
                        validated_packages = []
                        for pkg in scheduled_packages:
                            validated_pkg = self._validate_and_fix_package_schedule(pkg, timeline_blocks)
                            validated_packages.append(validated_pkg)
                        
                        logger.info(f"🔧 Успешно починили JSON и обработали {len(validated_packages)} пакетов")
                        return validated_packages
                        
                    except Exception as fix_error:
                        logger.error(f"❌ Не удалось починить JSON: {fix_error}")
            
            logger.warning(f"🔄 Переходим на fallback планирование для {len(original_packages)} пакетов")
            return self._create_fallback_schedule(original_packages, timeline_blocks, workforce_range)
    
    def _try_fix_truncated_json(self, broken_json: str) -> Optional[str]:
        """
        Пытается починить обрезанный JSON ответ от LLM
        """
        try:
            # Основные стратегии починки:
            
            # 1. Убираем незавершенные строки в конце
            lines = broken_json.split('\n')
            
            # Ищем последнюю завершенную строку с фигурной скобкой или квадратной скобкой
            fixed_lines = []
            for i, line in enumerate(lines):
                # Если строка содержит только ключ без значения - останавливаемся
                if '"unit":' in line and line.strip().endswith('"unit":'):
                    logger.info("🔧 Обнаружена незавершенная строка с 'unit:', обрезаем")
                    break
                    
                # Если строка неполная (например, не закрыта кавычка) - останавливаемся  
                if line.strip() and not line.strip().endswith((',', '{', '}', '[', ']', '"')):
                    logger.info(f"🔧 Обнаружена незавершенная строка: '{line.strip()}', обрезаем")
                    break
                    
                fixed_lines.append(line)
            
            # 2. Находим правильное место для закрытия JSON
            fixed_content = '\n'.join(fixed_lines)
            
            # 3. Подсчитываем открытые скобки и закрываем их
            open_braces = fixed_content.count('{') - fixed_content.count('}')
            open_brackets = fixed_content.count('[') - fixed_content.count(']')
            
            # Добавляем недостающие закрывающие скобки
            closing = ''
            for _ in range(open_brackets):
                closing += '\n    ]'
            for _ in range(open_braces):
                closing += '\n  }'
            
            fixed_json = fixed_content + closing
            
            # 4. Проверяем что результат валидный
            json.loads(fixed_json)  # Если не валидный - exception
            
            logger.info("🔧 JSON успешно починен")
            return fixed_json
            
        except Exception as e:
            logger.error(f"🔧 Ошибка при попытке починить JSON: {e}")
            return None
    
    def _validate_and_fix_package_schedule(self, package: Dict, timeline_blocks: List[Dict]) -> Dict:
        """
        Валидирует и исправляет календарный план для пакета
        """
        package_id = package.get('package_id', 'unknown')
        
        # Валидация schedule_blocks
        schedule_blocks = package.get('schedule_blocks', [])
        max_week = len(timeline_blocks)
        # Безопасное преобразование и валидация schedule_blocks
        valid_blocks = []
        for week in schedule_blocks:
            try:
                week_num = int(week) if isinstance(week, str) else week
                if 1 <= week_num <= max_week:
                    valid_blocks.append(week_num)
            except (ValueError, TypeError):
                continue
        schedule_blocks = valid_blocks
        
        if not schedule_blocks:
            schedule_blocks = [1]  # fallback
        
        # Валидация progress_per_block
        progress_per_block = package.get('progress_per_block', {})
        total_progress = 0
        
        # Приводим ключи к строковому виду и пересчитываем прогресс
        normalized_progress = {}
        for week in schedule_blocks:
            week_str = str(week)
            progress = progress_per_block.get(week_str, progress_per_block.get(week, 0))
            normalized_progress[week_str] = max(0, min(100, progress))
            total_progress += normalized_progress[week_str]
        
        # Нормализуем прогресс к 100%
        if total_progress != 100 and total_progress > 0:
            scale_factor = 100.0 / total_progress
            for week_str in normalized_progress:
                normalized_progress[week_str] = round(normalized_progress[week_str] * scale_factor)
        elif total_progress == 0:
            # Равномерное распределение
            progress_per_week = round(100.0 / len(schedule_blocks))
            for week in schedule_blocks:
                normalized_progress[str(week)] = progress_per_week
        
        # Валидация staffing_per_block
        staffing_per_block = package.get('staffing_per_block', {})
        normalized_staffing = {}
        
        for week in schedule_blocks:
            week_str = str(week)
            staff = staffing_per_block.get(week_str, staffing_per_block.get(week, 1))
            normalized_staffing[week_str] = max(1, min(20, staff))  # От 1 до 20 человек
        
        # Извлекаем обоснования планирования
        scheduling_reasoning = package.get('scheduling_reasoning', {})
        if not scheduling_reasoning:
            # Создаем базовые обоснования если их нет
            scheduling_reasoning = {
                'why_these_weeks': f'Пакет запланирован на недели {schedule_blocks} по технологической последовательности',
                'why_this_duration': f'Продолжительность {len(schedule_blocks)} недель соответствует объему работ',
                'why_this_sequence': 'Равномерное распределение прогресса по неделям',
                'why_this_staffing': f'Количество персонала от {min(normalized_staffing.values())} до {max(normalized_staffing.values())} человек оптимально для данного типа работ'
            }
        
        # Обновляем пакет
        package['schedule_blocks'] = schedule_blocks
        package['progress_per_block'] = normalized_progress
        package['staffing_per_block'] = normalized_staffing
        package['scheduling_reasoning'] = scheduling_reasoning
        
        return package
    
    def _validate_workforce_constraints(self, packages: List[Dict], 
                                      timeline_blocks: List[Dict], workforce_range: Dict) -> Dict:
        """
        Проверяет соблюдение ограничений по персоналу
        """
        max_workers = workforce_range['max']
        violations = []
        weekly_totals = {}
        
        # Считаем общее количество людей по неделям
        for week_num in range(1, len(timeline_blocks) + 1):
            week_str = str(week_num)
            total_workers = 0
            
            for package in packages:
                staffing = package.get('staffing_per_block', {})
                if week_str in staffing:
                    total_workers += staffing[week_str]
            
            weekly_totals[week_str] = total_workers
            
            if total_workers > max_workers:
                violations.append(f"Неделя {week_num}: {total_workers} > {max_workers}")
        
        return {
            'valid': len(violations) == 0,
            'violations': violations,
            'weekly_totals': weekly_totals
        }
    
    def _fix_workforce_constraints(self, packages: List[Dict], 
                                 timeline_blocks: List[Dict], workforce_range: Dict) -> List[Dict]:
        """
        Автоматически исправляет нарушения ограничений по персоналу
        """
        max_workers = workforce_range['max']
        
        # Простая логика: пропорционально уменьшаем персонал в перегруженные недели
        for week_num in range(1, len(timeline_blocks) + 1):
            week_str = str(week_num)
            
            # Считаем текущий персонал в эту неделю
            current_workers = 0
            week_packages = []
            
            for package in packages:
                staffing = package.get('staffing_per_block', {})
                if week_str in staffing:
                    current_workers += staffing[week_str]
                    week_packages.append(package)
            
            # Если превышение - пропорционально уменьшаем
            if current_workers > max_workers:
                scale_factor = max_workers / current_workers
                
                for package in week_packages:
                    original_staff = package['staffing_per_block'][week_str]
                    new_staff = max(1, round(original_staff * scale_factor))
                    package['staffing_per_block'][week_str] = new_staff
        
        return packages
    
    def _create_fallback_schedule(self, packages: List[Dict], timeline_blocks: List[Dict],
                                workforce_range: Dict) -> List[Dict]:
        """
        Создает базовый календарный план, если AI не сработал
        """
        fallback_packages = []
        max_workers = workforce_range['max']
        workers_per_package = max(1, max_workers // len(packages))
        
        for i, package in enumerate(packages):
            # Равномерно распределяем пакеты по времени
            weeks_per_package = max(1, len(timeline_blocks) // len(packages))
            start_week = (i * weeks_per_package) + 1
            end_week = min(start_week + weeks_per_package - 1, len(timeline_blocks))
            
            schedule_blocks = list(range(start_week, end_week + 1))
            
            # Равномерный прогресс
            progress_per_week = round(100.0 / len(schedule_blocks))
            progress_per_block = {}
            staffing_per_block = {}
            
            for week in schedule_blocks:
                week_str = str(week)
                progress_per_block[week_str] = progress_per_week
                staffing_per_block[week_str] = workers_per_package
            
            fallback_package = package.copy()
            fallback_package['schedule_blocks'] = schedule_blocks
            fallback_package['progress_per_block'] = progress_per_block
            fallback_package['staffing_per_block'] = staffing_per_block
            
            fallback_packages.append(fallback_package)
        
        return fallback_packages
    
    def _update_truth_data(self, truth_data: Dict, scheduled_packages: List[Dict], truth_path: str):
        """
        Обновляет true.json с финальным календарным планом
        СОХРАНЯЯ volume_data от Counter агента
        """
        # ИСПРАВЛЕНО: Объединяем scheduled_packages с существующими данными (volume_data)
        existing_packages = truth_data.get('results', {}).get('work_packages', [])
        existing_by_id = {pkg.get('package_id'): pkg for pkg in existing_packages}
        
        # Объединяем данные: берем календарный план из scheduled_packages + volume_data из existing
        merged_packages = []
        for scheduled_pkg in scheduled_packages:
            package_id = scheduled_pkg.get('package_id')
            existing_pkg = existing_by_id.get(package_id, {})
            
            # Объединяем: scheduled (календарь) + existing (volume_data)
            merged_pkg = scheduled_pkg.copy()
            
            # Сохраняем volume_data от Counter агента, если есть
            if 'volume_data' in existing_pkg:
                merged_pkg['volume_data'] = existing_pkg['volume_data']
                
            merged_packages.append(merged_pkg)
        
        truth_data['results']['work_packages'] = merged_packages
        
        # Создаем сводную информацию о календарном плане
        schedule_summary = self._create_schedule_summary(scheduled_packages, truth_data.get('timeline_blocks', []))
        
        truth_data['results']['schedule'] = schedule_summary['schedule_info']
        truth_data['results']['staffing'] = schedule_summary['staffing_info']
        
        # Добавляем метаданные завершения пайплайна
        truth_data['metadata']['pipeline_completed'] = True
        truth_data['metadata']['final_updated_at'] = datetime.now().isoformat()
        
        # Сохраняем обновленный файл
        with open(truth_path, 'w', encoding='utf-8') as f:
            json.dump(truth_data, f, ensure_ascii=False, indent=2)
    
    def _create_schedule_summary(self, packages: List[Dict], timeline_blocks: List[Dict]) -> Dict:
        """
        Создает сводную информацию о календарном плане
        """
        weekly_workload = {}
        total_packages = len(packages)
        
        for week_num in range(1, len(timeline_blocks) + 1):
            week_str = str(week_num)
            active_packages = 0
            total_workers = 0
            
            for package in packages:
                if week_str in package.get('staffing_per_block', {}):
                    active_packages += 1
                    total_workers += package['staffing_per_block'][week_str]
            
            weekly_workload[week_str] = {
                'active_packages': active_packages,
                'total_workers': total_workers
            }
        
        return {
            'schedule_info': {
                'total_packages': total_packages,
                'project_duration_weeks': len(timeline_blocks),
                'weekly_workload': weekly_workload,
                'created_at': datetime.now().isoformat()
            },
            'staffing_info': {
                'peak_workforce': max([w['total_workers'] for w in weekly_workload.values()]) if weekly_workload else 0,
                'average_workforce': (sum([w['total_workers'] for w in weekly_workload.values()]) / len(weekly_workload)) if weekly_workload else 0,
                'workforce_utilization': weekly_workload
            }
        }
    
    def _prepare_compact_packages(self, packages_with_calcs: List[Dict], project_path: str) -> List[Dict]:
        """
        Готовит компактные данные о пакетов для планировщика.
        ИСПРАВЛЕНО: Теперь читает данные напрямую из true.json вместо отдельных файлов
        """
        compact_packages = []
        
        for package in packages_with_calcs:
            package_id = package.get('package_id', 'unknown')
            package_name = package.get('name', package.get('package_name', f'Пакет {package_id}'))
            
            # Читаем данные из volume_data в true.json (единственная структура)
            volume_data = package.get('volume_data', {})
            
            if not volume_data:
                logger.warning(f"⚠️ Пакет {package_id} не имеет volume_data, пропускаем")
                continue
                
            final_quantity = volume_data.get('quantity', 0)
            final_unit = volume_data.get('unit', 'шт')
            calculation_logic = volume_data.get('calculation_logic', '')
            
            # Определяем сложность работ на основе названия пакета
            complexity = self._determine_package_complexity(package_name, calculation_logic)
            
            compact_package = {
                'package_id': package_id,
                'package_name': package_name,
                'final_quantity': final_quantity,
                'final_unit': final_unit,
                'complexity': complexity
                # ИСПРАВЛЕНО: Убрали calculation_summary - он не нужен для планирования
            }
            
            compact_packages.append(compact_package)
            logger.info(f"📦 Подготовлен пакет: {package_name} ({final_quantity} {final_unit}, сложность: {complexity})")
        
        return compact_packages
    
    def _determine_package_complexity(self, package_name: str, logic: str) -> str:
        """
        Определяет сложность пакета работ для планирования ресурсов
        """
        name_lower = package_name.lower()
        logic_lower = logic.lower()
        
        # Высокая сложность
        if any(keyword in name_lower for keyword in ['демонтаж', 'разборка', 'снос']):
            return 'high'
        if any(keyword in logic_lower for keyword in ['бетон', 'железобетон', 'конструкци']):
            return 'high'
            
        # Средняя сложность  
        if any(keyword in name_lower for keyword in ['установка', 'монтаж', 'строительство']):
            return 'medium'
        if any(keyword in logic_lower for keyword in ['стен', 'перекры', 'основани']):
            return 'medium'
            
        # Низкая сложность
        if any(keyword in name_lower for keyword in ['отделк', 'покраск', 'штукатурк', 'подготовк']):
            return 'low'
        if any(keyword in logic_lower for keyword in ['поверхност', 'краск', 'штукатур']):
            return 'low'
            
        return 'medium'  # По умолчанию

# Функция для запуска агента из внешнего кода
async def run_scheduler_and_staffer(project_path: str) -> Dict[str, Any]:
    """
    Запускает агента scheduler_and_staffer для указанного проекта
    
    Args:
        project_path: Путь к папке проекта
        
    Returns:
        Результат работы агента
    """
    agent = SchedulerAndStaffer()
    return await agent.process(project_path)

if __name__ == "__main__":
    import sys
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        test_project_path = sys.argv[1]
    else:
        # Тестирование по умолчанию
        test_project_path = "/home/imort/Herzog_v3/projects/34975055/d490876a"
    
    if os.path.exists(test_project_path):
        print("🧪 Тестирование scheduler_and_staffer")
        result = asyncio.run(run_scheduler_and_staffer(test_project_path))
        print(f"Результат: {result}")
    else:
        print(f"❌ Тестовый проект не найден: {test_project_path}")
