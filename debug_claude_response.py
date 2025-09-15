#!/usr/bin/env python3
"""
Отладочный скрипт для понимания что именно возвращает Claude
"""

import asyncio
import json
import logging
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

async def debug_claude_response():
    """Смотрим что именно возвращает Claude"""
    print("🔍 === ОТЛАДКА ОТВЕТА CLAUDE ===")

    # Тестовый режим
    os.environ['CLAUDE_TEST_MODE'] = 'true'

    try:
        from src.shared.claude_client import ClaudeClient
        client = ClaudeClient()

        # Очень простой промт для JSON ответа
        simple_prompt = """
        Ответь ТОЛЬКО в JSON формате, без дополнительного текста:
        {
            "test": "success",
            "packages": [
                {
                    "name": "Test Package",
                    "items": ["item1", "item2"]
                }
            ]
        }
        """

        print("🔄 Отправляем простой JSON промт...")

        result = await client.generate_response(
            prompt=simple_prompt,
            agent_name="test_agent"
        )

        print(f"\n📊 Успех: {result['success']}")
        print(f"📊 Токены: {result.get('usage_metadata', {}).get('total_token_count', 'N/A')}")

        if 'raw_text' in result:
            print(f"\n📋 ===== ПОЛНЫЙ СЫРОЙ ОТВЕТ =====")
            print(f"Длина: {len(result['raw_text'])} символов")
            print("--- НАЧАЛО ---")
            print(result['raw_text'])
            print("--- КОНЕЦ ---")

            # Проверим на markdown
            raw = result['raw_text']
            if "```" in raw:
                print(f"\n🔍 Найден markdown блок!")

            # Попробуем разные способы очистки
            print(f"\n🧹 === ПОПЫТКИ ОЧИСТКИ ===")

            # Способ 1: Удаляем всё до первой {
            first_brace = raw.find('{')
            if first_brace != -1:
                cleaned1 = raw[first_brace:]
                last_brace = cleaned1.rfind('}')
                if last_brace != -1:
                    cleaned1 = cleaned1[:last_brace+1]
                print(f"Способ 1 (до первой {{): {cleaned1[:100]}...")

                try:
                    test_json = json.loads(cleaned1)
                    print(f"✅ Способ 1 сработал!")
                    print(f"Результат: {test_json}")
                except Exception as e:
                    print(f"❌ Способ 1 не сработал: {e}")

        else:
            print("❌ Нет raw_text в ответе")

        # Тест с системной инструкцией
        print(f"\n🔄 === ТЕСТ С СИСТЕМНОЙ ИНСТРУКЦИЕЙ ===")

        system_instruction = """
        Ты ДОЛЖЕН отвечать ТОЛЬКО в формате JSON.
        НИКАКОГО дополнительного текста, объяснений или комментариев.
        Только валидный JSON.
        """

        result2 = await client.generate_response(
            prompt="Создай простой JSON с полем 'status': 'ok'",
            agent_name="test_agent",
            system_instruction=system_instruction
        )

        if 'raw_text' in result2:
            print(f"\n📋 ===== ОТВЕТ С СИСТЕМНОЙ ИНСТРУКЦИЕЙ =====")
            print("--- НАЧАЛО ---")
            print(result2['raw_text'])
            print("--- КОНЕЦ ---")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_claude_response())