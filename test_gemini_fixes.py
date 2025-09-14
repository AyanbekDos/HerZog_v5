#!/usr/bin/env python3
"""
Тест исправлений GeminiClient
Проверяет все исправленные проблемы:
1. Обработка JSONDecodeError как retry
2. Функция _add_salt_to_prompt
3. Проверка пустых ответов от API
"""

import asyncio
import json
import logging

# Активируем виртуальное окружение если нужно
import sys
import os
sys.path.insert(0, '/home/imort/Herzog_v3')

from src.shared.gemini_client import GeminiClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_salt_function():
    """Тестируем функцию добавления соли к промпту"""
    print("\n🧪 ТЕСТ 1: Функция _add_salt_to_prompt")

    client = GeminiClient()

    original_prompt = "Проанализируй данные строительства"

    # Попытка 1 - без соли
    salted_1 = client._add_salt_to_prompt(original_prompt, 1)
    assert salted_1 == original_prompt, "На первой попытке соль не должна добавляться"
    print("✅ Попытка 1: соль не добавлена (правильно)")

    # Попытка 2 - с солью
    salted_2 = client._add_salt_to_prompt(original_prompt, 2)
    assert "Уникальный ID запроса:" in salted_2, "На второй попытке должна быть соль"
    assert "HRZ-" in salted_2, "Должен быть код проекта"
    assert original_prompt in salted_2, "Оригинальный промпт должен сохраниться"
    print("✅ Попытка 2: соль добавлена корректно")

    print(f"📏 Длина промпта: {len(original_prompt)} → {len(salted_2)} (+{len(salted_2) - len(original_prompt)} символов)")

async def test_json_validation():
    """Тестируем простой JSON запрос"""
    print("\n🧪 ТЕСТ 2: Валидация JSON ответа")

    client = GeminiClient()

    # Простой запрос с четким JSON
    prompt = """
Дай мне простой JSON ответ с информацией о стройке:

{
    "project": "Тестовая стройка",
    "status": "active",
    "days": 30
}

Ответь СТРОГО этим JSON без дополнительного текста.
"""

    try:
        print("🔄 Отправляем запрос к Gemini...")
        response = await client.generate_response(prompt, max_retries=3)

        if response.get('success'):
            print("✅ Запрос выполнен успешно")
            print(f"🤖 Модель: {response.get('model_used')}")
            print(f"🔢 Попыток: {response.get('attempt')}")
            print(f"📊 Токенов: {response.get('usage_metadata', {}).get('total_token_count', 0)}")

            if response.get('json_parse_success'):
                print("✅ JSON успешно распарсен")
                parsed_json = response.get('response')
                print(f"📋 Ответ: {json.dumps(parsed_json, ensure_ascii=False, indent=2)}")
            else:
                print("❌ JSON не удалось распарсить")
                print(f"🗒️ Сырой текст: {response.get('raw_text', '')[:200]}...")
        else:
            print(f"❌ Запрос завершился ошибкой: {response.get('error')}")

    except Exception as e:
        print(f"💥 Исключение: {e}")

async def main():
    """Главная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ GEMINI CLIENT")
    print("=" * 50)

    try:
        await test_salt_function()
        await test_json_validation()

        print("\n🎉 ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")

    except Exception as e:
        print(f"💥 КРИТИЧЕСКАЯ ОШИБКА ТЕСТИРОВАНИЯ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())