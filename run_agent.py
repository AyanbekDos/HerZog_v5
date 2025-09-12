#!/usr/bin/env python3
"""
Скрипт для запуска агентов системы HerZog v3.0
"""

import sys
import os
import logging

# Добавляем путь к исходникам
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ai_agents.agent_runner import run_agent, run_pipeline

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    if len(sys.argv) < 3:
        print("Использование:")
        print("  python run_agent.py <путь_к_проекту> <имя_агента>")
        print("  python run_agent.py <путь_к_проекту> pipeline [start_from]")
        print()
        print("Примеры:")
        print("  python run_agent.py projects/34975055/94b9a7b6 2_strategist")
        print("  python run_agent.py projects/34975055/94b9a7b6 pipeline 2_strategist")
        return 1
    
    project_dir = sys.argv[1]
    command = sys.argv[2]
    
    if not os.path.exists(project_dir):
        print(f"❌ Проект не найден: {project_dir}")
        return 1
    
    if command == "pipeline":
        # Запуск всего пайплайна
        start_from = sys.argv[3] if len(sys.argv) > 3 else "1.1_group_creator"
        print(f"🏭 Запуск пайплайна для проекта {project_dir} с агента {start_from}")
        success = run_pipeline(project_dir, start_from)
        print(f"Результат: {'✅ Успех' if success else '❌ Ошибка'}")
        return 0 if success else 1
    
    else:
        # Запуск одного агента
        agent_name = command
        print(f"🤖 Запуск агента {agent_name} для проекта {project_dir}")
        success = run_agent(agent_name, project_dir)
        print(f"Результат: {'✅ Успех' if success else '❌ Ошибка'}")
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())