"""
Агент 1: "Архитектор" (work_packager.py)
Создает укрупненные пакеты работ для строительного проекта
"""

import json
import os
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Импорты из нашей системы
from ..shared.gemini_client import gemini_client
from ..shared.truth_initializer import update_pipeline_status

logger = logging.getLogger(__name__)

class WorkPackager:
    """
    Агент для создания укрупненных пакетов работ
    Анализирует детализированные работы и создает высокоуровневую структуру проекта
    """
    
    def __init__(self):
        self.agent_name = "work_packager"
    
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
            
            with open(os.path.join(llm_input_path, "llm_input.json"), 'w', encoding='utf-8') as f:
                json.dump(debug_input_data, f, ensure_ascii=False, indent=2)
            
            # Вызываем Gemini API с указанием агента для оптимальной модели
            logger.info("📡 Отправка запроса в Gemini (work_packager -> gemini-2.5-pro)")
            gemini_response = await gemini_client.generate_response(formatted_prompt, agent_name="work_packager")
            
            # Сохраняем ответ от LLM
            with open(os.path.join(llm_input_path, "llm_response.json"), 'w', encoding='utf-8') as f:
                json.dump(gemini_response, f, ensure_ascii=False, indent=2)
            
            if not gemini_response.get('success', False):
                raise Exception(f"Ошибка Gemini API: {gemini_response.get('error', 'Неизвестная ошибка')}")
            
            # Обрабатываем ответ
            work_packages = self._process_llm_response(gemini_response['response'])
            
            # Обновляем true.json
            truth_data['results']['work_packages'] = work_packages
            
            with open(truth_path, 'w', encoding='utf-8') as f:
                json.dump(truth_data, f, ensure_ascii=False, indent=2)
            
            # Обновляем статус на завершено
            update_pipeline_status(truth_path, self.agent_name, "completed")
            
            logger.info(f"✅ Агент {self.agent_name} завершен успешно")
            logger.info(f"📊 Создано {len(work_packages)} пакетов работ")
            
            return {
                'success': True,
                'work_packages_created': len(work_packages),
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
        
        # Получаем директиву пользователя
        project_inputs = truth_data.get('project_inputs', {})
        target_count = project_inputs.get('target_work_package_count', 15)
        conceptualizer_directive = project_inputs.get('agent_directives', {}).get('conceptualizer', '')
        
        return {
            'source_work_items': work_items_for_llm,
            'target_work_package_count': target_count,
            'user_directive': conceptualizer_directive,
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
    
    def _format_prompt(self, input_data: Dict, prompt_template: str) -> str:
        """
        Форматирует промпт с подстановкой данных
        """
        return prompt_template.format(
            source_work_items=json.dumps(input_data['source_work_items'], 
                                       ensure_ascii=False, indent=2),
            target_work_package_count=input_data['target_work_package_count'],
            user_directive=input_data['user_directive'],
            total_work_items=input_data['total_work_items']
        )
    
    def _process_llm_response(self, llm_response: Any) -> List[Dict]:
        """
        Обрабатывает ответ от LLM и извлекает пакеты работ
        """
        try:
            if isinstance(llm_response, str):
                response_data = json.loads(llm_response)
            else:
                response_data = llm_response
                
            work_packages = response_data.get('work_packages', [])
            
            # Валидация и очистка данных
            validated_packages = []
            for i, package in enumerate(work_packages):
                package_id = package.get('package_id', f'pkg_{i+1:03d}')
                name = package.get('name', f'Пакет работ {i+1}')
                description = package.get('description', '')
                
                validated_packages.append({
                    'package_id': package_id,
                    'name': name,
                    'description': description,
                    'created_at': datetime.now().isoformat()
                })
            
            return validated_packages
            
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА парсинга ответа LLM: {e}")
            logger.error(f"Сырой ответ от Gemini: {llm_response}")
            raise Exception(f"Не удалось распарсить ответ от Gemini: {e}")

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