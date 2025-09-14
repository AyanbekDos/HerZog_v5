"""
Модуль для классификации сметных позиций через Gemini 2.5 Pro
"""

import json
import logging
import os
import uuid
from typing import List, Dict, Optional
from dotenv import load_dotenv
from ..shared.gemini_client import gemini_client

load_dotenv()

def load_prompt_template() -> str:
    """Загружает шаблон промпта из файла"""
    try:
        prompt_path = os.path.join(os.path.dirname(__file__), '../prompts/gemini_classification_prompt.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.error(f"Ошибка загрузки промпта: {e}")
        return ""

async def classify_with_gemini(items: List[Dict], project_dir: str = None) -> Dict[str, Dict]:
    """
    Классификация неопределенных позиций через Gemini 2.5 Pro
    
    Args:
        items: Список неопределенных позиций с полями code, name
        project_dir: Путь к папке проекта для сохранения llm_input/response
        
    Returns:
        Словарь {id: {"classification": str, "reasoning": str}}
    """
    if not items:
        return {}
    
    # Используем реальные ID из данных и готовим минимальные данные
    items_with_id = []
    id_mapping = {}
    
    for item in items:
        item_id = item.get('id', str(uuid.uuid4()))  # Используем реальный id или генерируем если нет
        id_mapping[item_id] = item
        
        items_with_id.append({
            "id": item_id,
            "full_name": f"{item.get('code', '')} {item.get('name', '')}"
        })
    
    # Загружаем и заполняем шаблон промпта
    prompt_template = load_prompt_template()
    if not prompt_template:
        logging.error("Не удалось загрузить шаблон промпта")
        return {}
    
    # Разделяем системную инструкцию и пользовательские данные
    system_instruction = prompt_template.replace('{ITEMS_JSON}', "")  # Убираем плейсхолдер
    system_instruction = system_instruction.replace("Анализируй следующие позиции:", "Проанализируй строительные позиции в формате JSON, которые будут предоставлены пользователем:")
    user_prompt = json.dumps(items_with_id, ensure_ascii=False, indent=2)

    try:
        # Используем асинхронный gemini_client с системной инструкцией
        logging.info("📡 Отправка запроса на классификацию в Gemini с системной инструкцией (classifier -> gemini-2.5-flash-lite)")
        gemini_response = await gemini_client.generate_response(
            prompt=user_prompt,
            agent_name="classifier",
            system_instruction=system_instruction
        )

        # Сохраняем llm_input и llm_response если указана папка проекта
        if project_dir:
            classified_dir = os.path.join(project_dir, "2_classified")
            os.makedirs(classified_dir, exist_ok=True)

            # Сохраняем структурированные данные для отладки
            llm_input_path = os.path.join(classified_dir, "llm_input.json")
            llm_input_data = {
                "system_instruction": system_instruction,
                "user_prompt": user_prompt,
                "items": []
            }

            # Добавляем реальные ID к каждой позиции
            for item in items:
                # Используем item_id напрямую - он уже есть в id_mapping
                item_id = item.get('id')
                if item_id and item_id in id_mapping:
                    llm_input_data["items"].append({
                        "id": item_id,
                        "code": item.get('code', ''),
                        "name": item.get('name', '')
                    })

            with open(llm_input_path, 'w', encoding='utf-8') as f:
                json.dump(llm_input_data, f, ensure_ascii=False, indent=2)

            # Сохраняем ответ от Gemini
            llm_response_path = os.path.join(classified_dir, "llm_response.json")
            with open(llm_response_path, 'w', encoding='utf-8') as f:
                json.dump(gemini_response, f, ensure_ascii=False, indent=2)

            logging.info(f"Сохранены llm_input.json и llm_response.json в {classified_dir}")

        # Проверяем успешность ответа
        if not gemini_response.get('success', False):
            logging.error(f"Ошибка Gemini API: {gemini_response.get('error', 'Неизвестная ошибка')}")
            return {}

        # Извлекаем текст ответа
        response_text = gemini_response.get('raw_text', '')
        logging.info(f"Получен ответ от Gemini: {response_text[:200]}...")

        # Парсим JSON ответ из gemini_response['response'] (уже распарсен)
        classifications = gemini_response.get('response', [])

        if isinstance(classifications, list):
            # Преобразуем в словарь по ID
            result = {}
            for classification in classifications:
                item_id = classification.get('id') or classification.get('uuid')  # Поддерживаем оба варианта для обратной совместимости
                if item_id in id_mapping:
                    result[item_id] = {
                        'classification': classification.get('classification', 'Неопределенное'),
                        'reasoning': classification.get('reasoning', ''),
                        'original_item': id_mapping[item_id]
                    }

            logging.info(f"Gemini успешно классифицировал {len(result)} позиций")
            return result
        else:
            logging.error("Gemini вернул ответ не в виде списка")
            return {}

    except Exception as e:
        logging.error(f"Ошибка при запросе к Gemini API: {str(e)}")
        return {}

def convert_gemini_result(gemini_result: Dict) -> Dict:
    """
    Конвертирует результат Gemini в формат совместимый с основным классификатором
    
    Args:
        gemini_result: Результат от classify_with_gemini
        
    Returns:
        Словарь с полями classification, reasoning
    """
    classification = gemini_result.get('classification', 'Неопределенное')
    
    return {
        'classification': classification,
        'gemini_confidence': 0.85,  # Примерная уверенность
        'gemini_reasoning': gemini_result.get('reasoning', '')
    }

if __name__ == "__main__":
    # Тестирование модуля
    logging.basicConfig(level=logging.INFO)
    
    test_items = [
        {
            'code': '47-1',
            'name': 'Погрузка в автотранспортное средство: мусор строительный с погрузкой вручную'
        },
        {
            'code': 'КП',
            'name': 'Размещение строительного мусора на полигоне ТБО'
        }
    ]
    
    result = classify_with_gemini(test_items)
    print(f"Результат классификации: {result}")