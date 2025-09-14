#!/usr/bin/env python3
"""
Скрипт для создания снапшота проекта Herzog v3.0
Собирает все .py файлы и важные конфигурационные файлы в один текстовый файл
для анализа в стороннем ЛЛМ
"""

import os
from pathlib import Path
from datetime import datetime


def create_project_snapshot(output_file="snapshot.txt"):
    """
    Создает снапшот проекта со всеми .py файлами и важными конфигурационными файлами
    """

    # Файлы и папки для включения
    include_extensions = ['.py', '.txt', '.md', '.json', '.env.example']
    include_files = ['CLAUDE.md', 'requirements.txt', '.env.example', 'README.md']

    # Папки для исключения
    exclude_dirs = {
        '__pycache__',
        '.git',
        'venv',
        'env',
        '.venv',
        'node_modules',
        'projects',  # Рабочие директории проектов
        '.pytest_cache'
    }

    project_root = Path.cwd()

    with open(output_file, 'w', encoding='utf-8') as snapshot:
        # Заголовок снапшота
        snapshot.write(f"# СНАПШОТ ПРОЕКТА HERZOG V3.0\n")
        snapshot.write(f"# Дата создания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        snapshot.write(f"# Корневая директория: {project_root}\n")
        snapshot.write("=" * 80 + "\n\n")

        # Структура проекта
        snapshot.write("## СТРУКТУРА ПРОЕКТА\n\n")
        for root, dirs, files in os.walk(project_root):
            # Исключаем ненужные директории
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            level = root.replace(str(project_root), '').count(os.sep)
            indent = '  ' * level

            if level == 0:
                snapshot.write(f"{os.path.basename(root)}/\n")
            else:
                snapshot.write(f"{indent}{os.path.basename(root)}/\n")

            # Показываем только важные файлы в структуре
            sub_indent = '  ' * (level + 1)
            for file in files:
                if (any(file.endswith(ext) for ext in include_extensions) or
                    file in include_files):
                    snapshot.write(f"{sub_indent}{file}\n")

        snapshot.write("\n" + "=" * 80 + "\n\n")

        # Содержимое файлов
        file_count = 0

        for root, dirs, files in os.walk(project_root):
            # Исключаем ненужные директории
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in sorted(files):
                file_path = Path(root) / file
                relative_path = file_path.relative_to(project_root)

                # Проверяем, нужно ли включать этот файл
                should_include = False

                # Включаем .py файлы
                if file.endswith('.py'):
                    should_include = True

                # Включаем конкретные важные файлы
                elif file in include_files:
                    should_include = True

                # Включаем файлы промптов
                elif file.endswith('.txt') and 'prompt' in file.lower():
                    should_include = True

                if should_include:
                    try:
                        snapshot.write(f"## ФАЙЛ: {relative_path}\n")
                        snapshot.write("-" * 60 + "\n")

                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            snapshot.write(content)

                        snapshot.write("\n\n" + "=" * 80 + "\n\n")
                        file_count += 1

                    except Exception as e:
                        snapshot.write(f"ОШИБКА ЧТЕНИЯ ФАЙЛА: {e}\n\n")

        # Статистика
        snapshot.write("## СТАТИСТИКА СНАПШОТА\n")
        snapshot.write(f"Всего файлов включено: {file_count}\n")
        snapshot.write(f"Дата создания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    print(f"✅ Снапшот проекта создан: {output_file}")
    print(f"📁 Включено файлов: {file_count}")
    return output_file


if __name__ == "__main__":
    # Создаем снапшот
    snapshot_file = create_project_snapshot()

    # Показываем размер файла
    size_mb = os.path.getsize(snapshot_file) / (1024 * 1024)
    print(f"📊 Размер снапшота: {size_mb:.2f} МБ")