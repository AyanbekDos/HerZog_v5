#!/usr/bin/env python3
"""
Скрипт для миграции всех агентов с Gemini на Claude
Создаёт резервные копии и заменяет import в агентах
"""

import os
import shutil
import logging
from typing import List
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Файлы для миграции
AGENT_FILES = [
    'src/ai_agents/work_packager.py',
    'src/ai_agents/works_to_packages.py',
    'src/ai_agents/counter.py',
    'src/ai_agents/scheduler_and_staffer.py',
    'src/data_processing/gemini_classifier.py'
]

# Паттерн замены
OLD_IMPORT = "from ..shared.gemini_client import gemini_client"
NEW_IMPORT = "from ..shared.claude_client import claude_client as gemini_client  # Migrated to Claude"

OLD_IMPORT_CLASSIFIER = "from ..shared.gemini_client import gemini_client"
NEW_IMPORT_CLASSIFIER = "from ..shared.claude_client import claude_client as gemini_client  # Migrated to Claude"

def create_backup(file_path: str) -> str:
    """Создаёт резервную копию файла"""
    backup_path = f"{file_path}.gemini_backup"

    if os.path.exists(backup_path):
        logger.info(f"📋 Backup уже существует: {backup_path}")
        return backup_path

    shutil.copy2(file_path, backup_path)
    logger.info(f"💾 Создан backup: {backup_path}")
    return backup_path

def migrate_agent_file(file_path: str) -> bool:
    """Мигрирует один файл агента"""
    if not os.path.exists(file_path):
        logger.warning(f"⚠️  Файл не найден: {file_path}")
        return False

    # Создаём backup
    backup_path = create_backup(file_path)

    try:
        # Читаем файл
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Ищем и заменяем import
        old_content = content

        # Замена для обычных агентов
        if OLD_IMPORT in content:
            content = content.replace(OLD_IMPORT, NEW_IMPORT)
            logger.info(f"✅ Заменён import в {file_path}")

        # Замена для classifier (может иметь другой путь)
        elif "from ..shared.gemini_client import gemini_client" in content:
            content = content.replace("from ..shared.gemini_client import gemini_client", NEW_IMPORT_CLASSIFIER)
            logger.info(f"✅ Заменён import classifier в {file_path}")

        elif "from src.shared.gemini_client import gemini_client" in content:
            content = content.replace("from src.shared.gemini_client import gemini_client",
                                     "from src.shared.claude_client import claude_client as gemini_client  # Migrated to Claude")
            logger.info(f"✅ Заменён абсолютный import в {file_path}")

        else:
            logger.info(f"ℹ️  Никаких замен в {file_path} не требуется")
            return True

        # Записываем изменённый файл
        if content != old_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"💾 Файл обновлён: {file_path}")

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка при миграции {file_path}: {e}")
        # Восстанавливаем из backup
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
            logger.info(f"🔄 Восстановлен из backup: {file_path}")
        return False

def update_env_file():
    """Добавляет настройки Claude в .env если нужно"""
    env_path = ".env"

    if not os.path.exists(env_path):
        logger.warning("⚠️  .env файл не найден")
        return

    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Добавляем настройку тестового режима если её нет
    if "CLAUDE_TEST_MODE" not in content:
        with open(env_path, 'a', encoding='utf-8') as f:
            f.write("\n# Claude API Settings\n")
            f.write("CLAUDE_TEST_MODE=true  # Set to 'false' for production (Sonnet 4)\n")
        logger.info("✅ Добавлены настройки Claude в .env")
    else:
        logger.info("ℹ️  Настройки Claude уже есть в .env")

def create_migration_report() -> str:
    """Создаёт отчёт о миграции"""
    report = []
    report.append("# Отчёт о миграции на Claude API")
    report.append(f"Дата: {os.popen('date').read().strip()}")
    report.append("")
    report.append("## Мигрированные файлы:")

    for file_path in AGENT_FILES:
        if os.path.exists(file_path):
            backup_path = f"{file_path}.gemini_backup"
            status = "✅ Мигрирован" if os.path.exists(backup_path) else "❌ НЕ мигрирован"
            report.append(f"- {file_path} - {status}")

    report.append("")
    report.append("## Как откатить изменения:")
    report.append("```bash")
    for file_path in AGENT_FILES:
        backup_path = f"{file_path}.gemini_backup"
        if os.path.exists(backup_path):
            report.append(f"cp {backup_path} {file_path}")
    report.append("```")

    report.append("")
    report.append("## Настройки:")
    report.append("- CLAUDE_TEST_MODE=true (Claude 3.5 Sonnet, дешевле)")
    report.append("- CLAUDE_TEST_MODE=false (Claude Sonnet 4, дороже)")

    report_text = "\n".join(report)

    with open("claude_migration_report.md", 'w', encoding='utf-8') as f:
        f.write(report_text)

    return report_text

def main():
    """Основная функция миграции"""
    print("🚀 === МИГРАЦИЯ НА CLAUDE API ===")
    print("Этот скрипт заменит Gemini на Claude во всех агентах")
    print("")

    # Подтверждение
    answer = input("Продолжить? (y/N): ").strip().lower()
    if answer not in ['y', 'yes', 'да']:
        print("❌ Миграция отменена")
        return

    print("\n🔄 Начинаем миграцию...")

    # Мигрируем файлы
    success_count = 0
    for file_path in AGENT_FILES:
        print(f"\n📂 Обрабатываем: {file_path}")
        if migrate_agent_file(file_path):
            success_count += 1

    # Обновляем .env
    print(f"\n📝 Обновляем настройки...")
    update_env_file()

    # Создаём отчёт
    print(f"\n📊 Создаём отчёт...")
    report = create_migration_report()

    print(f"\n🎯 === МИГРАЦИЯ ЗАВЕРШЕНА ===")
    print(f"✅ Успешно мигрировано: {success_count}/{len(AGENT_FILES)} файлов")
    print(f"📋 Отчёт сохранён: claude_migration_report.md")

    if success_count == len(AGENT_FILES):
        print("")
        print("🧪 Для тестирования запустите:")
        print("  python test_claude_agent.py")
        print("")
        print("🏭 Для продакшена установите:")
        print("  CLAUDE_TEST_MODE=false в .env")

    else:
        print("")
        print("⚠️  Не все файлы мигрированы. Проверьте логи выше.")

    print(f"\n💾 Backup файлы сохранены с расширением .gemini_backup")

if __name__ == "__main__":
    main()