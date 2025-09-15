# Отчёт о миграции на Claude API
Дата: Mon Sep 15 13:43:36 +05 2025

## Мигрированные файлы:
- src/ai_agents/work_packager.py - ✅ Мигрирован
- src/ai_agents/works_to_packages.py - ✅ Мигрирован
- src/ai_agents/counter.py - ✅ Мигрирован
- src/ai_agents/scheduler_and_staffer.py - ✅ Мигрирован
- src/data_processing/gemini_classifier.py - ✅ Мигрирован

## Как откатить изменения:
```bash
cp src/ai_agents/work_packager.py.gemini_backup src/ai_agents/work_packager.py
cp src/ai_agents/works_to_packages.py.gemini_backup src/ai_agents/works_to_packages.py
cp src/ai_agents/counter.py.gemini_backup src/ai_agents/counter.py
cp src/ai_agents/scheduler_and_staffer.py.gemini_backup src/ai_agents/scheduler_and_staffer.py
cp src/data_processing/gemini_classifier.py.gemini_backup src/data_processing/gemini_classifier.py
```

## Настройки:
- CLAUDE_TEST_MODE=true (Claude 3.5 Sonnet, дешевле)
- CLAUDE_TEST_MODE=false (Claude Sonnet 4, дороже)