"""
Агент 4: "Супер-Планировщик" (scheduler_and_staffer.py)
Создает комплексный график работ: сроки, прогресс и распределение людей
"""

import json
import os
import asyncio
import logging
import math
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict

# Импорты из нашей системы
from ..shared.claude_client import claude_client as gemini_client  # Migrated to Claude
from ..shared.truth_initializer import update_pipeline_status

logger = logging.getLogger(__name__)

class SchedulerAndStaffer:
    """
    Агент для создания финального календарного плана с распределением персонала
    Обеспечивает соблюдение лимитов по количеству рабочих
    """
    
    def __init__(self, batch_size: int = 12):
        self.agent_name = "scheduler_and_staffer"
        self.batch_size = batch_size

    
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
            # Поддерживаем как новую иерархическую структуру, так и старую плоскую
            work_breakdown_structure = truth_data.get('results', {}).get('work_breakdown_structure', [])
            work_packages = truth_data.get('results', {}).get('work_packages', [])  # Fallback для старых проектов
            volume_calculations = truth_data.get('results', {}).get('volume_calculations', [])
            timeline_blocks = truth_data.get('timeline_blocks', [])
            project_inputs = truth_data.get('project_inputs', {})

            # Если есть новая иерархическая структура, извлекаем пакеты из неё
            if work_breakdown_structure:
                work_packages = [item for item in work_breakdown_structure if item.get('type') == 'package']
                logger.info(f"📊 Используем иерархическую структуру: найдено {len(work_packages)} пакетов работ")

                # Обогащаем пакеты данными расчетов объемов из counter
                volume_by_id = {vol.get('package_id'): vol for vol in volume_calculations}
                for package in work_packages:
                    package_id = package.get('id')
                    if package_id in volume_by_id:
                        package['volume_data'] = volume_by_id[package_id]

            elif work_packages:
                logger.info(f"📊 Используем старую плоскую структуру: найдено {len(work_packages)} пакетов работ")
            else:
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
            # Объединяем старые директивы strategist + foreman в одну
            scheduler_and_staffer_directive = (
                user_directives.get('scheduler_and_staffer') or
                f"{user_directives.get('strategist', '')} {user_directives.get('foreman', '')}".strip()
            )
            
            # Загружаем промпт
            prompt_template = self._load_prompt()
            
            # Подготавливаем компактные данные о пакетах для планирования
            compact_packages = self._prepare_compact_packages(packages_with_calcs, project_path)

            # Обрабатываем ВСЕ пакеты сразу - никаких батчей!
            logger.info(f"📦 Обработка ВСЕХ {len(compact_packages)} пакетов за один раз")

            scheduled_packages = await self._process_all_packages_at_once(
                compact_packages, timeline_blocks, workforce_range,
                scheduler_and_staffer_directive, prompt_template, agent_folder
            )

            logger.info(f"✅ Обработано {len(scheduled_packages)} пакетов за один запрос")
            
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
# РОЛЬ
Ты — эксперт по календарному планированию.

# ЗАДАЧА
Создай реалистичный и оптимизированный календарный план, распределив пакеты работ по неделям и назначив персонал.

# ВХОДНЫЕ ДАННЫЕ
В запросе пользователя ты получишь JSON-объект со следующими ключами:
- "work_packages": пакеты работ с их составом
- "timeline_blocks": доступные недели проекта
- "workforce_range": ограничения по персоналу
- "user_directive": директива пользователя

# КРИТИЧЕСКИЕ ОГРАНИЧЕНИЯ
1. **Лимиты персонала (сумма по всем пакетам в неделю):** В пределах заданного диапазона workforce_range.
2. **Последовательность:** Демонтаж -> Конструкции -> Инженерные сети -> Отделка.

# ФОРМАТ ВЫВОДА (СТРОГО JSON)
{
    "scheduled_packages": [
        {
            "package_id": "pkg_001",
            "schedule_blocks": [1, 2],
            "progress_per_block": { "1": 60, "2": 40 },
            "staffing_per_block": { "1": 10, "2": 8 },
            "scheduling_reasoning": {
                "why_these_weeks": "Кратко.",
                "why_this_duration": "Кратко.",
                "why_this_sequence": "Кратко.",
                "why_this_staffing": "Кратко."
            }
        }
    ]
}

# ПРОВЕРКИ ПЕРЕД ОТВЕТОМ
1. **Лимиты:** Сумма `staffing_per_block` для КАЖДОЙ недели в диапазоне workforce_range.
2. **100%:** Сумма `progress_per_block` для каждого пакета равна 100.
3. **Обоснование:** Поля `scheduling_reasoning` обязательны.
"""
    
    def _add_salt_to_prompt(self, prompt: str) -> str:
        """Добавляет уникальную соль для предотвращения RECITATION."""
        unique_id = str(uuid.uuid4())[:8]
        session_id = str(uuid.uuid4())[:12]
        prefix = f"# TASK_ID: {unique_id} | SESSION: {session_id} | MODE: STRICT_JSON_OUTPUT\n"
        prefix += f"# ANTI_RECITATION_SALT: {session_id}{unique_id}\n"
        suffix = f"\n# END_TASK: {unique_id} | VERIFY: {session_id}"
        return prefix + prompt + suffix

    def _format_prompt(self, input_data: Dict, prompt_template: str) -> Tuple[str, str]:
        """
        Форматирует промпт с разделением на system_instruction и user_prompt

        Returns:
            Tuple[str, str]: (system_instruction, user_prompt)
        """
        # System instruction - статический промпт без плейсхолдеров
        system_instruction = prompt_template

        # User prompt - JSON с данными + дополнительное соление против RECITATION
        anti_recitation_id = str(uuid.uuid4())[:10]
        user_prompt_data = {
            '_meta': {
                'task_type': 'schedule_planning',
                'session_id': anti_recitation_id,
                'timestamp': datetime.now().isoformat()
            },
            'work_packages': input_data['work_packages'],
            'timeline_blocks': input_data['timeline_blocks'],
            'workforce_range': input_data['workforce_range'],
            'user_directive': input_data['user_directive']
        }
        user_prompt = json.dumps(user_prompt_data, ensure_ascii=False, indent=2)

        return system_instruction, user_prompt

    async def _process_batch(self, batch_packages: List[Dict], timeline_blocks: List[Dict],
                           workforce_range: Dict, user_directive: str, prompt_template: str,
                           batch_num: int, agent_folder: str) -> List[Dict]:
        """
        Обрабатывает один батч пакетов для планирования
        """
        # Подготавливаем входные данные для батча
        input_data = {
            'work_packages': batch_packages,
            'timeline_blocks': timeline_blocks,
            'workforce_range': workforce_range,
            'user_directive': user_directive
        }

        # Формируем запрос для LLM
        system_instruction, user_prompt = self._format_prompt(input_data, prompt_template)

        # Добавляем соль к системной инструкции для предотвращения RECITATION
        salted_system_instruction = self._add_salt_to_prompt(system_instruction)

        # Сохраняем РЕАЛЬНЫЕ входные данные для отладки
        debug_data = {
            "batch_packages": batch_packages,    # РЕАЛЬНЫЕ данные пакетов батча
            "timeline_blocks": timeline_blocks,  # РЕАЛЬНЫЕ данные недель
            "workforce_range": workforce_range,
            "user_directive": user_directive,
            "system_instruction": salted_system_instruction,
            "user_prompt": user_prompt,
            "meta": {
                "batch_number": batch_num + 1,
                "packages_count": len(batch_packages),
                "timeline_blocks_count": len(timeline_blocks)
            }
        }
        batch_input_path = os.path.join(agent_folder, f"batch_{batch_num+1:03d}_input.json")
        with open(batch_input_path, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, ensure_ascii=False, indent=2)

        # Вызываем Gemini API с system_instruction и user_prompt
        logger.info(f"📡 Отправка батча {batch_num + 1} в Gemini (scheduler_and_staffer -> gemini-2.5-pro)")
        gemini_response = await gemini_client.generate_response(
            prompt=user_prompt,
            system_instruction=salted_system_instruction,
            agent_name="scheduler_and_staffer"
        )

        # Сохраняем ответ от LLM
        batch_response_path = os.path.join(agent_folder, f"batch_{batch_num+1:03d}_response.json")
        with open(batch_response_path, 'w', encoding='utf-8') as f:
            json.dump(gemini_response, f, ensure_ascii=False, indent=2)


        if not gemini_response.get('success', False):
            logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА Gemini API для батча {batch_num + 1}: {gemini_response.get('error')}")
            raise Exception(f"Gemini API не смог обработать батч {batch_num + 1}. Проверьте промпт и соединение.")

        # Обрабатываем ответ
        scheduled_batch = self._process_scheduling_response(
            gemini_response['response'], batch_packages, timeline_blocks, workforce_range
        )

        return scheduled_batch

    async def _process_all_packages_at_once(self, compact_packages: List[Dict], timeline_blocks: List[Dict],
                                          workforce_range: Dict, scheduler_directive: str, prompt_template: str,
                                          agent_folder: str) -> List[Dict]:
        """
        Обрабатывает ВСЕ пакеты за один запрос - без батчей!
        """
        from ..shared.claude_client import claude_client

        # Формируем единый промт с ВСЕМИ пакетами
        user_prompt = json.dumps({
            "work_packages": compact_packages,
            "timeline_blocks": timeline_blocks,
            "workforce_range": workforce_range,
            "user_directive": scheduler_directive
        }, ensure_ascii=False, indent=2)

        # Солим системную инструкцию
        salted_system_instruction = f"{prompt_template}\n\n# SALT: {uuid.uuid4()}"

        # Сохраняем РЕАЛЬНЫЕ входные данные для отладки
        input_data = {
            "work_packages": compact_packages,  # РЕАЛЬНЫЕ данные пакетов
            "timeline_blocks": timeline_blocks, # РЕАЛЬНЫЕ данные недель
            "workforce_range": workforce_range,
            "user_directive": scheduler_directive,
            "meta": {
                "packages_count": len(compact_packages),
                "timeline_blocks_count": len(timeline_blocks),
                "timestamp": datetime.now().isoformat()
            }
        }

        input_path = os.path.join(agent_folder, "all_packages_input.json")
        with open(input_path, 'w', encoding='utf-8') as f:
            json.dump(input_data, f, ensure_ascii=False, indent=2)

        # Вызываем Claude API с ВСЕМИ пакетами
        logger.info(f"📡 Отправка ВСЕХ пакетов в Claude (scheduler_and_staffer)")
        claude_response = await claude_client.generate_response(
            prompt=user_prompt,
            system_instruction=salted_system_instruction,
            agent_name="scheduler_and_staffer"
        )

        # Сохраняем ответ от Claude
        response_path = os.path.join(agent_folder, "all_packages_response.json")
        with open(response_path, 'w', encoding='utf-8') as f:
            json.dump(claude_response, f, ensure_ascii=False, indent=2)

        if not claude_response.get('success', False):
            logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА Claude API: {claude_response.get('error')}")
            raise Exception(f"Claude API не смог обработать все пакеты. Проверьте промпт и соединение.")

        # Обрабатываем ответ
        scheduled_packages = self._process_scheduling_response(
            claude_response['response'], compact_packages, timeline_blocks, workforce_range
        )

        return scheduled_packages


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
        Поддерживает как иерархическую, так и плоскую структуру
        """
        work_breakdown_structure = truth_data.get('results', {}).get('work_breakdown_structure', [])

        if work_breakdown_structure:
            # Новая иерархическая структура
            logger.info("💾 Обновляем иерархическую структуру с календарными данными")

            # Создаем индекс scheduled_packages по package_id
            schedule_by_id = {}
            for scheduled_pkg in scheduled_packages:
                package_id = scheduled_pkg.get('package_id')
                schedule_by_id[package_id] = scheduled_pkg

            # Обновляем пакеты в work_breakdown_structure
            for item in work_breakdown_structure:
                if item.get('type') == 'package':
                    package_id = item.get('id')
                    if package_id in schedule_by_id:
                        scheduled_data = schedule_by_id[package_id]

                        # Добавляем календарные данные к пакету
                        item.update({
                            'schedule_blocks': scheduled_data.get('schedule_blocks', []),
                            'progress_per_block': scheduled_data.get('progress_per_block', {}),
                            'staffing_per_block': scheduled_data.get('staffing_per_block', {}),
                            'scheduling_reasoning': scheduled_data.get('scheduling_reasoning', {})
                        })

            # Обновляем иерархическую структуру
            truth_data['results']['work_breakdown_structure'] = work_breakdown_structure

            # Также сохраняем в scheduled_packages для совместимости
            truth_data['results']['scheduled_packages'] = scheduled_packages

        else:
            # Старая плоская структура - работаем с work_packages
            logger.info("💾 Обновляем плоскую структуру с календарными данными")

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

                # СОХРАНЯЕМ ИМЯ ПАКЕТА от work_packager, если есть
                if 'name' in existing_pkg:
                    merged_pkg['name'] = existing_pkg['name']

                # СОХРАНЯЕМ ОПИСАНИЕ ПАКЕТА от work_packager, если есть
                if 'description' in existing_pkg:
                    merged_pkg['description'] = existing_pkg['description']

                merged_packages.append(merged_pkg)

            # Обновляем work_packages для старой структуры
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
        Готовит информативные данные о пакетах для планировщика.
        ИСПРАВЛЕНО: Теперь извлекает полную информацию из volume_data, включая component_analysis
        """
        compact_packages = []

        for package in packages_with_calcs:
            package_id = package.get('package_id', 'unknown')
            package_name = package.get('name', package.get('package_name', f'Пакет {package_id}'))

            # Читаем данные из volume_data в true.json
            volume_data = package.get('volume_data', {})

            if not volume_data:
                logger.warning(f"⚠️ Пакет {package_id} не имеет volume_data, пропускаем")
                continue

            # Извлекаем основные данные объема
            final_quantity = volume_data.get('quantity', 0)
            final_unit = volume_data.get('unit', 'шт')

            # Извлекаем component_analysis для детальной информации о составе
            component_analysis = volume_data.get('component_analysis', [])
            source_works_count = len(component_analysis)

            # Определяем сложность работ
            calculation_logic = volume_data.get('calculation_logic', '')
            complexity = self._determine_package_complexity(package_name, calculation_logic)

            # Создаем расширенную структуру согласно требованиям
            compact_package = {
                'package_id': package_id,
                'package_name': package_name,
                'total_volume': {
                    'quantity': final_quantity,
                    'unit': final_unit
                },
                'source_works_count': source_works_count,
                'component_analysis': component_analysis,
                'complexity': complexity
            }

            compact_packages.append(compact_package)
            logger.info(f"📦 Подготовлен пакет: {package_name} ({final_quantity} {final_unit}, {source_works_count} работ, сложность: {complexity})")

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
async def run_scheduler_and_staffer(project_path: str, batch_size: int = 12) -> Dict[str, Any]:
    """
    Запускает агента scheduler_and_staffer для указанного проекта

    Args:
        project_path: Путь к папке проекта
        batch_size: Размер батча для обработки (по умолчанию 12)

    Returns:
        Результат работы агента
    """
    agent = SchedulerAndStaffer(batch_size=batch_size)
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
