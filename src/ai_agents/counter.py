"""
Агент 3: "Сметчик" (counter.py)
Интеллектуально рассчитывает итоговые объемы для каждого укрупненного пакета работ
"""

import json
import os
import asyncio
import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict

# Импорты из нашей системы
from ..shared.gemini_client import gemini_client
from ..shared.truth_initializer import update_pipeline_status

logger = logging.getLogger(__name__)

class WorkVolumeCalculator:
    """
    Агент для интеллектуального расчета объемов по укрупненным пакетам работ
    Применяет логику агрегации: сложение однотипного, максимум для площадей "пирога"
    """
    
    def __init__(self):
        self.agent_name = "counter"

    
    async def process(self, project_path: str) -> Dict[str, Any]:
        """
        Главный метод обработки расчетов объемов
        
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
            agent_folder = os.path.join(project_path, "6_counter")
            os.makedirs(agent_folder, exist_ok=True)
            
            # Извлекаем входные данные
            work_packages = truth_data.get('results', {}).get('work_packages', [])
            source_work_items = truth_data.get('source_work_items', [])
            agent_directives = truth_data.get('project_inputs', {}).get('agent_directives', {})
            user_directive = agent_directives.get('counter') or agent_directives.get('accountant', '')
            
            if not work_packages:
                raise Exception("Не найдены пакеты работ. Сначала должен быть запущен work_packager")
            
            # Проверяем что работы имеют назначения к пакетам
            works_with_packages = [w for w in source_work_items if w.get('package_id')]
            if not works_with_packages:
                raise Exception("Работы не назначены к пакетам. Сначала должен быть запущен works_to_packages")
            
            logger.info(f"📊 Расчет объемов для {len(work_packages)} пакетов")
            logger.info(f"📋 Обработка {len(works_with_packages)} работ с назначениями")
            
            # Загружаем промпт
            prompt_template = self._load_prompt()
            
            # Группируем работы по пакетам
            packages_with_works = self._group_works_by_packages(work_packages, works_with_packages)
            
            # Обрабатываем каждый пакет
            calculated_packages = []
            for package_data in packages_with_works:
                logger.info(f"🔢 Расчет объемов для пакета: {package_data['package']['name']}")
                
                calculated_package = await self._calculate_package_volumes(
                    package_data, user_directive, prompt_template, agent_folder
                )
                calculated_packages.append(calculated_package)
            
            # Обновляем true.json с результатами
            self._update_truth_data(truth_data, calculated_packages, truth_path)
            
            # Обновляем статус на завершено
            update_pipeline_status(truth_path, self.agent_name, "completed")
            
            logger.info(f"✅ Агент {self.agent_name} завершен успешно")
            logger.info(f"📊 Обработано {len(calculated_packages)} пакетов работ")
            
            return {
                'success': True,
                'packages_calculated': len(calculated_packages),
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
    
    def _group_works_by_packages(self, work_packages: List[Dict], 
                                source_work_items: List[Dict]) -> List[Dict]:
        """
        Группирует работы по пакетам для обработки
        """
        packages_with_works = []
        
        for package in work_packages:
            package_id = package.get('package_id')
            
            # Находим все работы этого пакета
            package_works = [
                work for work in source_work_items 
                if work.get('package_id') == package_id
            ]
            
            # Подготавливаем данные для AI
            works_for_ai = []
            for work in package_works:
                works_for_ai.append({
                    'id': work.get('id'),
                    'name': work.get('name', ''),
                    'code': work.get('code', ''),
                    'unit': work.get('unit', ''),
                    'quantity': work.get('quantity', 0.0)
                })
            
            packages_with_works.append({
                'package': package,
                'works': works_for_ai,
                'work_count': len(works_for_ai)
            })
        
        return packages_with_works
    
    async def _calculate_package_volumes(self, package_data: Dict, user_directive: str,
                                       prompt_template: str, agent_folder: str) -> Dict:
        """
        Рассчитывает объемы для одного пакета работ
        """
        package = package_data['package']
        package_id = package.get('package_id')
        
        # Подготавливаем входные данные для AI
        input_data = {
            'package': package,
            'works': package_data['works'],
            'user_directive': user_directive
        }
        
        # Формируем запрос для LLM
        system_instruction, user_prompt = self._format_prompt(input_data, prompt_template)

        # Добавляем соль к системной инструкции для предотвращения RECITATION
        salted_system_instruction = self._add_salt_to_prompt(system_instruction)

        # Сохраняем структурированный промпт для отладки (как в work_packager)
        debug_data = {
            "system_instruction": salted_system_instruction,
            "user_prompt": user_prompt
        }
        input_path = os.path.join(agent_folder, f"{package_id}_input.json")
        with open(input_path, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, ensure_ascii=False, indent=2)

        # Вызываем Gemini API с указанием агента для оптимальной модели
        logger.info(f"📡 Отправка запроса для пакета {package_id} в Gemini (counter -> gemini-2.5-flash-lite)")
        gemini_response = await gemini_client.generate_response(
            prompt=user_prompt,
            system_instruction=salted_system_instruction,
            agent_name="counter"
        )
        
        # Сохраняем ответ от LLM
        response_path = os.path.join(agent_folder, f"{package_id}_response.json")
        with open(response_path, 'w', encoding='utf-8') as f:
            json.dump(gemini_response, f, ensure_ascii=False, indent=2)
        
        if not gemini_response.get('success', False):
            logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА Gemini API для пакета {package_id}: {gemini_response.get('error')}")
            raise Exception(f"Не удалось получить ответ от Gemini для пакета {package_id}: {gemini_response.get('error')}")
        
        # Обрабатываем ответ
        calculation_result = self._process_calculation_response(
            gemini_response['response'], package, package_data['works']
        )
        
        return calculation_result
    
    def _load_prompt(self) -> str:
        """
        Загружает промпт-шаблон для агента
        """
        prompt_path = os.path.join(
            os.path.dirname(__file__), "..", "prompts", "counter_prompt.txt"
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
Ты - эксперт-сметчик в строительстве. Твоя задача - интеллектуально рассчитать итоговые объемы для пакета работ.

ПАКЕТ РАБОТ:
{package}

ВХОДЯЩИЕ РАБОТЫ:
{works}

ДИРЕКТИВА ПОЛЬЗОВАТЕЛЯ: {user_directive}

ПРАВИЛА РАСЧЕТА ОБЪЕМОВ:
1. СЛОЖЕНИЕ: Одинаковые единицы измерения (м², м³, шт) - складываем количества
2. МАКСИМУМ: Для "слоеных" конструкций (пол, потолок, стены) - берем максимальную площадь
3. ЛОГИКА: Анализируй смысл работ - что реально нужно для выполнения пакета
4. ОКРУГЛЕНИЕ: Итоговые объемы округляй до разумных значений

ПРИМЕРЫ:
- Демонтаж пола (3 вида) → макс. площадь пола
- Устройство пола (стяжка + покрытие) → площадь пола (одинаковая)  
- Монтаж труб → сумма длин всех труб
- Окраска стен (грунт + краска) → площадь стен (одинаковая)

ОБЯЗАТЕЛЬНО УЧИТЫВАЙ ДИРЕКТИВУ: {user_directive}

ФОРМАТ ОТВЕТА (строго JSON):
{{
    "calculation": {{
        "unit": "м²",
        "quantity": 150.0,
        "calculation_logic": "Взята максимальная площадь пола из всех работ демонтажа",
        "component_analysis": [
            {{"work_name": "Демонтаж линолеума", "unit": "м²", "quantity": 120.0}},
            {{"work_name": "Демонтаж стяжки", "unit": "м²", "quantity": 150.0}}
        ]
    }}
}}

ВАЖНО: 
- unit и quantity - это то, что потребуется заказчику для выполнения всего пакета
- calculation_logic - объясни свою логику расчета
- Если работы разнородные, выбери наиболее значимую единицу измерения
"""
    
    def _add_salt_to_prompt(self, prompt: str) -> str:
        """Добавляет уникальную соль для предотвращения RECITATION."""
        unique_id = str(uuid.uuid4())[:8]
        prefix = f"# ID: {unique_id} | Режим: JSON_STRICT\n"
        suffix = f"\n# Контроль: {unique_id}"
        return prefix + prompt + suffix

    def _format_prompt(self, input_data: Dict, prompt_template: str) -> Tuple[str, str]:
        """
        Форматирует промпт с разделением на system_instruction и user_prompt

        Returns:
            Tuple[str, str]: (system_instruction, user_prompt)
        """
        # System instruction - статический промпт без плейсхолдеров
        system_instruction = prompt_template

        # User prompt - JSON с данными
        user_prompt_data = {
            'package': input_data['package'],
            'works': input_data['works'],
            'user_directive': input_data['user_directive']
        }
        user_prompt = json.dumps(user_prompt_data, ensure_ascii=False, indent=2)

        return system_instruction, user_prompt

    def _clean_and_parse_json(self, response_text: str) -> Dict:
        """
        Очищает ответ от markdown и парсит JSON
        """
        try:
            # Убираем markdown блок ```json ... ```
            import re

            # Ищем JSON блок в markdown
            json_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
            match = re.search(json_pattern, response_text, re.DOTALL | re.IGNORECASE)

            if match:
                json_content = match.group(1).strip()
            else:
                # Если нет markdown блока, используем всю строку
                json_content = response_text.strip()

            # Парсим JSON
            return json.loads(json_content)

        except json.JSONDecodeError as e:
            logger.error(f"❌ Не удалось распарсить JSON: {e}")
            logger.error(f"Исходный текст: {response_text[:200]}...")
            raise
        except Exception as e:
            logger.error(f"❌ Ошибка обработки ответа: {e}")
            raise
    
    def _process_calculation_response(self, llm_response: Any, package: Dict,
                                    works: List[Dict]) -> Dict:
        """
        Обрабатывает ответ от LLM с расчетами
        """
        try:
            # Обрабатываем ответ с учетом того, что может прийти строка с markdown
            if isinstance(llm_response, str):
                # Сырая строка, возможно с markdown блоком ```json
                response_data = self._clean_and_parse_json(llm_response)
            elif isinstance(llm_response, dict):
                # Уже распарсенный объект
                response_data = llm_response
            else:
                raise ValueError(f"Неожиданный тип ответа: {type(llm_response)}")

            calculation = response_data.get('calculation', {})
            
            # Валидация и извлечение результата
            final_unit = calculation.get('unit', 'шт')
            
            # Безопасное преобразование количества
            raw_quantity = calculation.get('quantity', 0)
            try:
                if isinstance(raw_quantity, str):
                    final_quantity = float(raw_quantity)
                elif isinstance(raw_quantity, (int, float)):
                    final_quantity = float(raw_quantity)
                else:
                    final_quantity = 0.0
            except (ValueError, TypeError):
                logger.warning(f"Не удалось преобразовать quantity к числу: {raw_quantity}, используем 0")
                final_quantity = 0.0
                
            # Поддерживаем старый и новый формат ответа
            calculation_logic = calculation.get('calculation_logic', 'Автоматический расчет')
            applied_rule = calculation.get('applied_rule', 'НЕОПРЕДЕЛЕНО')
            calculation_steps = calculation.get('calculation_steps', [])
            component_analysis = calculation.get('component_analysis', [])
            reasoning = calculation.get('reasoning', {})

            # Если есть новый формат - используем его
            if applied_rule != 'НЕОПРЕДЕЛЕНО' and calculation_steps:
                calculation_logic = f"{applied_rule}: {', '.join(calculation_steps[:2])}"  # Первые 2 шага как логика

            # Создаем результат
            result = package.copy()
            result['calculations'] = {
                'unit': final_unit,
                'quantity': final_quantity,
                'calculation_logic': calculation_logic,
                'applied_rule': applied_rule,
                'calculation_steps': calculation_steps,
                'component_analysis': component_analysis,
                'reasoning': reasoning,
                'source_works_count': len(works),
                'calculated_at': datetime.now().isoformat()
            }
            
            return result
            
        except (json.JSONDecodeError, KeyError, AttributeError, ValueError) as e:
            logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА парсинга ответа расчетов: {e}")
            logger.error(f"Сырой ответ от Gemini: {llm_response}")
            raise Exception(f"Не удалось распарсить ответ расчетов от Gemini: {e}")
    
    def _update_truth_data(self, truth_data: Dict, calculated_packages: List[Dict], truth_path: str):
        """
        Обновляет true.json с результатами расчетов
        Добавляет только необходимые данные для Excel отчета
        """
        # Получаем текущие work_packages
        current_packages = truth_data.get('results', {}).get('work_packages', [])
        
        # Создаем словарь для быстрого поиска по package_id
        calculations_dict = {}
        for calc_package in calculated_packages:
            package_id = calc_package.get('package_id')
            calculations = calc_package.get('calculations', {})
            
            # Извлекаем данные включая обоснования для ПТО
            calculations_dict[package_id] = {
                'unit': calculations.get('unit', 'шт'),
                'quantity': calculations.get('quantity', 0),
                'calculation_logic': calculations.get('calculation_logic', 'Автоматический расчет'),
                'component_analysis': calculations.get('component_analysis', [])
            }
        
        # Обновляем каждый пакет минимальными данными
        for package in current_packages:
            package_id = package.get('package_id')
            if package_id in calculations_dict:
                # Добавляем только самое нужное
                package['volume_data'] = calculations_dict[package_id]
        
        # Обновляем work_packages в true.json
        truth_data['results']['work_packages'] = current_packages
        
        # Добавляем минимальную сводную статистику
        units_summary = defaultdict(float)
        for calc_data in calculations_dict.values():
            unit = calc_data['unit']
            quantity = calc_data['quantity']
            
            # Безопасное преобразование количества
            try:
                if isinstance(quantity, str):
                    quantity = float(quantity)
                elif isinstance(quantity, (int, float)):
                    quantity = float(quantity)
                else:
                    quantity = 0.0
            except (ValueError, TypeError):
                logger.warning(f"Не удалось преобразовать количество к числу: {quantity}")
                quantity = 0.0
            
            if unit and quantity:
                units_summary[unit] += quantity
        
        # Добавляем краткую статистику
        truth_data['results']['volume_summary'] = {
            'total_packages': len(calculated_packages),
            'units_breakdown': dict(units_summary),
            'calculated_at': datetime.now().isoformat()
        }
        
        # Сохраняем обновленный файл
        with open(truth_path, 'w', encoding='utf-8') as f:
            json.dump(truth_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Обновлен true.json с данными для {len(calculated_packages)} пакетов")
        
        # Копируем обновленный true.json в папку агента
        agent_folder = os.path.join(os.path.dirname(truth_path), "6_counter")
        agent_truth_copy = os.path.join(agent_folder, "updated_true.json")
        
        with open(agent_truth_copy, 'w', encoding='utf-8') as f:
            json.dump(truth_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📁 Скопирован обновленный true.json в {agent_truth_copy}")

# Функция для запуска агента из внешнего кода
async def run_counter(project_path: str) -> Dict[str, Any]:
    """
    Запускает агента counter для указанного проекта
    
    Args:
        project_path: Путь к папке проекта
        
    Returns:
        Результат работы агента
    """
    agent = WorkVolumeCalculator()
    return await agent.process(project_path)

if __name__ == "__main__":
    import sys
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        test_project_path = sys.argv[1]
    else:
        test_project_path = "/home/imort/Herzog_v3/projects/34975055/d490876a"
    
    if os.path.exists(test_project_path):
        print("🧪 Тестирование counter")
        result = asyncio.run(run_counter(test_project_path))
        print(f"Результат: {result}")
    else:
        print(f"❌ Тестовый проект не найден: {test_project_path}")