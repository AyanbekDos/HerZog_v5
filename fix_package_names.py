#!/usr/bin/env python3
"""
Быстрое исправление имен пакетов в true.json из промежуточных файлов
"""

import os
import json
import sys

def fix_package_names(project_path: str):
    """Исправляет имена пакетов в true.json"""

    # Читаем имена из work_packager
    work_packager_response = os.path.join(project_path, "4_work_packager", "llm_response.json")
    if not os.path.exists(work_packager_response):
        print(f"❌ Не найден {work_packager_response}")
        return False

    with open(work_packager_response, 'r', encoding='utf-8') as f:
        packager_data = json.load(f)

    packages_with_names = packager_data.get('response', {}).get('work_packages', [])
    if not packages_with_names:
        print("❌ Не найдены пакеты с именами")
        return False

    # Создаем словарь имен по package_id
    names_dict = {}
    for pkg in packages_with_names:
        package_id = pkg.get('package_id')
        name = pkg.get('name')
        description = pkg.get('description')
        if package_id and name:
            names_dict[package_id] = {
                'name': name,
                'description': description
            }

    print(f"✅ Найдено {len(names_dict)} пакетов с именами")

    # Читаем true.json
    truth_path = os.path.join(project_path, "true.json")
    if not os.path.exists(truth_path):
        print(f"❌ Не найден {truth_path}")
        return False

    with open(truth_path, 'r', encoding='utf-8') as f:
        truth_data = json.load(f)

    # Обновляем имена в work_packages
    work_packages = truth_data.get('results', {}).get('work_packages', [])
    if not work_packages:
        print("❌ Не найдены work_packages в true.json")
        return False

    updated_count = 0
    for package in work_packages:
        package_id = package.get('package_id')
        if package_id in names_dict:
            package['name'] = names_dict[package_id]['name']
            package['description'] = names_dict[package_id]['description']
            updated_count += 1
            print(f"✅ Обновлен {package_id}: {names_dict[package_id]['name']}")

    # Сохраняем обновленный true.json
    with open(truth_path, 'w', encoding='utf-8') as f:
        json.dump(truth_data, f, ensure_ascii=False, indent=2)

    print(f"🎉 Обновлено {updated_count} пакетов в {truth_path}")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        # Автоматически найдем последний проект
        project_path = "/home/imort/Herzog_v3/projects/34975055/f77f33ea"

    if os.path.exists(project_path):
        print(f"🔧 Исправляю имена пакетов в {project_path}")
        success = fix_package_names(project_path)
        if success:
            print("✅ Имена пакетов исправлены!")
        else:
            print("❌ Не удалось исправить имена пакетов")
    else:
        print(f"❌ Проект не найден: {project_path}")