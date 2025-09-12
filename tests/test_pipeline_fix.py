#!/usr/bin/env python3

import asyncio
import os
from src.main_pipeline import HerzogPipeline

async def test_pipeline():
    project_path = 'projects/34975055/fdebae37'
    
    if not os.path.exists(project_path):
        print(f'❌ Проект не найден: {project_path}')
        return
    
    print(f'✅ Тестируем пайплайн для проекта: {project_path}')
    
    pipeline = HerzogPipeline(project_path)
    
    # Тестируем этап концептуализации (шаг 4)
    print('🎯 Запускаем этап концептуализации...')
    result = await pipeline.run_ai_agent(4)
    
    print('📊 Результат:')
    print(result)
    
    if result.get('success'):
        print('✅ Концептуализация завершена успешно!')
    else:
        print('❌ Ошибка в концептуализации:', result.get('error'))

if __name__ == '__main__':
    asyncio.run(test_pipeline())