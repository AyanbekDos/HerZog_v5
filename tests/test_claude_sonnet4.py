#!/usr/bin/env python3
"""
Тест Claude Sonnet 4 через OpenRouter
Проверяем работу с реальной моделью Claude 4
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

async def test_claude_sonnet4():
    """Тест Claude Sonnet 4"""
    print("🧪 === ТЕСТ CLAUDE SONNET 4 ===")

    # Устанавливаем продакшн режим для использования Claude 4
    os.environ['CLAUDE_TEST_MODE'] = 'false'

    try:
        from src.shared.claude_client import ClaudeClient
        client = ClaudeClient()

        print(f"✅ ClaudeClient создан")
        print(f"🧪 Тестовый режим: {client.test_mode}")
        print(f"🎯 Модель: {client.model_name}")

        # Тест с минимальным промтом для проверки модели
        print("\n--- ТЕСТ: Claude Sonnet 4 простой запрос ---")
        simple_prompt = """
        Ответь кратко в JSON формате:
        {
            "model_test": "success",
            "model_name": "claude-sonnet-4"
        }
        """

        result = await client.generate_response(
            prompt=simple_prompt,
            agent_name="test_agent"
        )

        if result['success']:
            print("✅ Claude Sonnet 4 отвечает!")
            print(f"🤖 Модель: {result['model_used']}")
            print(f"📊 Токены: {result['usage_metadata']['total_token_count']}")
            print(f"💰 Стоимость: ~${result.get('estimated_cost', 0):.4f}")
            print(f"📝 Ответ: {result['response']}")

            # Показываем статистику
            stats = client.get_usage_stats()
            print(f"\n📈 === СТАТИСТИКА ===")
            print(f"Входные токены: {stats['total_input_tokens']}")
            print(f"Выходные токены: {stats['total_output_tokens']}")
            print(f"Общая стоимость: ~${stats['estimated_cost']:.4f}")

            return True
        else:
            print(f"❌ Ошибка: {result['error']}")
            return False

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    async def main():
        print("🚀 Тестируем Claude Sonnet 4...")

        success = await test_claude_sonnet4()

        if success:
            print("\n✅ CLAUDE SONNET 4 РАБОТАЕТ!")
        else:
            print("\n❌ CLAUDE SONNET 4 НЕ ДОСТУПЕН!")

    asyncio.run(main())