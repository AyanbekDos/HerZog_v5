#!/usr/bin/env python3
"""
Скрипт для проверки логических несостыковок в структуре true.json
"""

import json
import os
from pathlib import Path

def check_truth_structure(truth_path):
    """Проверяет truth.json на логические несостыковки"""

    print(f"🔍 Анализ структуры: {truth_path}")

    with open(truth_path, 'r', encoding='utf-8') as f:
        truth_data = json.load(f)

    issues = []
    results = truth_data.get('results', {})

    # Проверка 1: Наличие обязательных разделов
    required_sections = ['work_breakdown_structure', 'volume_calculations', 'scheduled_packages']
    for section in required_sections:
        if section not in results:
            issues.append(f"❌ Отсутствует раздел: {section}")
        else:
            count = len(results[section])
            print(f"✅ {section}: {count} элементов")

    # Проверка 2: Соответствие package ID между разделами
    work_breakdown_packages = [p['id'] for p in results.get('work_breakdown_structure', []) if p.get('type') == 'package']
    volume_calc_packages = [p['id'] for p in results.get('volume_calculations', []) if p.get('type') == 'package']
    scheduled_packages_ids = [p.get('package_id', p.get('id', 'unknown')) for p in results.get('scheduled_packages', [])]

    print(f"\n📦 Пакеты по разделам:")
    print(f"   work_breakdown_structure: {work_breakdown_packages}")
    print(f"   volume_calculations: {volume_calc_packages}")
    print(f"   scheduled_packages: {scheduled_packages_ids}")

    # Проверяем что все пакеты есть везде
    all_packages = set(work_breakdown_packages + volume_calc_packages + scheduled_packages_ids)
    for pkg_id in all_packages:
        if pkg_id not in work_breakdown_packages:
            issues.append(f"❌ Пакет {pkg_id} отсутствует в work_breakdown_structure")
        if pkg_id not in volume_calc_packages:
            issues.append(f"❌ Пакет {pkg_id} отсутствует в volume_calculations")
        if pkg_id not in scheduled_packages_ids:
            issues.append(f"❌ Пакет {pkg_id} отсутствует в scheduled_packages")

    # Проверка 3: Наличие calculations в пакетах
    missing_calculations = []
    for pkg in results.get('volume_calculations', []):
        if pkg.get('type') == 'package' and 'calculations' not in pkg:
            missing_calculations.append(pkg.get('id', 'unknown'))

    if missing_calculations:
        issues.append(f"❌ Пакеты без calculations: {missing_calculations}")
    else:
        print(f"✅ Все пакеты в volume_calculations имеют calculations")

    # Проверка 4: Наличие scheduling_reasoning в scheduled_packages
    missing_reasoning = []
    for pkg in results.get('scheduled_packages', []):
        if 'scheduling_reasoning' not in pkg:
            missing_reasoning.append(pkg.get('package_id', pkg.get('id', 'unknown')))

    if missing_reasoning:
        issues.append(f"❌ Пакеты без scheduling_reasoning: {missing_reasoning}")
    else:
        print(f"✅ Все scheduled_packages имеют scheduling_reasoning")

    # Проверка 5: timeline_blocks
    timeline_blocks = truth_data.get('timeline_blocks', [])
    if not timeline_blocks:
        issues.append(f"❌ Отсутствуют timeline_blocks")
    else:
        print(f"✅ timeline_blocks: {len(timeline_blocks)} блоков")

        # Проверяем что scheduled_packages ссылаются на существующие блоки
        used_blocks = set()
        for pkg in results.get('scheduled_packages', []):
            schedule_blocks = pkg.get('schedule_blocks', [])
            used_blocks.update(schedule_blocks)

        available_blocks = set(block.get('block_id', block.get('week_id')) for block in timeline_blocks)
        missing_blocks = used_blocks - available_blocks
        if missing_blocks:
            issues.append(f"❌ Ссылки на несуществующие блоки: {missing_blocks}")

    # Вывод результатов
    print(f"\n📊 Результаты проверки:")
    if not issues:
        print("🎉 Логических несостыковок не найдено!")
    else:
        print(f"🚨 Найдено {len(issues)} проблем:")
        for issue in issues:
            print(f"   {issue}")

    return issues

if __name__ == "__main__":
    # Проверяем последний проект
    project_path = "/home/imort/Herzog_v3/projects/34975055/b38f541e/true.json"

    if os.path.exists(project_path):
        issues = check_truth_structure(project_path)
        print(f"\n🎯 Итого найдено проблем: {len(issues)}")
    else:
        print(f"❌ Файл не найден: {project_path}")