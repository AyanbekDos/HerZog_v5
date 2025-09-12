"""
Агент 2: "Распределитель" (works_to_packages.py)  
Присваивает каждую детализированную работу одному из укрупненных пакетов
Поддерживает батчинг для обработки больших объемов данных
"""

import json
import os
import asyncio
import logging
import math
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Импорты из нашей системы
from ..shared.gemini_client import gemini_client
from ..shared.truth_initializer import update_pipeline_status

logger = logging.getLogger(__name__)

class WorksToPackagesAssigner:
    """
    Агент для присвоения работ к укрупненным пакетам
    Обрабатывает большие объемы работ через батчинг
    """
    
    def __init__(self, batch_size: int = 50):
        self.agent_name = "works_to_packages"
        self.batch_size = batch_size
    
    async def process(self, project_path: str) -> Dict[str, Any]:
        """
        Главный метод обработки с поддержкой батчинга
        
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
            agent_folder = os.path.join(project_path, "5_works_to_packages")
            os.makedirs(agent_folder, exist_ok=True)
            
            # Извлекаем входные данные
            work_packages = truth_data.get('results', {}).get('work_packages', [])
            source_work_items = truth_data.get('source_work_items', [])
            
            if not work_packages:
                raise Exception("Не найдены пакеты работ. Сначала должен быть запущен work_packager")
            
            logger.info(f"📊 Обработка {len(source_work_items)} работ в {len(work_packages)} пакетов")
            
            # Загружаем промпт
            prompt_template = self._load_prompt()
            
            # Разбиваем работы на батчи и обрабатываем
            assigned_works = []
            total_batches = math.ceil(len(source_work_items) / self.batch_size)
            
            for batch_num in range(total_batches):
                start_idx = batch_num * self.batch_size
                end_idx = min((batch_num + 1) * self.batch_size, len(source_work_items))
                batch_works = source_work_items[start_idx:end_idx]
                
                logger.info(f"📦 Обработка батча {batch_num + 1}/{total_batches} ({len(batch_works)} работ)")
                
                # Обрабатываем батч
                batch_result = await self._process_batch(
                    batch_works, work_packages, prompt_template, 
                    batch_num, agent_folder
                )
                
                assigned_works.extend(batch_result)
            
            # Обновляем true.json с результатами
            self._update_truth_data(truth_data, assigned_works, truth_path)
            
            # Обновляем статус на завершено
            update_pipeline_status(truth_path, self.agent_name, "completed")
            
            logger.info(f"✅ Агент {self.agent_name} завершен успешно")
            logger.info(f"📊 Обработано {len(assigned_works)} работ")
            
            return {
                'success': True,
                'works_processed': len(assigned_works),
                'batches_processed': total_batches,
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
    
    async def _process_batch(self, batch_works: List[Dict], work_packages: List[Dict], 
                           prompt_template: str, batch_num: int, agent_folder: str) -> List[Dict]:
        """
        Обрабатывает один батч работ
        """
        # Подготавливаем входные данные для батча
        input_data = {
            'batch_works': [
                {
                    'id': work.get('id'),
                    'name': work.get('name', ''),
                    'code': work.get('code', '')
                }
                for work in batch_works
            ],
            'work_packages': work_packages,
            'batch_number': batch_num + 1
        }
        
        # Формируем запрос для LLM
        formatted_prompt = self._format_prompt(input_data, prompt_template)
        
        # ИСПРАВЛЕНО: Сохраняем входные данные С ПРОМПТОМ для отладки
        debug_input_data = {
            'input_data': input_data,
            'prompt_template': prompt_template,
            'formatted_prompt': formatted_prompt,
            'generated_at': datetime.now().isoformat(),
            'agent': self.agent_name,
            'batch_number': batch_num + 1
        }
        
        batch_input_path = os.path.join(agent_folder, f"batch_{batch_num+1:03d}_input.json")
        with open(batch_input_path, 'w', encoding='utf-8') as f:
            json.dump(debug_input_data, f, ensure_ascii=False, indent=2)
        
        # Вызываем Gemini API с указанием агента для оптимальной модели
        logger.info(f"📡 Отправка батча {batch_num + 1} в Gemini (works_to_packages -> gemini-2.5-flash-lite)")
        gemini_response = await gemini_client.generate_response(formatted_prompt, agent_name="works_to_packages")
        
        # Сохраняем ответ от LLM
        batch_response_path = os.path.join(agent_folder, f"batch_{batch_num+1:03d}_response.json")
        with open(batch_response_path, 'w', encoding='utf-8') as f:
            json.dump(gemini_response, f, ensure_ascii=False, indent=2)
        
        if not gemini_response.get('success', False):
            logger.error(f"Ошибка Gemini API для батча {batch_num + 1}: {gemini_response.get('error')}")
            # Возвращаем работы без назначения пакетов
            return batch_works
        
        # Обрабатываем ответ
        assignments = self._process_batch_response(gemini_response['response'], batch_works)
        
        return assignments
    
    def _load_prompt(self) -> str:
        """
        Загружает промпт-шаблон для агента
        """
        prompt_path = os.path.join(
            os.path.dirname(__file__), "..", "prompts", "works_to_packages_prompt.txt"
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
Ты - эксперт по строительству. Твоя задача - присвоить каждую детализированную работу одному из укрупненных пакетов работ.

ДОСТУПНЫЕ ПАКЕТЫ РАБОТ:
{work_packages}

РАБОТЫ ДЛЯ РАСПРЕДЕЛЕНИЯ (БАТЧ {batch_number}):
{batch_works}

ЗАДАЧА:
Для каждой работы выбери наиболее подходящий package_id из доступных пакетов. 
Анализируй название работы и ее код, чтобы понять, к какому типу работ она относится.

ПРИНЦИПЫ РАСПРЕДЕЛЕНИЯ:
1. Демонтажные работы → в пакет с демонтажем
2. Монтажные работы → в соответствующий монтажный пакет
3. Отделочные работы → в отделочные пакеты
4. Материалы обычно не включаются в пакеты (но если есть, то к соответствующим работам)

ФОРМАТ ОТВЕТА (строго JSON):
{{
    "assignments": [
        {{
            "work_id": "id_работы",
            "package_id": "pkg_001"
        }}
    ]
}}

ВАЖНО: Количество assignments должно точно соответствовать количеству входящих работ!
"""
    
    def _format_prompt(self, input_data: Dict, prompt_template: str) -> str:
        """
        Форматирует промпт с подстановкой данных
        """
        return prompt_template.format(
            work_packages=json.dumps(input_data['work_packages'], ensure_ascii=False, indent=2),
            batch_works=json.dumps(input_data['batch_works'], ensure_ascii=False, indent=2),
            batch_number=input_data['batch_number']
        )
    
    def _process_batch_response(self, llm_response: Any, original_works: List[Dict]) -> List[Dict]:
        """
        Обрабатывает ответ от LLM для батча
        """
        try:
            if isinstance(llm_response, str):
                response_data = json.loads(llm_response)
            else:
                response_data = llm_response
            
            assignments = response_data.get('assignments', [])
            
            # Создаем словарь для быстрого поиска
            assignment_dict = {assign['work_id']: assign['package_id'] for assign in assignments}
            
            # Обновляем оригинальные работы
            updated_works = []
            for work in original_works:
                work_copy = work.copy()
                work_id = work.get('id')
                
                if work_id in assignment_dict:
                    work_copy['package_id'] = assignment_dict[work_id]
                else:
                    # Если назначение не найдено, ошибка - не должно быть fallback
                    logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Не найдено назначение для работы {work_id}")
                    raise Exception(f"Gemini не назначил пакет для работы {work_id}. Проверьте промпт и ответ LLM.")
                
                updated_works.append(work_copy)
            
            return updated_works
            
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА парсинга ответа LLM для батча: {e}")
            logger.error(f"Сырой ответ от Gemini: {llm_response}")
            raise Exception(f"Не удалось распарсить ответ от Gemini для батча: {e}")
    
    def _update_truth_data(self, truth_data: Dict, assigned_works: List[Dict], truth_path: str):
        """
        Обновляет true.json с результатами назначений
        """
        # Обновляем source_work_items с package_id
        truth_data['source_work_items'] = assigned_works
        
        # Добавляем статистику в results
        if 'results' not in truth_data:
            truth_data['results'] = {}
        
        # Считаем статистику по пакетам
        package_stats = {}
        for work in assigned_works:
            package_id = work.get('package_id')
            if package_id:
                if package_id not in package_stats:
                    package_stats[package_id] = 0
                package_stats[package_id] += 1
        
        truth_data['results']['package_assignments'] = {
            'total_works': len(assigned_works),
            'works_per_package': package_stats,
            'assigned_at': datetime.now().isoformat()
        }
        
        # Сохраняем обновленный файл
        with open(truth_path, 'w', encoding='utf-8') as f:
            json.dump(truth_data, f, ensure_ascii=False, indent=2)

# Функция для запуска агента из внешнего кода
async def run_works_to_packages(project_path: str, batch_size: int = 50) -> Dict[str, Any]:
    """
    Запускает агента works_to_packages для указанного проекта
    
    Args:
        project_path: Путь к папке проекта
        batch_size: Размер батча для обработки
        
    Returns:
        Результат работы агента
    """
    agent = WorksToPackagesAssigner(batch_size=batch_size)
    return await agent.process(project_path)

if __name__ == "__main__":
    # Тестирование агента
    test_project_path = "/home/imort/Herzog_v3/projects/34975055/d19120ef"
    
    if os.path.exists(test_project_path):
        print("🧪 Тестирование works_to_packages")
        result = asyncio.run(run_works_to_packages(test_project_path))
        print(f"Результат: {result}")
    else:
        print(f"❌ Тестовый проект не найден: {test_project_path}")