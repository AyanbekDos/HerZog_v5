# HerZog v3.0 🏗️

**Политический инструмент** для быстрого формирования управляемого календарного плана строительных работ на основе сметных данных.

## 🚀 Особенности

- **AI-Powered Planning**: 8-этапный конвейер с использованием Google Gemini
- **Telegram Bot Interface**: Простой интерфейс для загрузки смет и получения планов  
- **Multi-Model Architecture**: Оптимизированная архитектура для минимизации токенов
- **RECITATION Bypass**: Продвинутая система обхода блокировок AI
- **Professional Reports**: Многостраничные Excel отчеты с обоснованиями
- **Docker Ready**: Полная контейнеризация для легкого деплоя

## 🏗️ Архитектура

```
📊 Excel Смета → 🤖 AI Pipeline → 📅 Календарный План
```

### Этапы обработки:
1. **Extractor** - Извлечение данных из Excel
2. **Classifier** - Классификация работ/материалов  
3. **Preparer** - Подготовка единой структуры данных
4. **Work Packager** - Создание укрупненных пакетов работ
5. **Works to Packages** - Распределение работ по пакетам
6. **Counter** - Подсчет объемов и стоимостей
7. **Scheduler & Staffer** - Календарное планирование и ресурсы
8. **Reporter** - Генерация итоговых отчетов

## 🛠️ Технологический стек

- **Backend**: Python 3.11, asyncio
- **AI**: Google Gemini 2.5 Pro/Flash-Lite
- **Reports**: OpenPyXL, ReportLab
- **Bot**: python-telegram-bot
- **Deploy**: Docker, Docker Compose
- **CI/CD**: GitHub Actions

## 📦 Быстрый старт

### 1. Клонирование репозитория
```bash
git clone https://github.com/AyanbekDos/HerZog.git
cd HerZog
```

### 2. Настройка окружения
```bash
cp .env.example .env
# Отредактируйте .env со своими токенами
```

### 3. Запуск через Docker
```bash
docker-compose up -d
```

### 4. Локальная разработка
```bash
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows
pip install -r requirements.txt
python main_bot.py
```

## 🌊 Digital Ocean Deploy

### Автоматический деплой через GitHub Actions
1. Добавьте секреты в GitHub:
   - `DO_SSH_PRIVATE_KEY`
   - `DO_DROPLET_IP` 
   - `TELEGRAM_BOT_TOKEN`
   - `GOOGLE_API_KEY`

2. Push в main ветку автоматически задеплоит на сервер

### Ручной деплой
```bash
export DO_DROPLET_IP="your_server_ip"
export DO_SSH_KEY_PATH="/path/to/your/ssh/key"
./deploy.sh
```

## ⚙️ Конфигурация

### Переменные окружения (.env)
```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GOOGLE_API_KEY=your_google_gemini_api_key  
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Docker Compose
Настроен для production с:
- Автоперезапуск контейнеров
- Health checks
- Persistent volumes для проектов и логов
- Network isolation

## 🧪 Тестирование

```bash
# Тест системы обхода RECITATION
python test_recitation_bypass.py

# Тест отдельных агентов  
python -m src.ai_agents.work_packager projects/path/to/project
python -m src.ai_agents.scheduler_and_staffer projects/path/to/project
```

## 📊 Результаты

Система генерирует профессиональные Excel отчеты с:
- **📊 График** - Календарный план Gantt с цветовым кодированием
- **📅 Планирование** - Детальные обоснования решений AI
- **📋 Пакеты работ** - Информация по каждому пакету
- **🧮 Логика расчетов** - Техническая документация

## 🚨 Продвинутые фичи

### Anti-RECITATION System
Система автоматически обходит блокировки Gemini:
- Multi-model fallback (Pro → Flash-Lite)
- Dynamic prompt modification
- Temperature/top_p adjustment
- UUID-based prompt randomization

### Multi-Agent Architecture  
- Специализированные агенты для разных задач
- Оптимизированный выбор модели по сложности
- Batch processing для больших объемов данных

## 🐛 Troubleshooting

### Частые проблемы:
1. **RECITATION блокировки** - Система автоматически обходит
2. **Токен лимиты** - Используется batch processing
3. **Кодировка PDF** - Настроен DejaVu Sans для кириллицы

## 📈 Производительность

- **Обработка**: 168 работ → 29 пакетов за ~2 минуты
- **Токены**: 6-кратная оптимизация (453→75 токенов для простых агентов)  
- **Надежность**: 99%+ успешности благодаря fallback системе

## 🤝 Contributing

1. Fork репозиторий
2. Создайте feature branch
3. Коммитьте изменения  
4. Push в branch
5. Создайте Pull Request

## 📄 License

MIT License - смотрите файл LICENSE для деталей

## 🎯 Roadmap

- [ ] Web интерфейс
- [ ] API endpoints  
- [ ] Multiple file support
- [ ] Advanced scheduling algorithms
- [ ] Cost estimation
- [ ] Integration с 1С

---

**HerZog v3.0** - Когда нужно быстро и профессионально! 🚀