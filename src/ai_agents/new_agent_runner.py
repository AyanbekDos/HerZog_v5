"""
Новый runner для агентов HerZog v3.0
Запускает новые агенты: work_packager, works_to_packages, counter, scheduler_and_staffer
"""

import json
import logging
import os
import asyncio
from typing import Dict, Any, Optional

# Импорт наших новых агентов
from .work_packager import run_work_packager
from .works_to_packages import run_works_to_packages
from .counter import run_counter
from .scheduler_and_staffer import run_scheduler_and_staffer

logger = logging.getLogger(__name__)

# Конфигурация новых агентов
NEW_AGENTS = {
    "work_packager": {
        "name": "Архитектор - создание пакетов работ",
        "function": run_work_packager,
        "description": "Создает укрупненные пакеты работ из детализированных работ"
    },
    "works_to_packages": {
        "name": "Распределитель - назначение работ к пакетам", 
        "function": run_works_to_packages,
        "description": "Распределяет каждую работу по соответствующим пакетам"
    },
    "counter": {
        "name": "Сметчик - расчет объемов",
        "function": run_counter,
        "description": "Рассчитывает интеллектуальные объемы для пакетов работ"
    },
    "scheduler_and_staffer": {
        "name": "Супер-планировщик - календарный план",
        "function": run_scheduler_and_staffer,
        "description": "Создает календарный план с распределением персонала"
    }
}

async def run_new_agent(agent_name: str, project_path: str) -> Dict[str, Any]:
    """
    Запускает один из новых агентов
    
    Args:
        agent_name: Имя агента (work_packager, works_to_packages, counter, scheduler_and_staffer)
        project_path: Путь к проекту
        
    Returns:
        Результат выполнения агента
    """
    
    if agent_name not in NEW_AGENTS:
        return {
            'success': False,
            'error': f"Неизвестный агент: {agent_name}",
            'available_agents': list(NEW_AGENTS.keys())
        }
    
    agent_config = NEW_AGENTS[agent_name]
    
    logger.info(f"🤖 Запуск агента: {agent_config['name']}")
    logger.info(f"📝 {agent_config['description']}")
    
    try:
        # Запускаем агента
        result = await agent_config['function'](project_path)
        
        if result.get('success'):
            logger.info(f"✅ Агент {agent_name} завершен успешно")
        else:
            logger.error(f"❌ Агент {agent_name} завершился с ошибкой: {result.get('error')}")
        
        return result
        
    except Exception as e:
        error_result = {
            'success': False,
            'error': str(e),
            'agent': agent_name
        }
        logger.error(f"💥 Исключение в агенте {agent_name}: {e}")
        return error_result

async def run_new_pipeline(project_path: str, start_from: str = "work_packager") -> Dict[str, Any]:
    """
    Запускает полный пайплайн новых агентов
    
    Args:
        project_path: Путь к проекту
        start_from: С какого агента начать
        
    Returns:
        Общий результат пайплайна
    """
    
    # Последовательность агентов
    pipeline_sequence = [
        "work_packager",
        "works_to_packages", 
        "counter",
        "scheduler_and_staffer"
    ]
    
    # Определяем с какого агента начинать
    try:
        start_index = pipeline_sequence.index(start_from)
        agents_to_run = pipeline_sequence[start_index:]
    except ValueError:
        return {
            'success': False,
            'error': f"Неизвестный стартовый агент: {start_from}",
            'available_agents': pipeline_sequence
        }
    
    logger.info(f"🏗️ Запуск нового пайплайна HerZog v3.0")
    logger.info(f"📂 Проект: {project_path}")
    logger.info(f"🎯 Агенты: {' → '.join(agents_to_run)}")
    
    pipeline_result = {
        'success': False,
        'project_path': project_path,
        'agents_completed': [],
        'agents_failed': [],
        'start_from': start_from,
        'total_agents': len(agents_to_run),
        'results': {}
    }
    
    # Запускаем агентов последовательно
    for agent_name in agents_to_run:
        logger.info(f"\n{'='*50}")
        logger.info(f"🚀 ЭТАП: {agent_name.upper()}")
        logger.info(f"{'='*50}")
        
        agent_result = await run_new_agent(agent_name, project_path)
        pipeline_result['results'][agent_name] = agent_result
        
        if agent_result.get('success'):
            pipeline_result['agents_completed'].append(agent_name)
            logger.info(f"✅ Этап {agent_name} завершен успешно")
        else:
            pipeline_result['agents_failed'].append(agent_name)
            logger.error(f"❌ Этап {agent_name} провален: {agent_result.get('error')}")
            
            # Прерываем пайплайн при ошибке
            pipeline_result['error'] = f"Пайплайн остановлен на этапе {agent_name}: {agent_result.get('error')}"
            return pipeline_result
    
    # Если дошли сюда - все агенты выполнены успешно
    pipeline_result['success'] = True
    logger.info(f"\n🎉 ПАЙПЛАЙН ЗАВЕРШЕН УСПЕШНО!")
    logger.info(f"✅ Выполнено агентов: {len(pipeline_result['agents_completed'])}")
    
    return pipeline_result

def run_new_agent_sync(agent_name: str, project_path: str) -> bool:
    """
    Синхронная обертка для запуска агента (для совместимости со старым кодом)
    
    Args:
        agent_name: Имя агента
        project_path: Путь к проекту
        
    Returns:
        True если агент выполнен успешно
    """
    try:
        result = asyncio.run(run_new_agent(agent_name, project_path))
        return result.get('success', False)
    except Exception as e:
        logger.error(f"Ошибка в синхронной обертке для {agent_name}: {e}")
        return False

def get_new_agent_info(agent_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Возвращает информацию о новых агентах
    
    Args:
        agent_name: Имя конкретного агента или None для всех
        
    Returns:
        Информация об агенте(ах)
    """
    if agent_name:
        if agent_name in NEW_AGENTS:
            return NEW_AGENTS[agent_name]
        else:
            return {'error': f'Агент {agent_name} не найден'}
    else:
        return NEW_AGENTS

if __name__ == "__main__":
    # Тестирование нового runner'а
    import sys
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) >= 3:
        # Запуск конкретного агента: python new_agent_runner.py work_packager /path/to/project
        agent_name = sys.argv[1]
        project_path = sys.argv[2]
        
        print(f"🧪 Тестирование агента: {agent_name}")
        print(f"📂 Проект: {project_path}")
        
        result = asyncio.run(run_new_agent(agent_name, project_path))
        print(f"📊 Результат: {result}")
        
    elif len(sys.argv) == 2:
        # Запуск полного пайплайна: python new_agent_runner.py /path/to/project  
        project_path = sys.argv[1]
        
        print(f"🧪 Тестирование полного пайплайна")
        print(f"📂 Проект: {project_path}")
        
        result = asyncio.run(run_new_pipeline(project_path))
        print(f"📊 Результат: {result}")
        
    else:
        # Показать информацию о доступных агентах
        print("🤖 Новые агенты HerZog v3.0:")
        print("=" * 50)
        
        for agent_name, config in NEW_AGENTS.items():
            print(f"📦 {agent_name}:")
            print(f"   Название: {config['name']}")
            print(f"   Описание: {config['description']}")
            print()
        
        print("💡 Использование:")
        print("   python new_agent_runner.py work_packager /path/to/project  # один агент")
        print("   python new_agent_runner.py /path/to/project               # весь пайплайн")