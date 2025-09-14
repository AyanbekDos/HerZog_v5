#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диагностика ошибки RECITATION в Gemini API
Создает детальный отчет о проблеме для других разработчиков
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path


def create_recitation_debug_report():
    """Создает полный отчет об ошибке RECITATION"""

    # Создаем папку для отчета
    report_dir = Path("RECITATION_ERROR_REPORT")
    if report_dir.exists():
        shutil.rmtree(report_dir)
    report_dir.mkdir()

    # Основной отчет
    report_content = f"""
# КРИТИЧЕСКАЯ ОШИБКА: Gemini RECITATION блокировка

## Дата создания отчета: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## ОПИСАНИЕ ПРОБЛЕМЫ

Система HerZog v3.0 сталкивается с критической ошибкой при работе с Gemini API:
- Ошибка: "Контент заблокирован Gemini из-за RECITATION"
- Агент: scheduler_and_staffer
- Модель: gemini-2.5-pro
- Размер промпта: 20364 символов
- Все 5 попыток заблокированы

RECITATION означает, что Gemini считает промпт слишком похожим на существующий контент
из своих обучающих данных и блокирует ответ из соображений авторских прав.

## ЛОКАЛИЗАЦИЯ ПРОБЛЕМЫ

Проблемный проект: /home/imort/Herzog_v3/projects/34975055/2b07f457
Время возникновения: 2025-09-14 22:48:32

## ФАЙЛЫ В ОТЧЕТЕ

1. scheduler_and_staffer_prompt.txt - проблемный промпт
2. gemini_client.py - клиент API с логикой повторов
3. scheduler_and_staffer.py - агент планирования
4. truth.json - данные проекта (если доступны)
5. error_log.txt - полный лог ошибок

## ВОЗМОЖНЫЕ РЕШЕНИЯ

1. **Модификация промпта**: Изменить формулировки, добавить уникальности
2. **Смена модели**: Попробовать другую версию Gemini
3. **Разбиение промпта**: Уменьшить размер, обработать частями
4. **Фильтрация данных**: Убрать потенциально проблемный контент
5. **Fallback на другую модель**: OpenAI GPT как резервный вариант

## КРИТИЧНОСТЬ

🔴 ВЫСОКАЯ - блокирует работу всего пайплайна обработки
Без решения система не может создавать календарные планы.
"""

    # Сохраняем основной отчет
    with open(report_dir / "README.txt", "w", encoding="utf-8") as f:
        f.write(report_content)

    # Копируем ключевые файлы
    files_to_copy = [
        ("src/prompts/scheduler_and_staffer_prompt.txt", "scheduler_and_staffer_prompt.txt"),
        ("src/shared/gemini_client.py", "gemini_client.py"),
        ("src/ai_agents/scheduler_and_staffer.py", "scheduler_and_staffer.py"),
        ("src/ai_agents/new_agent_runner.py", "new_agent_runner.py")
    ]

    for source, dest in files_to_copy:
        source_path = Path(source)
        if source_path.exists():
            shutil.copy2(source_path, report_dir / dest)
            print(f"✅ Скопирован: {source}")
        else:
            print(f"❌ Не найден: {source}")

    # Копируем проблемный truth.json если доступен
    problem_project = Path("projects/34975055/2b07f457")
    for stage in ["3_prepared", "4_packaged", "5_counted"]:
        truth_file = problem_project / stage / "truth.json"
        if truth_file.exists():
            shutil.copy2(truth_file, report_dir / f"truth_{stage}.json")
            print(f"✅ Скопирован truth.json из {stage}")
            break

    # Создаем лог ошибок
    error_log = """
2025-09-14 22:48:32,607 - src.shared.gemini_client - ERROR - ❌ Ошибка при обращении к Gemini (попытка 1): Контент заблокирован Gemini из-за RECITATION
2025-09-14 22:48:33,608 - src.shared.gemini_client - INFO - 📡 Попытка 2/5: gemini-2.5-pro (scheduler_and_staffer) (промт: 20364 символов)
2025-09-14 22:49:07,580 - src.shared.gemini_client - ERROR - ❌ Ошибка при обращении к Gemini (попытка 2): Контент заблокирован Gemini из-за RECITATION
2025-09-14 22:49:08,582 - src.shared.gemini_client - INFO - 📡 Попытка 3/5: gemini-2.5-pro (scheduler_and_staffer) (промт: 20364 символов)
2025-09-14 22:49:42,683 - src.shared.gemini_client - ERROR - ❌ Ошибка при обращении к Gemini (попытка 3): Контент заблокирован Gemini из-за RECITATION
2025-09-14 22:49:43,684 - src.shared.gemini_client - INFO - 📡 Попытка 4/5: gemini-2.5-pro (scheduler_and_staffer) (промт: 20364 символов)
2025-09-14 22:50:18,304 - src.shared.gemini_client - ERROR - ❌ Ошибка при обращении к Gemini (попытка 4): Контент заблокирован Gemini из-за RECITATION
2025-09-14 22:50:19,306 - src.shared.gemini_client - INFO - 📡 Попытка 5/5: gemini-2.5-pro (scheduler_and_staffer) (промт: 20364 символов)
2025-09-14 22:50:54,013 - src.shared.gemini_client - ERROR - ❌ Ошибка при обращении к Gemini (попытка 5): Контент заблокирован Gemini из-за RECITATION
2025-09-14 22:50:54,013 - src.ai_agents.scheduler_and_staffer - ERROR - ❌ КРИТИЧЕСКАЯ ОШИБКА Gemini API для батча 1: Контент заблокирован Gemini из-за RECITATION
2025-09-14 22:50:54,013 - src.ai_agents.scheduler_and_staffer - ERROR - ❌ Ошибка агента scheduler_and_staffer: Gemini API не смог обработать батч 1. Проверьте промпт и соединение.
2025-09-14 22:50:54,019 - src.ai_agents.new_agent_runner - ERROR - ❌ Агент scheduler_and_staffer завершился с ошибкой: Gemini API не смог обработать батч 1. Проверьте промпт и соединение.
2025-09-14 22:50:55,255 - src.main_pipeline - ERROR - ❌ Ошибка в пайплайне: Агент scheduler_and_staffer завершился с ошибкой
"""

    with open(report_dir / "error_log.txt", "w", encoding="utf-8") as f:
        f.write(error_log.strip())

    # Анализируем размер промпта
    prompt_file = Path("src/prompts/scheduler_and_staffer_prompt.txt")
    if prompt_file.exists():
        prompt_text = prompt_file.read_text(encoding="utf-8")
        analysis = f"""
# АНАЛИЗ ПРОМПТА

Размер файла: {len(prompt_text)} символов
Строки: {len(prompt_text.splitlines())}

ПОТЕНЦИАЛЬНЫЕ ПРОБЛЕМЫ:
- Слишком большой размер (20364 символа)
- Возможно содержит шаблонные фразы из интернета
- Может содержать копирайт-контент

РЕКОМЕНДАЦИИ:
1. Сократить промпт на 50%
2. Заменить шаблонные фразы уникальными
3. Убрать потенциально проблемный контент
4. Добавить больше контекста проекта
"""

        with open(report_dir / "prompt_analysis.txt", "w", encoding="utf-8") as f:
            f.write(analysis)

    # Создаем скрипт для быстрого тестирования
    test_script = '''#!/usr/bin/env python3
# Тест для проверки исправления RECITATION ошибки

import sys
sys.path.append('..')
from src.shared.gemini_client import GeminiClient

def test_recitation_fix():
    """Тестирует исправленный промпт на RECITATION"""
    client = GeminiClient()

    # Загружаем исправленный промпт
    with open("../src/prompts/scheduler_and_staffer_prompt.txt", "r", encoding="utf-8") as f:
        prompt = f.read()

    print(f"Тестируем промпт размером: {len(prompt)} символов")

    try:
        # Тест с минимальными данными
        test_data = {"packages": [{"name": "test", "work_items": []}]}
        result = client.call_gemini(prompt, test_data, "test_recitation")
        print("✅ УСПЕХ: Промпт прошел без RECITATION ошибки!")
        return True
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return False

if __name__ == "__main__":
    test_recitation_fix()
'''

    with open(report_dir / "test_fix.py", "w", encoding="utf-8") as f:
        f.write(test_script)

    print(f"\n🎯 ОТЧЕТ СОЗДАН: {report_dir.absolute()}")
    print(f"📁 Включено {len(list(report_dir.glob('*')))} файлов")
    print("\n📋 ДЛЯ РАЗРАБОТЧИКОВ:")
    print("1. Читайте README.txt для понимания проблемы")
    print("2. Анализируйте scheduler_and_staffer_prompt.txt")
    print("3. Используйте test_fix.py для проверки исправлений")
    print("4. Проблема критичная - блокирует весь пайплайн!")


if __name__ == "__main__":
    create_recitation_debug_report()