#!/usr/bin/env python3
"""
Тест восстановления поврежденного JSON
"""

import sys
import os

# Добавляем путь к модулям Herzog
sys.path.append('/home/imort/Herzog_v3')

from src.shared.gemini_client import gemini_client
from src.ai_agents.work_packager import WorkPackager

def test_json_recovery():
    """Тестируем восстановление поврежденного JSON"""
    
    print("🧪 Тестирование восстановления поврежденного JSON...")
    
    # Сырой ответ из реального проекта (обрезанный)
    broken_json = """{
  "work_packages": [
    {
      "package_id": "pkg_001",
      "name": "Демонтаж кровли и стропильной системы",
      "description": "Разборка кровельного покрытия из хризотилцементных листов, обрешетки и деревянных элементов конструкций крыш."
    },
    {
      "package_id": "pkg_002",
      "name": "Демонтаж внутренних конструкций",
      "description": "Разборка кирпичных стен и железобетонных фундаментов внутри здания."
    },
    {
      "package_id": "pkg_003",
      "name": "Демонтаж полов и оснований",
      "description": "Разборка покрытий полов (плитка, цемент, линолеум, доски), оснований, лаг, столбиков и плинтусов."
    },
    {
      "package_id": "pkg_015",
      "name": "Отделка потолков",
      "description" """
    
    print("🔧 Тестирую _try_fix_broken_json...")
    
    try:
        fixed = gemini_client._try_fix_broken_json(broken_json)
        print(f"✅ JSON восстановлен! Найдено пакетов: {len(fixed.get('work_packages', []))}")
        
        for pkg in fixed.get('work_packages', [])[:3]:  # Показываем первые 3
            print(f"   - {pkg.get('package_id')}: {pkg.get('name')}")
            
    except Exception as e:
        print(f"❌ Ошибка восстановления JSON: {e}")
    
    print("\n🔧 Тестирую _extract_packages_from_raw_response...")
    
    try:
        packager = WorkPackager()
        packages = packager._extract_packages_from_raw_response(broken_json)
        print(f"✅ Извлечено пакетов из сырого ответа: {len(packages)}")
        
        for pkg in packages[:3]:  # Показываем первые 3
            print(f"   - {pkg.get('package_id')}: {pkg.get('name')}")
            
    except Exception as e:
        print(f"❌ Ошибка извлечения пакетов: {e}")
    
    print("\n🔧 Тестирую создание fallback пакетов...")
    
    try:
        packager = WorkPackager()
        fallback = packager._create_basic_fallback_packages()
        print(f"✅ Создано fallback пакетов: {len(fallback)}")
        
        for pkg in fallback:
            print(f"   - {pkg.get('package_id')}: {pkg.get('name')}")
            
    except Exception as e:
        print(f"❌ Ошибка создания fallback: {e}")

if __name__ == "__main__":
    test_json_recovery()