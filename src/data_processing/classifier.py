"""
Модуль CLASSIFIER
Задача: Реализовать гибридный классификатор, который принимает на вход master_list,
классифицирует каждую позицию и обогащает ее дополнительными данными из API "Сметного Дела".
"""

import requests
import logging
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Импортируем после определения функций внизу файла

load_dotenv()


def classify_locally(item: Dict) -> Optional[str]:
    """
    Локальная классификация по жестким правилам
    
    Args:
        item: Словарь с данными позиции
        
    Returns:
        "Работа", "Материал", "Иное" или None
    """
    code = item.get('code', '').upper().strip()
    name = item.get('name', '').lower().strip()
    
    # Шаг 2.1: Классификация по шифру
    work_prefixes = ['ГЭСН', 'ТЕР', 'ТЕРм', 'ТЕРр', 'ФЕР', 'ГЭСНМ', 'ГЭСНР', 'ГЭСНП', 'ГЭСНМР']
    material_prefixes = ['ФСБЦ', 'ТССЦ', 'ТЦ', 'ФССЦ', 'ФССЦм', 'ФССЦо']
    
    for prefix in work_prefixes:
        if code.startswith(prefix):
            return "Работа"
    
    for prefix in material_prefixes:
        if code.startswith(prefix):
            return "Материал"
    
    # Шаг 2.2: Классификация на "Иное" по ключевым словам в названии
    other_keywords = [
        'накладные расходы', 'сметная прибыль', 'вспомогательные ресурсы',
        'на каждые', 'итого', 'всего', 'транспорт', 'доставка материала'
    ]
    
    for keyword in other_keywords:
        if keyword in name:
            return "Иное"
    
    return None


def get_smetnoedelo_data(code: str, api_token: str) -> Optional[Dict]:
    """
    ВРЕМЕННО ОТКЛЮЧЕНО - API токен исчерпан
    """
    return None  # Временно отключаем API пока не получите новый токен

def get_smetnoedelo_data_ORIGINAL(code: str, api_token: str) -> Optional[Dict]:
    """
    Получение данных из API "Сметного Дела"
    
    Args:
        code: Шифр расценки
        api_token: API токен
        
    Returns:
        Словарь с данными или None при ошибке
    """
    try:
        # Определяем базу по коду (согласно документации API)
        code_upper = code.upper()
        
        base_mapping = {
            'ГЭСН': 'gesn',
            'ГЭСНм': 'gesnm', 
            'ГЭСНмр': 'gesnmr',
            'ГЭСНп': 'gesnp',
            'ГЭСНр': 'gesnr',
            'ФЕР': 'fer',
            'ФЕРм': 'ferm',
            'ФЕРмр': 'fermr', 
            'ФЕРп': 'ferp',
            'ФЕРр': 'ferr',
            'ТЕР': 'gesn',  # Территориальные расценки обычно в ГЭСН
            # Материалы - пока не работают в API
            'ФСБЦ': 'fsbcm',
            'ФССЦм': 'fsscm',
            'ФССЦо': 'fssco',
            'ФСЭМ': 'fsem'
        }
        
        base = None
        for prefix, base_code in base_mapping.items():
            if code_upper.startswith(prefix):
                base = base_code
                break
        
        if not base:
            logging.warning(f"Не удалось определить базу для кода {code}")
            return None
        
        # Запрос к API (правильный формат из test_api.py)
        url = "https://cs.smetnoedelo.ru/api/"
        params = {
            'token': api_token,
            'base': base,
            'code': code
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Проверяем на ошибки в ответе
            if data.get('error'):
                logging.warning(f"API вернул ошибку для кода {code}: {data.get('error')}")
                return None
            
            # Извлекаем иерархию из TREE структуры (новый формат API)
            hierarchy_parts = []
            tree_data = data.get('TREE', [])
            for item in tree_data:
                if 'NAME' in item:
                    hierarchy_parts.append(item['NAME'])
            
            result = {
                'official_name': data.get('BASE_NAME', '')  # Используем BASE_NAME вместо NAME
            }
            
            
            logging.info(f"API успешно вернул данные для {code}: {result['official_name']}")
            return result
        
        elif response.status_code == 404:
            logging.warning(f"Код {code} не найден в API Сметного Дела")
            return None
        
        else:
            logging.error(f"Ошибка API Сметного Дела: {response.status_code}")
            return None
            
    except Exception as e:
        logging.error(f"Ошибка при запросе к API Сметного Дела для кода {code}: {str(e)}")
        return None


def classify_items(master_list: List[Dict], progress_callback=None, project_dir: str = None) -> List[Dict]:
    """
    Главная функция модуля CLASSIFIER
    
    Args:
        master_list: Результат работы модуля EXTRACTOR
        
    Returns:
        classified_list: Список с классифицированными позициями
    """
    classified_list = []
    api_token = os.getenv('SMETNOEDELO_API_KEY')
    
    if not api_token:
        logging.error("Не найден API ключ SMETNOEDELO_API_KEY")
        logging.info("Работаю только с локальной классификацией без API обогащения")
    
    # Кэш для API запросов
    api_cache = {}
    total_items = len(master_list)
    
    for i, item in enumerate(master_list):
        # Создаем копию элемента для обработки
        classified_item = item.copy()
        
        # Шаг 3.1: Локальная классификация
        classification = classify_locally(item)
        
        if classification:
            classified_item['classification'] = classification
            
            # Шаг 3.3: Обогащение данными из API для работ (только если есть API ключ)
            if classification == "Работа" and api_token:
                code = item.get('code', '')
                
                # Проверяем кэш
                if code in api_cache:
                    api_data = api_cache[code]
                else:
                    api_data = get_smetnoedelo_data(code, api_token)
                    api_cache[code] = api_data
                
                if api_data:
                    # Обновляем официальное наименование если получено из API
                    if api_data['official_name']:
                        classified_item['name'] = api_data['official_name']
        
        else:
            # Помечаем как неопределенное для последующей групповой обработки через Gemini
            classified_item['classification'] = "Неопределенное"
        
        classified_list.append(classified_item)
        
        # Вызываем callback для обновления прогресса
        if progress_callback and i % 5 == 0:  # Каждые 5 элементов
            progress_callback(i + 1, total_items)
    
    # Шаг 3.4: Групповая обработка неопределенных позиций И "Иное" через Gemini
    # Теперь отправляем в Gemini всё что не "Работа" и не "Материал"
    undefined_items = [item for item in classified_list if item['classification'] in ['Неопределенное', 'Иное']]
    
    if undefined_items:
        logging.info(f"Отправляю {len(undefined_items)} позиций в Gemini для анализа ('Иное' + 'Неопределенные')")
        
        try:
            from .gemini_classifier import classify_with_gemini, convert_gemini_result
            
            # Подготавливаем данные для Gemini (только код и название)
            gemini_input = []
            item_mapping = {}
            
            for i, item in enumerate(undefined_items):
                gemini_input.append({
                    'code': item.get('code', ''),
                    'name': item.get('name', '')
                })
                item_mapping[i] = item
            
            # Получаем результаты от Gemini
            gemini_results = classify_with_gemini(gemini_input, project_dir)
            
            # Обновляем классификацию для найденных позиций
            for item_uuid, gemini_result in gemini_results.items():
                # Находим соответствующий элемент в classified_list
                original_item = gemini_result['original_item']
                
                for classified_item in classified_list:
                    if classified_item.get('id') == original_item.get('id'):
                        
                        # Конвертируем результат Gemini
                        converted_result = convert_gemini_result(gemini_result)
                        
                        # Обновляем позицию (заменяем "Иное" или "Неопределенное" на результат Gemini)
                        classified_item.update(converted_result)
                        break
            
            logging.info(f"Gemini обработал {len(gemini_results)} позиций (включая 'Иное' и 'Неопределенные')")
            
        except Exception as e:
            logging.error(f"Ошибка при обработке неопределенных позиций через Gemini: {e}")
    
    # Статистика классификации (после обработки Gemini)
    classifications = [item['classification'] for item in classified_list]
    work_count = classifications.count('Работа')
    material_count = classifications.count('Материал')
    other_count = classifications.count('Иное')
    unknown_count = classifications.count('Неопределенное')
    
    logging.info(f"Финальная статистика классификации:")
    logging.info(f"  Работ: {work_count}")
    logging.info(f"  Материалов: {material_count}")
    logging.info(f"  Иное: {other_count}")
    logging.info(f"  Неопределенных: {unknown_count}")
    
    return classified_list


def classify_estimates(input_file: str) -> List[Dict]:
    """
    Главная функция для пайплайна - классификация извлеченных данных
    
    Args:
        input_file: Путь к файлу raw_estimates.json
        
    Returns:
        Список классифицированных записей
    """
    import json
    
    # Читаем сырые данные
    with open(input_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    logging.info(f"Загружено {len(raw_data)} записей для классификации")
    
    # Определяем путь к проекту из input_file
    project_dir = None
    if "projects/" in input_file:
        # Извлекаем путь до папки проекта
        parts = input_file.split("/")
        if "projects" in parts:
            project_idx = parts.index("projects")
            if project_idx + 2 < len(parts):  # projects/user_id/project_id
                project_dir = "/".join(parts[:project_idx + 3])
    
    # Классифицируем данные
    classified_data = classify_items(raw_data, project_dir=project_dir)
    
    logging.info(f"Классификация завершена: {len(classified_data)} записей")
    
    return classified_data


if __name__ == "__main__":
    import sys
    import json
    
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        # Режим реального использования - аргумент = путь к проекту
        project_dir = sys.argv[1]
        raw_estimates_file = os.path.join(project_dir, '1_extracted', 'raw_estimates.json')
        
        # Проверяем что файл существует
        if not os.path.exists(raw_estimates_file):
            logging.error(f"Не найден файл: {raw_estimates_file}")
            sys.exit(1)
        
        # Запускаем классификацию
        try:
            result = classify_estimates(raw_estimates_file)
            
            # Сохраняем результат
            output_file = os.path.join(project_dir, '2_classified', 'classified_estimates.json')
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logging.info(f"✅ Результат сохранен: {output_file}")
            print(f"Классифицировано {len(result)} позиций")
            
        except Exception as e:
            logging.error(f"Ошибка при классификации: {e}")
            sys.exit(1)
    
    else:
        # Режим тестирования - без аргументов
        logging.info("Режим тестирования classifier...")
        
        # Тестовые данные
        test_data = [
            {
                'id': 'test-1',
                'source_file': 'test.xlsx',
                'position_num': '1',
                'code': 'ГЭСН46-02-009-02',
                'name': 'Отбивка штукатурки с поверхностей',
                'unit': '100 м2',
                'quantity': '7.77'
            },
            {
                'id': 'test-2',
                'source_file': 'test.xlsx',
                'position_num': '2',
                'code': 'ФСБЦ-14.4.01.02-0012',
                'name': 'Смесь сухая штукатурная',
                'unit': 'кг',
                'quantity': '1000'
            }
        ]
        
        result = classify_items(test_data)
        
        print(f"Классифицировано {len(result)} позиций")
        for item in result:
            print(f"Позиция {item['position_num']}: {item['classification']}")
