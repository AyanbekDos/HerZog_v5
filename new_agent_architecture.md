# Техническое Задание: Упрощение Архитектуры Агентов через true.json

## 🎯 Краткая суть изменений

Создаем единый файл `true.json` в папке каждого проекта смет (например: `/projects/34975055/913cf31a/true.json`), который становится единственным источником правды. Все агенты читают и пишут только в него.

## 📋 Что у нас есть сейчас

### Текущая структура:
```
/Herzog_v3/
├── main_bot.py
├── /src/
│   ├── main_pipeline.py              # Главный координатор
│   ├── /ai_agents/
│   │   ├── agent_config_v2.py        # Конфигурация агентов
│   │   ├── agent_logic_v2.py         # Логика обработки данных
│   │   └── agent_runner.py           # Запуск агентов
│   └── /shared/
│       └── gemini_client.py          # Уже есть клиент для LLM
└── /projects/
    └── /{user_id}/{project_id}/
        ├── 0_input/
        ├── 1_extracted/
        ├── 2_classified/
        ├── 3_prepared/
        ├── 4.1_grouped/              # Агент 1.1
        ├── 4_conceptualized/         # Агент 1.2
        ├── 5_scheduled/              # Агент 2
        ├── 6_accounted/              # Агент 3
        ├── 7_staffed/                # Агент 4
        └── 8_output/
```

### Текущие агенты (из agent_config_v2.py):
1. `1.1_group_creator` - Создает группы работ
2. `1.2_group_assigner` - Назначает работы в группы (ЗДЕСЬ НУЖНО БАТЧИРОВАНИЕ!)
3. `2_strategist` - Планирует временные этапы
4. `3_accountant` - Подсчитывает объемы
5. `4_foreman` - Распределяет рабочих

## 🔧 Что меняем

### 1. Добавляем true.json в корень папки проекта
**Путь**: `/projects/{user_id}/{project_id}/true.json`

**Структура** (как в примере):
```json
{
  "metadata": {
    "project_id": "...",
    "pipeline_status": [
      { "agent_name": "1.1_group_creator", "status": "pending" },
      { "agent_name": "1.2_group_assigner", "status": "pending" },
      { "agent_name": "2_strategist", "status": "pending" },
      { "agent_name": "3_accountant", "status": "pending" },
      { "agent_name": "4_foreman", "status": "pending" }
    ]
  },
  "project_inputs": { ... },
  "timeline_blocks": [ ... ],
  "source_work_items": [ ... ],
  "results": {
    "work_packages": [],
    "schedule": {},
    "accounting": {},
    "staffing": {}
  }
}
```

### 2. Модифицируем main_pipeline.py
```python
def run_pipeline(project_path):
    """Читает true.json и запускает нужного агента"""
    truth_path = f"{project_path}/true.json"
    
    # Читаем файл правды
    with open(truth_path, 'r') as f:
        truth = json.load(f)
    
    # Находим агента со статусом "in_progress" или первого "pending"
    current_agent = None
    for agent in truth['metadata']['pipeline_status']:
        if agent['status'] == 'in_progress':
            current_agent = agent['agent_name']
            break
        elif agent['status'] == 'pending' and not current_agent:
            current_agent = agent['agent_name']
            agent['status'] = 'in_progress'
    
    if current_agent:
        # Запускаем агента
        run_agent(current_agent, project_path)
```

### 3. Модифицируем agent_runner.py

Каждый агент делает следующее:

```python
def run_agent(agent_id, project_path):
    """Универсальный запуск агента"""
    
    # 1. Читаем true.json
    truth_path = f"{project_path}/true.json"
    with open(truth_path, 'r') as f:
        truth = json.load(f)
    
    # 2. Получаем конфигурацию агента (какие теги брать)
    agent_config = get_agent_tags(agent_id)
    
    # 3. Извлекаем нужные данные по тегам
    agent_data = extract_by_tags(truth, agent_config['input_tags'])
    
    # 4. Подготавливаем запрос к LLM
    llm_input = prepare_llm_input(agent_id, agent_data)
    
    # 5. Сохраняем llm_input.json в папку агента
    agent_folder = get_agent_folder(agent_id, project_path)
    with open(f"{agent_folder}/llm_input.json", 'w') as f:
        json.dump(llm_input, f)
    
    # 6. Отправляем в Gemini (с батчированием для агента 1.2)
    if agent_id == "1.2_group_assigner" and len(truth['source_work_items']) > 100:
        responses = process_in_batches(llm_input)
    else:
        responses = gemini_client.send(llm_input)
    
    # 7. Сохраняем llm_response.json
    with open(f"{agent_folder}/llm_response.json", 'w') as f:
        json.dump(responses, f)
    
    # 8. Обновляем true.json результатами
    update_truth_with_results(truth, agent_id, responses)
    
    # 9. Обновляем статусы в pipeline_status
    update_pipeline_status(truth, agent_id)
    
    # 10. Сохраняем обновленный true.json
    with open(truth_path, 'w') as f:
        json.dump(truth, f)
    
    # 11. Копируем true.json в папку агента для истории
    with open(f"{agent_folder}/true.json", 'w') as f:
        json.dump(truth, f)
```

### 4. Конфигурация тегов для агентов

Добавляем в agent_config_v2.py:

```python
AGENT_TAGS = {
    "1.1_group_creator": {
        "input_tags": ["project_inputs", "source_work_items"],
        "output_tags": ["results.work_packages"]
    },
    "1.2_group_assigner": {
        "input_tags": ["source_work_items", "results.work_packages"],
        "output_tags": ["source_work_items[].package_id"],
        "needs_batching": True,
        "batch_size": 50
    },
    "2_strategist": {
        "input_tags": ["project_inputs", "timeline_blocks", "results.work_packages"],
        "output_tags": ["results.schedule"]
    },
    "3_accountant": {
        "input_tags": ["project_inputs", "results.work_packages", "source_work_items"],
        "output_tags": ["results.accounting"]
    },
    "4_foreman": {
        "input_tags": ["project_inputs", "timeline_blocks", "results.schedule", "results.accounting"],
        "output_tags": ["results.staffing"]
    }
}
```

### 5. Батчирование для агента 1.2

```python
def process_in_batches(llm_input):
    """
    Разбивает большой запрос на батчи для агента 1.2
    При 1000 работ и 40 групп = 20 батчей по 50 работ
    """
    work_items = llm_input['source_work_items']
    work_packages = llm_input['work_packages']
    
    batch_size = 50
    batches = []
    
    # Разбиваем работы на чанки
    for i in range(0, len(work_items), batch_size):
        batch = {
            'work_packages': work_packages,  # Все группы в каждом батче
            'source_work_items': work_items[i:i+batch_size]
        }
        batches.append(batch)
    
    # Обрабатываем батчи параллельно
    results = []
    for batch in batches:
        response = gemini_client.send(batch)
        results.extend(response)
    
    return merge_batch_results(results)
```

### 6. Обновление статусов

```python
def update_pipeline_status(truth, current_agent_id):
    """Обновляет статусы агентов в true.json"""
    agents = truth['metadata']['pipeline_status']
    
    for i, agent in enumerate(agents):
        if agent['agent_name'] == current_agent_id:
            # Завершаем текущего
            agent['status'] = 'completed'
            agent['completed_at'] = datetime.now().isoformat()
            
            # Активируем следующего
            if i + 1 < len(agents):
                agents[i + 1]['status'] = 'in_progress'
                agents[i + 1]['started_at'] = datetime.now().isoformat()
            break
```

## 📂 Что получается в итоге

После работы всех агентов структура папки проекта:
```
/projects/{user_id}/{project_id}/
├── true.json                      # ЕДИНЫЙ ИСТОЧНИК ПРАВДЫ
├── 0_input/
├── ...
├── 4.1_grouped/
│   ├── llm_input.json            # Запрос агента 1.1
│   ├── llm_response.json         # Ответ для агента 1.1
│   └── true.json                 # Снимок true.json после агента 1.1
├── 4_conceptualized/
│   ├── llm_input.json            # Запрос агента 1.2
│   ├── llm_response.json         # Ответ для агента 1.2
│   └── true.json                 # Снимок true.json после агента 1.2
└── ...
```

## 🔄 Workflow

1. **Запуск**: `main_pipeline.py` читает `true.json`
2. **Поиск агента**: Находит агента со статусом "in_progress" или первого "pending"
3. **Выполнение**: Агент читает теги → создает запрос → получает ответ → обновляет true.json
4. **Статусы**: Меняет свой статус на "completed", следующего на "in_progress"
5. **Повтор**: `main_pipeline.py` запускается снова и находит следующего агента

## ✅ Преимущества

1. **Простота**: Один файл правды, все понятно
2. **Прозрачность**: В папках агентов лежат промежуточные результаты
3. **История изменений**: Каждый агент сохраняет свой снимок true.json
4. **Батчирование**: Только для агента 1.2 где это критично
5. **Используем существующее**: gemini_client.py уже есть и работает

## ⚠️ Что НЕ добавляем

- ❌ Новые сущности типа base_agent.py
- ❌ truth_manager.py (просто json.load/json.dump)
- ❌ llm_client.py (есть gemini_client.py)
- ❌ true_backup.json в каждой папке (предыдущая версия и так в папке предыдущего агента)

## 📝 Последовательность реализации

1. Создать функцию инициализации true.json из существующих данных
2. Модифицировать main_pipeline.py для работы с true.json
3. Добавить в agent_config_v2.py маппинг тегов
4. Модифицировать agent_runner.py для чтения/записи true.json
5. Реализовать батчирование для агента 1.2
6. Протестировать на реальном проекте

---

*Техническое задание для Sonnet 4*
*Все основано на существующей архитектуре, минимум изменений*