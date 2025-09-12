#!/usr/bin/env python3
"""
Тестирование системы с разными моделями для разных агентов
"""

import asyncio
import sys
import os

# Добавляем путь к модулям Herzog
sys.path.append('/home/imort/Herzog_v3')

from src.shared.gemini_client import gemini_client

async def test_multi_model_system():
    """Тестируем систему с разными моделями для каждого агента"""
    
    print("🧪 Тестирование мультимодельной системы Gemini...")
    print(f"📋 Доступные модели для агентов:")
    for agent, model in gemini_client.agent_models.items():
        print(f"   {agent}: {model}")
    
    print()
    
    # Тестовый промт
    test_prompt = '''
{
    "test": "multi_model",
    "agent": "current_agent",
    "message": "Модель работает корректно!"
}
'''

    # Тестируем каждого агента
    agents_to_test = ['work_packager', 'works_to_packages', 'counter', 'scheduler_and_staffer']
    
    for agent_name in agents_to_test:
        try:
            print(f"🔄 Тестируем агента: {agent_name}")
            
            result = await gemini_client.generate_response(
                test_prompt, 
                agent_name=agent_name
            )
            
            if result['success']:
                model_used = result.get('model_used', 'unknown')
                tokens = result['usage_metadata']['total_token_count']
                attempt = result.get('attempt', 1)
                
                print(f"   ✅ Успех: {model_used} | Токенов: {tokens} | Попытка: {attempt}")
                
                if result['json_parse_success']:
                    response = result['response']
                    print(f"   💬 Ответ: {response.get('message', 'нет сообщения')}")
                else:
                    print(f"   ⚠️  JSON не парсится, сырой ответ: {result['raw_text'][:100]}...")
            else:
                print(f"   ❌ Ошибка: {result['error']}")
                
        except Exception as e:
            print(f"   💥 Исключение: {e}")
        
        print()
    
    # Тестируем дефолтный вызов (без агента)
    print("🔄 Тестируем дефолтный вызов (без указания агента)...")
    try:
        result = await gemini_client.generate_response(test_prompt)
        
        if result['success']:
            model_used = result.get('model_used', 'unknown')
            tokens = result['usage_metadata']['total_token_count']
            
            print(f"   ✅ Успех: {model_used} | Токенов: {tokens}")
        else:
            print(f"   ❌ Ошибка: {result['error']}")
            
    except Exception as e:
        print(f"   💥 Исключение: {e}")
    
    print("\n🎯 Тестирование мультимодельной системы завершено!")

if __name__ == "__main__":
    asyncio.run(test_multi_model_system())