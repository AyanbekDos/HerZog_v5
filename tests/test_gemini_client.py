#!/usr/bin/env python3
"""
Тестирование обновленного Gemini клиента с retry логикой
"""

import asyncio
import sys
import os

# Добавляем путь к модулям Herzog
sys.path.append('/home/imort/Herzog_v3')

from src.shared.gemini_client import gemini_client

async def test_gemini_client():
    """Тестируем обновленный клиент Gemini"""
    
    print("🧪 Тестирование обновленного Gemini клиента...")
    print(f"📋 Модель: {gemini_client.model.model_name}")
    
    # Простой тестовый запрос
    test_prompt = '''
Ты - помощник для анализа строительных работ. Ответь в формате JSON:

{
    "test": "ok",
    "model": "gemini-1.5-pro",
    "message": "Тестирование прошло успешно!"
}

Данные для анализа:
- Укладка плитки: 100 м2
- Подготовка основания: 100 м2
'''

    try:
        # Тестируем обычный запрос
        print("\n🔄 Отправляем тестовый запрос...")
        result = await gemini_client.generate_response(test_prompt)
        
        if result['success']:
            print(f"✅ Запрос успешен!")
            print(f"📊 Токенов использовано: {result['usage_metadata']['total_token_count']}")
            print(f"🎯 Попытка: {result.get('attempt', 1)}")
            print(f"📄 JSON парсинг: {'успешен' if result['json_parse_success'] else 'неуспешен'}")
            
            if result['json_parse_success']:
                response = result['response']
                print(f"💬 Ответ модели: {response.get('message', 'нет сообщения')}")
            else:
                print(f"💬 Сырой ответ: {result['raw_text'][:200]}...")
                
        else:
            print(f"❌ Запрос неуспешен: {result['error']}")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gemini_client())