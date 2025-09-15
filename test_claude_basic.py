#!/usr/bin/env python3
"""
Базовый тест Claude API через OpenRouter
Проверяет подключение и базовую функциональность с минимальными токенами
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

async def test_claude_basic():
    """Базовый тест Claude API"""
    print("🧪 === ТЕСТ CLAUDE API ЧЕРЕЗ OPENROUTER ===")

    # Проверяем наличие API ключа
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY не найден в .env файле!")
        return False

    print(f"✅ API ключ найден: {api_key[:10]}...")

    try:
        # Импортируем и создаем клиент
        from src.shared.claude_client import ClaudeClient
        client = ClaudeClient()

        print(f"✅ ClaudeClient создан")
        print(f"🧪 Тестовый режим: {client.test_mode}")
        print(f"🎯 Модель по умолчанию: {client.model_name}")

        # Тест 1: Простой запрос без системной инструкции
        print("\n--- ТЕСТ 1: Простой запрос ---")
        simple_prompt = """
        Ответь в JSON формате:
        {
            "status": "success",
            "message": "Привет от Claude!",
            "test_number": 1
        }
        """

        result = await client.generate_response(
            prompt=simple_prompt,
            agent_name="test_agent"
        )

        if result['success']:
            print("✅ Простой запрос прошел успешно")
            print(f"📊 Токены: {result['usage_metadata']['total_token_count']}")
            print(f"💰 Стоимость: ~${result.get('estimated_cost', 0):.4f}")
            print(f"📝 Ответ: {result['response']}")
        else:
            print(f"❌ Ошибка простого запроса: {result['error']}")
            return False

        # Тест 2: Запрос с системной инструкцией
        print("\n--- ТЕСТ 2: Запрос с системной инструкцией ---")
        system_instruction = """
        Ты эксперт по строительству. Всегда отвечай в формате JSON.
        Будь краток и четок.
        """

        prompt_with_system = """
        Классифицируй эту строительную работу в JSON формате:
        "Демонтаж кирпичной стены толщиной 120мм"

        Формат ответа:
        {
            "category": "demolition",
            "type": "wall",
            "material": "brick",
            "complexity": "medium"
        }
        """

        result2 = await client.generate_response(
            prompt=prompt_with_system,
            agent_name="classifier",
            system_instruction=system_instruction
        )

        if result2['success']:
            print("✅ Запрос с системной инструкцией прошел успешно")
            print(f"📊 Токены: {result2['usage_metadata']['total_token_count']}")
            print(f"💰 Стоимость: ~${result2.get('estimated_cost', 0):.4f}")
            print(f"📝 Ответ: {result2['response']}")
        else:
            print(f"❌ Ошибка запроса с системной инструкцией: {result2['error']}")
            return False

        # Показываем общую статистику
        stats = client.get_usage_stats()
        print(f"\n📈 === ОБЩАЯ СТАТИСТИКА ТЕСТОВ ===")
        print(f"Всего запросов: {stats['total_requests']}")
        print(f"Входные токены: {stats['total_input_tokens']}")
        print(f"Выходные токены: {stats['total_output_tokens']}")
        print(f"Общая стоимость: ~${stats['estimated_cost']:.4f}")

        return True

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_error_handling():
    """Тест обработки ошибок"""
    print("\n🧪 === ТЕСТ ОБРАБОТКИ ОШИБОК ===")

    try:
        from src.shared.claude_client import ClaudeClient
        client = ClaudeClient()

        # Тест некорректного JSON
        print("\n--- ТЕСТ: Некорректный JSON промт ---")
        bad_json_prompt = """
        Ответь просто текстом, а не JSON:
        Привет, это не JSON ответ!
        """

        result = await client.generate_response(
            prompt=bad_json_prompt,
            agent_name="test_agent",
            max_retries=2  # Меньше ретраев для экономии
        )

        print(f"Результат обработки некорректного JSON: {result['success']}")
        if not result['success']:
            print(f"Ошибка (ожидаемо): {result['error']}")

    except Exception as e:
        print(f"❌ Ошибка в тесте обработки ошибок: {e}")

if __name__ == "__main__":
    async def main():
        print("🚀 Запуск тестов Claude API...")

        # Устанавливаем тестовый режим принудительно
        os.environ['CLAUDE_TEST_MODE'] = 'true'

        success = await test_claude_basic()

        if success:
            print("\n✅ ВСЕ БАЗОВЫЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
            await test_error_handling()
        else:
            print("\n❌ БАЗОВЫЕ ТЕСТЫ НЕ ПРОШЛИ!")
            return

        print("\n🎯 Готово! Claude API работает корректно.")
        print("💡 Можно переходить к тестированию агентов.")

    asyncio.run(main())