FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY src/ src/
COPY main_bot.py .
COPY .env.example .env

# Создаем необходимые директории
RUN mkdir -p projects logs temp

# Устанавливаем переменные среды
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Открываем порт для веб-интерфейса (если будет)
EXPOSE 8000

# Команда по умолчанию
CMD ["python", "main_bot.py"]