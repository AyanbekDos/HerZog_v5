#!/bin/bash

# HerZog v3.0 Deployment Script for Digital Ocean
# Этот скрипт автоматизирует развертывание системы на сервере

set -e

echo "🚀 Начинаем развертывание HerZog v3.0..."

# Проверяем переменные окружения
if [ -z "$DO_DROPLET_IP" ]; then
    echo "❌ Не задана переменная DO_DROPLET_IP"
    exit 1
fi

if [ -z "$DO_SSH_KEY_PATH" ]; then
    echo "❌ Не задана переменная DO_SSH_KEY_PATH"
    exit 1
fi

echo "📡 Подключаемся к серверу $DO_DROPLET_IP..."

# Развертывание на сервере
ssh -i "$DO_SSH_KEY_PATH" -o StrictHostKeyChecking=no root@$DO_DROPLET_IP << 'EOF'
# Обновляем систему
apt update && apt upgrade -y

# Устанавливаем Docker если не установлен
if ! command -v docker &> /dev/null; then
    echo "🐳 Устанавливаем Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
fi

# Устанавливаем Docker Compose если не установлен
if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Устанавливаем Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Создаем рабочую директорию
mkdir -p /opt/herzog
cd /opt/herzog

# Клонируем репозиторий или обновляем
if [ -d ".git" ]; then
    echo "📦 Обновляем код..."
    git pull origin main
else
    echo "📦 Клонируем репозиторий..."
    git clone https://github.com/AyanbekDos/HerZog_v5.git .
fi

# Создаем необходимые директории
mkdir -p projects logs temp

# Останавливаем старые контейнеры
docker-compose down || true

echo "🔧 Создайте файл .env со следующими переменными:"
echo "TELEGRAM_BOT_TOKEN=your_token"
echo "GOOGLE_API_KEY=your_key"
echo ""
echo "После создания .env запустите: docker-compose up -d"

EOF

echo "✅ Скрипт развертывания выполнен успешно!"
echo "🎯 Не забудьте создать .env файл на сервере и запустить docker-compose up -d"