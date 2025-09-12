"""
Модуль для классификации сметных позиций через Gemini 2.5 Pro
"""

import json
import logging
import os
import uuid
from typing import List, Dict, Optional
import requests
from dotenv import load_dotenv

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

def classify_with_gemini(items: List[Dict], project_dir: str = None) -> Dict[str, Dict]:
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
        
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logging.error("Не найден API ключ GEMINI_API_KEY")
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
    
    items_json = json.dumps(items_with_id, ensure_ascii=False, indent=2)
    prompt = prompt_template.replace('{ITEMS_JSON}', items_json)
    
    # Сохраняем llm_input.json если указана папка проекта
    if project_dir:
        llm_input_path = os.path.join(project_dir, "2_classified", "llm_input.json")
        
        # Подготавливаем данные для сохранения
        llm_input_data = {
            "prompt": prompt,
            "items": []
        }
        
        # Добавляем реальные ID к каждой позиции
        for item in items:
            # Найдем соответствующий ID для этой позиции
            matching_id_item = None
            for id_item in items_with_id:
                if id_item["full_name"] == f"{item.get('code', '')} {item.get('name', '')}":
                    matching_id_item = id_item
                    break
            
            if matching_id_item:
                llm_input_data["items"].append({
                    "id": matching_id_item["id"],
                    "code": item.get('code', ''),
                    "name": item.get('name', '')
                })
        
        with open(llm_input_path, 'w', encoding='utf-8') as f:
            json.dump(llm_input_data, f, ensure_ascii=False, indent=2)
        logging.info(f"Сохранен llm_input.json: {llm_input_path}")
    
    try:
        # Запрос к Gemini API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={api_key}"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 8192
            }
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Сохраняем llm_response.json если указана папка проекта
            if project_dir:
                llm_response_path = os.path.join(project_dir, "2_classified", "llm_response.json")
                with open(llm_response_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logging.info(f"Сохранен llm_response.json: {llm_response_path}")
            
            # Извлекаем текст ответа
            try:
                response_text = data['candidates'][0]['content']['parts'][0]['text']
                logging.info(f"Получен ответ от Gemini: {response_text[:200]}...")
                
                # Парсим JSON ответ
                # Ищем JSON массив в тексте
                start_idx = response_text.find('[')
                end_idx = response_text.rfind(']')
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_text = response_text[start_idx:end_idx+1]
                    classifications = json.loads(json_text)
                    
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
                    logging.error("Не найден валидный JSON в ответе Gemini")
                    return {}
                    
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                logging.error(f"Ошибка парсинга ответа Gemini: {e}")
                return {}
        
        else:
            logging.error(f"Ошибка API Gemini: {response.status_code} - {response.text}")
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