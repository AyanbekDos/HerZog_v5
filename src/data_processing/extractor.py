"""
Модуль EXTRACTOR для HerZog v3.0
Задача: Извлечение сырых данных из Excel-файлов смет (Шаг 1 пайплайна)
"""

import pandas as pd
import uuid
import os
from typing import List, Dict, Optional
import logging


def find_table_header(df: pd.DataFrame) -> Optional[int]:
    """
    Найти начало таблицы по заголовкам "№ п/п" и "Обоснование"
    
    Args:
        df: DataFrame с данными из Excel
        
    Returns:
        Номер строки-заголовка или None если не найдено
    """
    for i, row in df.iterrows():
        row_text = ' '.join([str(cell).lower() for cell in row if pd.notna(cell) and str(cell).strip()])
        
        if ('№ п/п' in row_text or 'п/п' in row_text or '№п/п' in row_text) and \
           ('обоснование' in row_text) and \
           ('наименование' in row_text):
            return i
    
    return None


def is_valid_row(row: pd.Series, position_col_idx: int = 0) -> bool:
    """
    Проверить валидность строки по числовому значению в колонке "№ п/п"
    и содержимому других колонок (исключить мусорные строки)
    
    Args:
        row: Строка DataFrame
        position_col_idx: Индекс колонки "№ п/п" (по умолчанию 0)
        
    Returns:
        True если строка содержит валидные данные сметы
    """
    if len(row) <= position_col_idx:
        return False
        
    position_value = row.iloc[position_col_idx]
    
    if pd.isna(position_value):
        return False
    
    # Проверяем, что это число
    try:
        num_value = float(str(position_value).replace(',', '.'))
    except (ValueError, TypeError):
        return False
    
    # Проверяем второю колонку - должна быть не просто число
    if len(row) > 1 and pd.notna(row.iloc[1]):
        code_value = str(row.iloc[1]).strip()
        
        # Исключаем строки где вторая колонка - просто число
        try:
            float(code_value)
            # Если это просто число, проверяем есть ли осмысленное содержимое в других колонках
            if len(row) > 2 and pd.notna(row.iloc[2]):
                name_value = str(row.iloc[2]).strip()
                # Если третья колонка тоже просто число - это мусорная строка
                try:
                    float(name_value)
                    return False  # Строка типа "1, 2, 3" - мусорная
                except:
                    pass  # Третья колонка не число - хорошо
        except:
            pass  # Вторая колонка не число - хорошо
    
    return True


def extract_from_file(file_path: str) -> List[Dict]:
    """
    Извлечь данные из одного XLSX файла
    
    Args:
        file_path: Путь к XLSX файлу
        
    Returns:
        Список словарей с извлеченными данными
    """
    try:
        # Читаем весь лист
        df = pd.read_excel(file_path, header=None)
        
        # Находим заголовок таблицы
        header_row = find_table_header(df)
        
        if header_row is None:
            logging.warning(f"Не найден заголовок таблицы в файле {file_path}")
            return []
        
        # Работаем с данными под заголовком
        data_df = df.iloc[header_row + 1:]
        
        extracted_data = []
        file_name = os.path.basename(file_path)
        
        for idx, row in data_df.iterrows():
            # Проверяем валидность строки
            if not is_valid_row(row):
                continue
            
            # Извлекаем данные из колонок согласно найденной структуре
            position_num = str(row.iloc[0]) if len(row) > 0 and pd.notna(row.iloc[0]) else ""
            code = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else ""
            name = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else ""
            unit = str(row.iloc[7]) if len(row) > 7 and pd.notna(row.iloc[7]) else ""
            quantity = str(row.iloc[8]) if len(row) > 8 and pd.notna(row.iloc[8]) else ""
            
            # Создаем плоский словарь с единым UUID
            record = {
                'id': str(uuid.uuid4()),
                'source_file': file_name,
                'position_num': position_num,
                'code': code,
                'name': name,
                'unit': unit,
                'quantity': quantity
            }
            
            extracted_data.append(record)
            
        logging.info(f"Извлечено {len(extracted_data)} записей из файла {file_name}")
        return extracted_data
        
    except Exception as e:
        logging.error(f"Ошибка при обработке файла {file_path}: {str(e)}")
        return []


def extract_from_files(file_paths: List[str]) -> List[Dict]:
    """
    Главная функция модуля EXTRACTOR
    
    Args:
        file_paths: Список путей к XLSX файлам
        
    Returns:
        master_list: Единый, плоский список словарей
    """
    master_list = []
    
    for file_path in file_paths:
        if not os.path.exists(file_path):
            logging.warning(f"Файл не найден: {file_path}")
            continue
            
        file_data = extract_from_file(file_path)
        master_list.extend(file_data)
    
    logging.info(f"Общее количество извлеченных записей: {len(master_list)}")
    return master_list


def extract_estimates(input_path: str) -> List[Dict]:
    """
    Главная функция для пайплайна - извлечение данных из всех Excel файлов в папке
    
    Args:
        input_path: Путь к папке 0_input с Excel файлами
        
    Returns:
        Список извлеченных записей
    """
    excel_files = []
    
    # Поиск всех Excel файлов в папке input
    for file_name in os.listdir(input_path):
        if file_name.endswith('.xlsx') and not file_name.startswith('~'):
            excel_files.append(os.path.join(input_path, file_name))
    
    if not excel_files:
        logging.warning(f"Не найдено Excel файлов в папке: {input_path}")
        return []
    
    logging.info(f"Найдено Excel файлов для обработки: {len(excel_files)}")
    
    # Извлекаем данные из всех найденных файлов
    return extract_from_files(excel_files)


if __name__ == "__main__":
    import sys
    import json
    
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    
    # Проверяем аргументы командной строки
    if len(sys.argv) >= 3:
        # Режим реального использования - аргументы: путь к Excel файлу и путь к проекту
        excel_file = sys.argv[1] 
        project_dir = sys.argv[2]
        
        # Проверяем что файл существует
        if not os.path.exists(excel_file):
            logging.error(f"Не найден файл: {excel_file}")
            sys.exit(1)
        
        # Запускаем извлечение
        try:
            result = extract_from_files([excel_file])
            
            # Сохраняем результат
            output_file = os.path.join(project_dir, '1_extracted', 'raw_estimates.json')
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logging.info(f"✅ Результат сохранен: {output_file}")
            print(f"Извлечено {len(result)} записей")
            if result:
                print("Пример первой записи:")
                for key, value in result[0].items():
                    print(f"  {key}: {value}")
            
        except Exception as e:
            logging.error(f"Ошибка при извлечении: {e}")
            sys.exit(1)
    
    else:
        # Режим тестирования - без аргументов
        logging.info("Режим тестирования extractor...")
        print("Использование: python -m src.data_processing.extractor <путь_к_excel> <путь_к_проекту>")
        
        # Тестовый запуск для демонстрации
        test_files = ["/home/imort/Herzog_v2claude/income/tretiy/02_01_01_Стены_ЛСР_по_Методике_2020_РИМ1.xlsx"]
        
        if os.path.exists(test_files[0]):
            result = extract_from_files(test_files)
            
            print(f"Тестовое извлечение: {len(result)} записей")
            if result:
                print("Пример первой записи:")
                for key, value in result[0].items():
                    print(f"  {key}: {value}")
        else:
            print("Тестовый файл не найден - пропускаем тестирование")