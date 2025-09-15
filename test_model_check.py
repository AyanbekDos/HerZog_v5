#!/usr/bin/env python3
"""
Проверяем какие модели доступны через OpenRouter
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def check_available_models():
    """Проверяем доступные модели Claude через OpenRouter"""
    print("🔍 === ПРОВЕРКА ДОСТУПНЫХ МОДЕЛЕЙ CLAUDE ===")

    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY не найден")
        return

    # Список моделей Claude для проверки
    models_to_test = [
        'anthropic/claude-sonnet-4',
        'anthropic/claude-3.5-sonnet-20241022',
        'anthropic/claude-3-5-sonnet-20241022',  # альтернативное название
        'anthropic/claude-3.5-sonnet'
    ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/imort/Herzog_v3",
        "X-Title": "Herzog Model Test"
    }

    base_url = "https://openrouter.ai/api/v1/chat/completions"

    for model in models_to_test:
        print(f"\n🧪 Тестируем модель: {model}")

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Ответь одним словом: 'работаю'"}],
            "max_tokens": 50,
            "temperature": 0.1
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(base_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                        usage = data.get('usage', {})

                        print(f"  ✅ РАБОТАЕТ")
                        print(f"  📝 Ответ: {content.strip()}")
                        print(f"  📊 Токены: {usage.get('total_tokens', 'N/A')}")

                        # Попробуем определить реальную модель по ответу
                        payload2 = {
                            "model": model,
                            "messages": [{"role": "user", "content": "Напиши свое имя и версию модели в JSON: {'name': 'your-name', 'version': 'your-version'}"}],
                            "max_tokens": 100,
                            "temperature": 0.1
                        }

                        async with session.post(base_url, json=payload2, headers=headers) as response2:
                            if response2.status == 200:
                                data2 = await response2.json()
                                content2 = data2.get('choices', [{}])[0].get('message', {}).get('content', '')
                                print(f"  🔍 Самоидентификация: {content2.strip()[:100]}")

                    elif response.status == 400:
                        data = await response.json()
                        error = data.get('error', {}).get('message', 'Unknown error')
                        print(f"  ❌ НЕ ПОДДЕРЖИВАЕТСЯ: {error}")

                    elif response.status == 429:
                        print(f"  ⏰ RATE LIMIT")

                    else:
                        print(f"  ❓ HTTP {response.status}")
                        data = await response.json()
                        print(f"     {data}")

        except Exception as e:
            print(f"  💥 ОШИБКА: {e}")

    print(f"\n✅ Проверка завершена!")

if __name__ == "__main__":
    asyncio.run(check_available_models())