# 🤖 Руководство по системе агентов HerZog v3.0

## 📊 Текущая схема сохранения данных

Каждый агент работает по принципу **"Читай → Обрабатывай → Сохраняй"**:

| Агент | Читает из | Добавляет к данным | Сохраняет в |
|-------|-----------|-------------------|-------------|
| `1.1_group_creator` | `3_prepared/` | `work_groups` (массив групп) | `4.1_grouped/` |
| `1.2_group_assigner` | `4.1_grouped/` | `group_uuid` к каждой работе | `4_conceptualized/` |
| `2_strategist` | `4_conceptualized/` | `schedule_phases` к работам | `5_scheduled/` |
| `3_accountant` | `5_scheduled/` | `consolidated_volume`, `unit_cost` | `6_accounted/` |
| `4_foreman` | `6_accounted/` | `worker_counts` к работам | `7_staffed/` |

### Два UUID у каждой работы:
- **`"id"`** - новый UUID для системы HerZog (создается в `preparer.py`)
- **`"internal_id"`** - оригинальный UUID из Excel сметы (создается в `extractor.py`)

---

## 🚀 Гибкая система нумерации агентов

### Формат ID агентов:
- **Основные**: `{группа}_{имя}` (например: `2_strategist`, `3_accountant`)
- **Подагенты**: `{группа}.{подгруппа}_{имя}` (например: `1.1_group_creator`, `1.2_group_assigner`)
- **Дополнительные**: `{группа}.{номер}_{имя}` (например: `3.5_cost_optimizer`)

### Группы агентов:
1. **Группа 1** - Концептуализация (группировка работ)
2. **Группа 2** - Планирование (временные этапы)
3. **Группа 3** - Учет (объемы и стоимость)
4. **Группа 4** - Ресурсы (распределение людей)

---

## ➕ Как легко добавить нового агента

### Вариант 1: Добавить после существующего агента
```python
from ai_agents.agent_config_v2 import add_agent_after

# Добавляем контроллер качества после группировщика
new_agent_id = add_agent_after(
    after_agent_id="1.1_group_creator",
    new_agent_id="quality_checker",
    name="Контроллер качества",
    description="Проверяет правильность группировки",
    prompt_file="agent_1.3_quality_checker_prompt.txt"
)
# Результат: создастся агент "1.3_quality_checker"
```

### Вариант 2: Добавить в конец группы
```python
from ai_agents.agent_config_v2 import registry

# Добавляем оптимизатор стоимости в группу 3 (Учет)
cost_optimizer_id = registry.add_agent_to_group(
    group=3,
    agent_id="cost_optimizer",
    name="Оптимизатор стоимости", 
    description="Анализирует возможности экономии",
    prompt_file="agent_3.5_cost_optimizer_prompt.txt"
)
# Результат: создастся агент "3.2_cost_optimizer" (или следующий свободный номер)
```

### Шаги для добавления агента:

1. **Создать промпт файл** в папке `src/prompts/`
2. **Зарегистрировать агента** (код выше)
3. **Создать логику обработки** (опционально):
   ```python
   from ai_agents.agent_logic_v2 import processor
   
   # Функция извлечения данных для агента
   def extract_for_new_agent(project_data):
       return {
           'work_groups': project_data.get('work_groups', []),
           'directives': project_data.get('directives', {})
       }
   
   # Функция обработки ответа LLM
   def process_new_agent_output(llm_response, project_data):
       updated_data = project_data.copy()
       # ... обработка ответа ...
       updated_data['new_agent_result'] = parsed_response
       return updated_data
   
   # Регистрация обработчиков
   processor.register_input_extractor("3.5_cost_optimizer", extract_for_new_agent)
   processor.register_output_processor("3.5_cost_optimizer", process_new_agent_output)
   ```

4. **Обновить пайплайн** для использования нового агента

---

## 🔧 Примеры использования

### Посмотреть текущую последовательность агентов:
```python
from ai_agents.agent_config_v2 import registry

for agent_id in registry.get_pipeline_sequence():
    config = registry.get_agent(agent_id)
    print(f"{agent_id}: {config['name']}")
```

### Получить агентов в группе:
```python
# Все агенты группы 1 (Концептуализация)
group_1_agents = registry.get_agents_by_group(1)
for agent in group_1_agents:
    print(f"{agent['agent_id']}: {agent['name']}")
```

### Проверить валидность системы:
```python
errors = registry.validate_pipeline()
if errors:
    print("Ошибки:", errors)
else:
    print("Система валидна!")
```

---

## 🎯 Готовые сценарии расширения

### 1. Контроль качества между этапами
```python
add_agent_after("1.1_group_creator", "quality_checker", ...)  # 1.3_quality_checker
add_agent_after("2_strategist", "schedule_validator", ...)     # 2.2_schedule_validator
```

### 2. Оптимизация и анализ
```python
registry.add_agent_to_group(3, "cost_optimizer", ...)     # 3.2_cost_optimizer  
registry.add_agent_to_group(3, "risk_analyzer", ...)      # 3.3_risk_analyzer
registry.add_agent_to_group(4, "resource_optimizer", ...) # 4.2_resource_optimizer
```

### 3. Специализированные планировщики
```python
registry.add_agent_to_group(2, "safety_planner", ...)     # 2.2_safety_planner
registry.add_agent_to_group(2, "equipment_planner", ...)  # 2.3_equipment_planner
```

---

## 📁 Файлы новой системы

- `src/ai_agents/agent_config_v2.py` - Гибкая конфигурация агентов
- `src/ai_agents/agent_logic_v2.py` - Обновленная логика обработки данных
- `examples/add_new_agent_example.py` - Демонстрация добавления агентов

---

## ✅ Преимущества новой системы

1. **Легкое добавление агентов** - одна функция вместо правки множества файлов
2. **Автоматическая нумерация** - система сама определяет номера подгрупп
3. **Группировка по функциям** - логическое разделение на этапы пайплайна
4. **Обратная совместимость** - старые агенты работают без изменений
5. **Валидация системы** - автоматическая проверка целостности
6. **Расширяемость** - поддержка произвольного количества агентов

🎉 **Система готова к легкому расширению!**