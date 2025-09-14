#!/usr/bin/env python3
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
