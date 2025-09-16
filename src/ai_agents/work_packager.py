"""
Агент 1: "Архитектор" (work_packager.py)
Создает укрупненные пакеты работ для строительного проекта
"""

import json
import os
import asyncio
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

# Импорты из нашей системы
from ..shared.claude_client import claude_client as gemini_client  # Migrated to Claude
from ..shared.truth_initializer import update_pipeline_status

logger = logging.getLogger(__name__)

class WorkPackager:
    """
    Агент для создания укрупненных пакетов работ
    Анализирует детализированные работы и создает высокоуровневую структуру проекта
    """
    
    def __init__(self):
        self.agent_name = "work_packager"

    def _add_salt_to_prompt(self, prompt: str) -> str:
        """Добавляет уникальную соль для предотвращения RECITATION."""
        unique_id = str(uuid.uuid4())[:8]
        prefix = f"# ID: {unique_id} | Режим: JSON_STRICT\n"
        suffix = f"\n# Контроль: {unique_id}"
        return prefix + prompt + suffix
    
    async def process(self, project_path: str) -> Dict[str, Any]:
        """
        Главный метод обработки
        
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
            
            # Извлекаем входные данные
            input_data = self._extract_input_data(truth_data)
            
            # Создаем папку агента
            llm_input_path = os.path.join(project_path, "4_work_packager")
            os.makedirs(llm_input_path, exist_ok=True)
            
            # Загружаем промпт
            prompt_template = self._load_prompt()
            
            # Формируем системную инструкцию и пользовательские данные
            system_instruction, user_prompt = self._format_prompt(input_data, prompt_template)

            # Добавляем соль к системной инструкции для предотвращения RECITATION
            salted_system_instruction = self._add_salt_to_prompt(system_instruction)

            # Сохраняем РЕАЛЬНЫЕ входные данные для отладки
            debug_data = {
                "work_items": input_data['source_work_items'],    # РЕАЛЬНЫЕ данные работ
                "user_directive": input_data['user_directive'],
                "target_package_count": input_data['target_work_package_count'],
                "system_instruction": salted_system_instruction,
                "user_prompt": user_prompt,
                "meta": {
                    "works_count": len(input_data['source_work_items']),
                    "target_packages": input_data['target_work_package_count']
                }
            }
            with open(os.path.join(llm_input_path, "llm_input.json"), 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2)

            # Вызываем Gemini API с разделенными промптами
            logger.info("📡 Отправка запроса в Claude (work_packager -> claude-sonnet-4)")
            gemini_response = await gemini_client.generate_response(
                prompt=user_prompt,
                agent_name="work_packager",
                system_instruction=salted_system_instruction
            )

            # Сохраняем ответ от LLM
            with open(os.path.join(llm_input_path, "llm_response.json"), 'w', encoding='utf-8') as f:
                json.dump(gemini_response, f, ensure_ascii=False, indent=2)
            
            if not gemini_response.get('success', False):
                raise Exception(f"Ошибка Claude API: {gemini_response.get('error', 'Неизвестная ошибка')}")
            
            # Обрабатываем ответ
            work_breakdown_structure = self._process_llm_response(gemini_response['response'])

            # Обновляем true.json с новой иерархической структурой
            truth_data['results']['work_breakdown_structure'] = work_breakdown_structure

            # Подсчитываем количество пакетов для совместимости с остальной системой
            packages_count = len([item for item in work_breakdown_structure if item.get('type') == 'package'])
            
            with open(truth_path, 'w', encoding='utf-8') as f:
                json.dump(truth_data, f, ensure_ascii=False, indent=2)
            
            # Обновляем статус на завершено
            update_pipeline_status(truth_path, self.agent_name, "completed")
            
            logger.info(f"✅ Агент {self.agent_name} завершен успешно")
            logger.info(f"📊 Создана иерархическая структура: {packages_count} пакетов работ в {len(work_breakdown_structure) - packages_count} категориях")

            return {
                'success': True,
                'work_packages_created': packages_count,
                'categories_created': len(work_breakdown_structure) - packages_count,
                'total_structure_items': len(work_breakdown_structure),
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
    
    def _extract_input_data(self, truth_data: Dict) -> Dict:
        """
        Извлекает необходимые данные из true.json для агента
        """
        # Получаем все работы (только их id и name)
        source_work_items = truth_data.get('source_work_items', [])
        work_items_for_llm = []
        
        for item in source_work_items:
            work_items_for_llm.append({
                'id': item.get('id'),
                'name': item.get('name', ''),
                'code': item.get('code', '')
            })
        
        # Получаем директиву пользователя (совместимость со старым форматом)
        project_inputs = truth_data.get('project_inputs', {})
        target_count = project_inputs.get('target_work_package_count', 15)
        agent_directives = project_inputs.get('agent_directives', {})
        work_packager_directive = agent_directives.get('work_packager') or agent_directives.get('conceptualizer', '')
        
        return {
            'source_work_items': work_items_for_llm,
            'target_work_package_count': target_count,
            'user_directive': work_packager_directive,
            'total_work_items': len(work_items_for_llm)
        }
    
    def _load_prompt(self) -> str:
        """
        Загружает промпт-шаблон для агента
        """
        prompt_path = os.path.join(
            os.path.dirname(__file__), "..", "prompts", "work_packager_prompt.txt"
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
Ты - архитектор строительного проекта. Твоя задача - проанализировать список детализированных строительных работ и создать укрупненные пакеты работ для управления проектом.

ВХОДНЫЕ ДАННЫЕ:
- Список работ: {source_work_items}
- Целевое количество пакетов: {target_work_package_count}
- Директива пользователя: {user_directive}

ЗАДАЧА:
Создай {target_work_package_count} человекопонятных названий для укрупненных пакетов работ, которые логически объединяют похожие строительные работы.

Каждый пакет должен иметь:
- package_id: уникальный идентификатор (например "pkg_001")  
- name: краткое понятное название (например "Демонтаж перегородок и полов")
- description: краткое описание содержимого пакета

ТРЕБОВАНИЯ:
1. Учитывай строительную логику и последовательность работ
2. Группируй по типам работ (демонтаж, монтаж, отделка и т.д.)
3. Обязательно учитывай директиву пользователя: {user_directive}
4. Названия должны быть понятными для заказчика

ФОРМАТ ОТВЕТА (строго JSON):
{{
    "work_packages": [
        {{
            "package_id": "pkg_001",
            "name": "Демонтаж конструкций", 
            "description": "Снос перегородок, демонтаж покрытий пола и потолка"
        }}
    ]
}}
"""
    
    def _format_prompt(self, input_data: Dict, prompt_template: str) -> tuple[str, str]:
        """
        Форматирует промпт, разделяя системную инструкцию и пользовательские данные

        Returns:
            tuple[str, str]: (system_instruction, user_prompt)
        """
        # Системная инструкция содержит статические данные (шаблон + директивы)
        system_instruction = prompt_template.format(
            target_work_package_count=input_data['target_work_package_count'],
            user_directive=input_data['user_directive'],
            total_work_items=input_data['total_work_items']
        )

        # Пользовательский промпт содержит только динамические данные (JSON)
        user_prompt = json.dumps(input_data['source_work_items'],
                                ensure_ascii=False, indent=2)

        return system_instruction, user_prompt
    
    def _process_llm_response(self, llm_response: Any) -> List[Dict]:
        """
        Обрабатывает ответ от LLM и извлекает иерархическую структуру пакетов работ
        """
        try:
            if isinstance(llm_response, str):
                response_data = json.loads(llm_response)
            else:
                response_data = llm_response

            work_breakdown_structure = response_data.get('work_breakdown_structure', [])

            # Валидация и очистка данных
            validated_structure = []
            cat_counter = 1
            pkg_counter = 1

            for item in work_breakdown_structure:
                item_type = item.get('type', 'package')
                name = item.get('name', '')

                if item_type == 'category':
                    # Валидация категории
                    category_id = item.get('id', f'cat_{cat_counter:03d}')
                    validated_structure.append({
                        'id': category_id,
                        'type': 'category',
                        'name': name or f'Категория {cat_counter}',
                        'parent_id': None,
                        'created_at': datetime.now().isoformat()
                    })
                    cat_counter += 1

                elif item_type == 'package':
                    # Валидация пакета работ
                    package_id = item.get('id', f'pkg_{pkg_counter:03d}')
                    parent_id = item.get('parent_id', '')
                    description = item.get('description', '')

                    validated_structure.append({
                        'id': package_id,
                        'type': 'package',
                        'name': name or f'Пакет работ {pkg_counter}',
                        'description': description,
                        'parent_id': parent_id,
                        'created_at': datetime.now().isoformat()
                    })
                    pkg_counter += 1

            return validated_structure

        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА парсинга ответа LLM: {e}")
            logger.error(f"Сырой ответ от Claude: {llm_response}")
            raise Exception(f"Не удалось распарсить ответ от Claude: {e}")

# Функция для запуска агента из внешнего кода
async def run_work_packager(project_path: str) -> Dict[str, Any]:
    """
    Запускает агента work_packager для указанного проекта
    
    Args:
        project_path: Путь к папке проекта
        
    Returns:
        Результат работы агента
    """
    agent = WorkPackager()
    return await agent.process(project_path)

if __name__ == "__main__":
    # Тестирование агента
    test_project_path = "/home/imort/Herzog_v3/projects/34975055/d19120ef"
    
    if os.path.exists(test_project_path):
        print("🧪 Тестирование work_packager")
        result = asyncio.run(run_work_packager(test_project_path))
        print(f"Результат: {result}")
    else:
        print(f"❌ Тестовый проект не найден: {test_project_path}")