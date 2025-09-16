#!/usr/bin/env python3
"""
Скрипт для создания снапшота проекта Herzog v3.0
Собирает все .py файлы и важные конфигурационные файлы в один текстовый файл
для анализа в стороннем ЛЛМ
Автоматически исключает файлы из .gitignore
"""

import os
import fnmatch
from pathlib import Path
from datetime import datetime


def load_gitignore_patterns(project_root):
    """Загружает паттерны из .gitignore"""
    gitignore_path = project_root / '.gitignore'
    patterns = []

    if gitignore_path.exists():
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Преобразуем gitignore паттерны в fnmatch паттерны
                    if line.endswith('/'):
                        patterns.append(line[:-1])  # Директории
                    patterns.append(line)

                    # Добавляем паттерны для поддиректорий
                    if not line.startswith('**/'):
                        patterns.append(f"**/{line}")
                        if line.endswith('/'):
                            patterns.append(f"**/{line[:-1]}")

    return patterns


def should_ignore_path(path, project_root, ignore_patterns):
    """Проверяет, нужно ли игнорировать путь согласно .gitignore"""
    relative_path = path.relative_to(project_root)

    for pattern in ignore_patterns:
        # Проверяем полный путь
        if fnmatch.fnmatch(str(relative_path), pattern):
            return True
        # Проверяем имя файла/директории
        if fnmatch.fnmatch(relative_path.name, pattern):
            return True
        # Проверяем любую часть пути
        path_parts = str(relative_path).split(os.sep)
        for part in path_parts:
            if fnmatch.fnmatch(part, pattern):
                return True

    return False


def create_project_snapshot(output_file="snapshot.txt"):
    """
    Создает снапшот проекта со всеми .py файлами и важными конфигурационными файлами
    Автоматически исключает файлы из .gitignore
    """

    project_root = Path.cwd()

    # Загружаем паттерны игнорирования из .gitignore
    ignore_patterns = load_gitignore_patterns(project_root)
    print(f"📋 Загружено {len(ignore_patterns)} паттернов из .gitignore")

    # Файлы и папки для включения
    include_extensions = ['.py', '.txt', '.md', '.json', '.env.example']
    include_files = ['CLAUDE.md', 'requirements.txt', '.env.example', 'README.md']

    # Дополнительные исключения (в дополнение к .gitignore)
    force_exclude_dirs = {
        '.git',
        'node_modules'
    }

    with open(output_file, 'w', encoding='utf-8') as snapshot:
        # Заголовок снапшота
        snapshot.write(f"# СНАПШОТ ПРОЕКТА HERZOG V3.0\n")
        snapshot.write(f"# Дата создания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        snapshot.write(f"# Корневая директория: {project_root}\n")
        snapshot.write("=" * 80 + "\n\n")

        # Структура проекта
        snapshot.write("## СТРУКТУРА ПРОЕКТА\n\n")
        for root, dirs, files in os.walk(project_root):
            root_path = Path(root)

            # Исключаем директории согласно .gitignore и force_exclude_dirs
            dirs[:] = [
                d for d in dirs
                if d not in force_exclude_dirs and not should_ignore_path(root_path / d, project_root, ignore_patterns)
            ]

            level = root.replace(str(project_root), '').count(os.sep)
            indent = '  ' * level

            if level == 0:
                snapshot.write(f"{os.path.basename(root)}/\n")
            else:
                snapshot.write(f"{indent}{os.path.basename(root)}/\n")

            # Показываем только важные файлы в структуре (не игнорируемые)
            sub_indent = '  ' * (level + 1)
            for file in files:
                file_path = root_path / file
                if (not should_ignore_path(file_path, project_root, ignore_patterns) and
                    (any(file.endswith(ext) for ext in include_extensions) or
                     file in include_files)):
                    snapshot.write(f"{sub_indent}{file}\n")

        snapshot.write("\n" + "=" * 80 + "\n\n")

        # Содержимое файлов
        file_count = 0
        ignored_count = 0

        for root, dirs, files in os.walk(project_root):
            root_path = Path(root)

            # Исключаем директории согласно .gitignore и force_exclude_dirs
            dirs[:] = [
                d for d in dirs
                if d not in force_exclude_dirs and not should_ignore_path(root_path / d, project_root, ignore_patterns)
            ]

            for file in sorted(files):
                file_path = root_path / file
                relative_path = file_path.relative_to(project_root)

                # Сначала проверяем .gitignore
                if should_ignore_path(file_path, project_root, ignore_patterns):
                    ignored_count += 1
                    continue

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
        snapshot.write(f"Файлов проигнорировано: {ignored_count}\n")
        snapshot.write(f"Использованных .gitignore паттернов: {len(ignore_patterns)}\n")
        snapshot.write(f"Дата создания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    print(f"✅ Снапшот проекта создан: {output_file}")
    print(f"📁 Включено файлов: {file_count}")
    print(f"🚫 Проигнорировано файлов: {ignored_count}")
    print(f"📋 Использовано паттернов из .gitignore: {len(ignore_patterns)}")
    return output_file


if __name__ == "__main__":
    # Создаем снапшот
    snapshot_file = create_project_snapshot()

    # Показываем размер файла
    size_mb = os.path.getsize(snapshot_file) / (1024 * 1024)
    print(f"📊 Размер снапшота: {size_mb:.2f} МБ")