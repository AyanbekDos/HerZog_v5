#!/usr/bin/env python3
"""
Тест реального Claude Sonnet 4 с правильными названиями моделей
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def test_real_claude_sonnet4():
    """Тестируем все возможные названия Claude Sonnet 4"""
    print("🔍 === ТЕСТ РЕАЛЬНОГО CLAUDE SONNET 4 ===")

    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY не найден")
        return

    # Различные варианты названий для тестирования
    model_variants = [
        'anthropic/claude-sonnet-4',
        'openrouter:anthropic/claude-sonnet-4',
        'anthropic/claude-sonnet-4-20250514',
        'anthropic/claude-4-sonnet'
    ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/imort/Herzog_v3",
        "X-Title": "Herzog Sonnet 4 Test"
    }

    base_url = "https://openrouter.ai/api/v1/chat/completions"

    for model in model_variants:
        print(f"\n🧪 Тестируем: {model}")

        # Специальный промт для определения версии модели
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": "Ответь ТОЧНО в JSON формате: {'model_family': 'claude', 'version': 'твоя версия', 'capabilities': ['что ты умеешь'], 'is_sonnet_4': true/false}"
                }
            ],
            "max_tokens": 200,
            "temperature": 0.1
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(base_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                        usage = data.get('usage', {})

                        print(f"  ✅ РАБОТАЕТ!")
                        print(f"  📊 Токены: вход={usage.get('prompt_tokens', 'N/A')}, выход={usage.get('completion_tokens', 'N/A')}")
                        print(f"  💰 Общие токены: {usage.get('total_tokens', 'N/A')}")
                        print(f"  🤖 Ответ: {content.strip()[:200]}...")

                        # Вычисляем стоимость по новым ценам
                        input_tokens = usage.get('prompt_tokens', 0)
                        output_tokens = usage.get('completion_tokens', 0)

                        # Цены из поиска: input=$0.000003, output=$0.000015
                        input_cost = input_tokens * 0.000003
                        output_cost = output_tokens * 0.000015
                        total_cost = input_cost + output_cost

                        print(f"  💰 Стоимость: ~${total_cost:.6f} (вход: ${input_cost:.6f}, выход: ${output_cost:.6f})")

                    elif response.status == 400:
                        data = await response.json()
                        error = data.get('error', {}).get('message', 'Unknown error')
                        print(f"  ❌ НЕ ПОДДЕРЖИВАЕТСЯ: {error}")

                    elif response.status == 429:
                        print(f"  ⏰ RATE LIMIT")

                    else:
                        print(f"  ❓ HTTP {response.status}")

        except Exception as e:
            print(f"  💥 ОШИБКА: {e}")

    print(f"\n🎯 === РЕЗУЛЬТАТ ===")
    print("Если какая-то модель работает - это и есть настоящий Sonnet 4!")

async def test_with_real_task():
    """Тест с реальной задачей для сравнения качества"""
    print(f"\n🧠 === ТЕСТ КАЧЕСТВА МОДЕЛИ ===")

    # Берем лучшую рабочую модель
    model = 'anthropic/claude-sonnet-4'

    api_key = os.getenv('OPENROUTER_API_KEY')
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/imort/Herzog_v3",
        "X-Title": "Herzog Quality Test"
    }

    base_url = "https://openrouter.ai/api/v1/chat/completions"

    # Сложная задача группировки работ
    complex_prompt = """
Сгруппируй эти строительные работы в логические пакеты. Ответь в JSON:

Работы:
1. Демонтаж кирпичной перегородки 120мм - 45м²
2. Демонтаж гипсокартонной перегородки - 30м²
3. Штукатурка стен цементная - 150м²
4. Штукатурка стен гипсовая - 80м²
5. Грунтовка стен - 230м²
6. Покраска стен водоэмульсионная - 230м²
7. Устройство стяжки пола - 200м²
8. Укладка керамогранита - 200м²

Формат ответа:
{
  "packages": [
    {
      "name": "Название пакета",
      "category": "demolition/preparation/finishing/flooring",
      "works": ["список id работ"],
      "reasoning": "почему сгруппированы вместе"
    }
  ]
}
"""

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": complex_prompt}],
        "max_tokens": 1000,
        "temperature": 0.3
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(base_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                    usage = data.get('usage', {})

                    print(f"✅ Сложная задача выполнена!")
                    print(f"📊 Токены: {usage.get('total_tokens', 'N/A')}")
                    print(f"🧠 Ответ (первые 500 символов):")
                    print(content[:500] + "...")

                    # Проверяем качество JSON
                    try:
                        import json
                        # Извлекаем JSON из ответа
                        if "{" in content and "}" in content:
                            start = content.find("{")
                            end = content.rfind("}") + 1
                            json_part = content[start:end]
                            parsed = json.loads(json_part)
                            print(f"✅ JSON валидный, пакетов создано: {len(parsed.get('packages', []))}")
                        else:
                            print(f"⚠️  JSON не найден в ответе")
                    except Exception as e:
                        print(f"❌ JSON невалидный: {e}")

                else:
                    print(f"❌ Ошибка: HTTP {response.status}")

    except Exception as e:
        print(f"💥 Ошибка: {e}")

if __name__ == "__main__":
    async def main():
        await test_real_claude_sonnet4()
        await test_with_real_task()

    asyncio.run(main())