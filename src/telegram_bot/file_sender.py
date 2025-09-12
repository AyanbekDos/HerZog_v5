"""
File Sender для HerZog v3.0 
Модуль для отправки готовых Excel и PDF файлов в Telegram
"""

import os
import logging
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime
import mimetypes

logger = logging.getLogger(__name__)

class TelegramFileSender:
    """
    Класс для отправки файлов в Telegram
    """
    
    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token
        self.max_file_size = 50 * 1024 * 1024  # 50MB - лимит Telegram
        
    async def send_project_files(self, chat_id: int, project_files: Dict[str, str], 
                               project_name: str = "Проект") -> Dict[str, Any]:
        """
        Отправляет файлы проекта пользователю в Telegram
        
        Args:
            chat_id: ID чата пользователя
            project_files: Словарь {тип_файла: путь_к_файлу}
            project_name: Название проекта
            
        Returns:
            Результат отправки
        """
        try:
            logger.info(f"📤 Отправка файлов проекта '{project_name}' в чат {chat_id}")
            
            # Проверяем наличие bot_token
            if not self.bot_token:
                logger.error("❌ Bot token не задан")
                return {
                    'success': False,
                    'error': 'Bot token не настроен'
                }
            
            # Импортируем telegram библиотеки
            try:
                from telegram import Bot
                from telegram.constants import ParseMode
            except ImportError:
                logger.error("❌ python-telegram-bot не установлен")
                return {
                    'success': False,
                    'error': 'Telegram библиотека не установлена'
                }
            
            # Создаем бота
            bot = Bot(token=self.bot_token)
            
            # Проверяем файлы
            valid_files = self._validate_files(project_files)
            if not valid_files:
                return {
                    'success': False,
                    'error': 'Нет валидных файлов для отправки'
                }
            
            # Отправляем заголовок
            header_text = f"📊 *КАЛЕНДАРНЫЙ ГРАФИК ГОТОВ*\\n\\n" \
                         f"🏗️ Проект: *{self._escape_markdown(project_name)}*\\n" \
                         f"📅 Дата: {datetime.now().strftime('%d\\.%m\\.%Y %H:%M')}\\n" \
                         f"📄 Файлов: {len(valid_files)}"
            
            await bot.send_message(
                chat_id=chat_id,
                text=header_text,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            
            # Отправляем файлы
            sent_files = []
            failed_files = []
            
            for file_type, file_path in valid_files.items():
                try:
                    result = await self._send_single_file(bot, chat_id, file_path, file_type)
                    if result['success']:
                        sent_files.append(file_type)
                        logger.info(f"✅ Отправлен {file_type}: {file_path}")
                    else:
                        failed_files.append((file_type, result['error']))
                        logger.error(f"❌ Ошибка отправки {file_type}: {result['error']}")
                
                except Exception as e:
                    failed_files.append((file_type, str(e)))
                    logger.error(f"❌ Исключение при отправке {file_type}: {e}")
                
                # Небольшая пауза между файлами
                await asyncio.sleep(1)
            
            # Отправляем итоговое сообщение
            summary_text = self._create_summary_message(sent_files, failed_files, project_name)
            await bot.send_message(
                chat_id=chat_id,
                text=summary_text,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            
            return {
                'success': True,
                'sent_files': sent_files,
                'failed_files': failed_files,
                'total_sent': len(sent_files)
            }
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка отправки файлов: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_files(self, project_files: Dict[str, str]) -> Dict[str, str]:
        """Валидирует файлы перед отправкой"""
        valid_files = {}
        
        for file_type, file_path in project_files.items():
            if not file_path or not os.path.exists(file_path):
                logger.warning(f"⚠️ Файл не существует: {file_type} -> {file_path}")
                continue
            
            # Проверяем размер файла
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.warning(f"⚠️ Файл слишком большой: {file_type} -> {file_size} bytes")
                continue
            
            if file_size == 0:
                logger.warning(f"⚠️ Пустой файл: {file_type} -> {file_path}")
                continue
                
            valid_files[file_type] = file_path
            logger.info(f"✅ Файл валиден: {file_type} -> {file_path} ({file_size} bytes)")
        
        return valid_files
    
    async def _send_single_file(self, bot, chat_id: int, file_path: str, file_type: str) -> Dict[str, Any]:
        """Отправляет один файл"""
        try:
            # Определяем MIME-type
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # Создаем красивое имя файла
            filename = self._create_filename(file_path, file_type)
            
            # Создаем описание файла
            caption = self._create_file_caption(file_path, file_type)
            
            # Отправляем файл как документ
            with open(file_path, 'rb') as file:
                await bot.send_document(
                    chat_id=chat_id,
                    document=file,
                    filename=filename,
                    caption=caption,
                    parse_mode="Markdown"
                )
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _create_filename(self, file_path: str, file_type: str) -> str:
        """Создает красивое имя файла для отправки"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        extension = os.path.splitext(file_path)[1]
        
        # Маппинг типов файлов на красивые названия
        type_names = {
            'excel': 'График',
            'pdf': 'PDF_График', 
            'xlsx': 'Excel_Отчет',
            'report': 'Отчет'
        }
        
        nice_name = type_names.get(file_type, file_type)
        return f"HerZog_{nice_name}_{timestamp}{extension}"
    
    def _create_file_caption(self, file_path: str, file_type: str) -> str:
        """Создает описание файла"""
        file_size = os.path.getsize(file_path)
        size_mb = round(file_size / (1024 * 1024), 2)
        
        # Маппинг описаний
        descriptions = {
            'excel': '📊 *Excel календарный график*',
            'pdf': '📄 *PDF календарный график*',
            'xlsx': '📋 *Многостраничный Excel отчет*',
            'report': '📊 *Отчет по проекту*'
        }
        
        description = descriptions.get(file_type, f'📎 *{file_type.capitalize()} файл*')
        
        return f"{description}\\nРазмер: {size_mb} MB"
    
    def _create_summary_message(self, sent_files: List[str], failed_files: List[tuple], project_name: str) -> str:
        """Создает итоговое сообщение"""
        summary = f"✅ *ОТПРАВКА ЗАВЕРШЕНА*\\n\\n"
        summary += f"🏗️ Проект: *{self._escape_markdown(project_name)}*\\n"
        
        if sent_files:
            summary += f"📤 Отправлено файлов: *{len(sent_files)}*\\n"
            for file_type in sent_files:
                summary += f"   ✓ {file_type}\\n"
        
        if failed_files:
            summary += f"❌ Ошибки отправки: *{len(failed_files)}*\\n"
            for file_type, error in failed_files:
                summary += f"   ✗ {file_type}: {error[:30]}\\.\\.\\n"
        
        summary += f"\\n🕐 Время: {datetime.now().strftime('%d\\.%m\\.%Y %H:%M')}"
        
        return summary
    
    def _escape_markdown(self, text: str) -> str:
        """Экранирует специальные символы для Markdown V2"""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text


class FileDeliveryManager:
    """
    Менеджер доставки файлов - интеграция с основным pipeline
    """
    
    def __init__(self, bot_token: str = None):
        self.sender = TelegramFileSender(bot_token)
    
    async def deliver_project_results(self, chat_id: int, project_path: str, 
                                    project_name: str = None) -> Dict[str, Any]:
        """
        Доставляет результаты проекта пользователю
        
        Args:
            chat_id: ID пользователя в Telegram
            project_path: Путь к папке проекта
            project_name: Название проекта
            
        Returns:
            Результат доставки
        """
        try:
            # Определяем название проекта
            if not project_name:
                # Пытаемся прочитать из true.json
                truth_file = os.path.join(project_path, 'true.json')
                if os.path.exists(truth_file):
                    import json
                    with open(truth_file, 'r', encoding='utf-8') as f:
                        truth_data = json.load(f)
                    
                    # Для v2.0 структуры
                    project_name = truth_data.get('meta', {}).get('project_name')
                    # Для v1.0 структуры
                    if not project_name:
                        project_name = truth_data.get('project_inputs', {}).get('project_name')
                    
                    if not project_name:
                        project_name = "Безымянный проект"
                else:
                    project_name = "Проект"
            
            # Собираем файлы для отправки
            project_files = self._collect_project_files(project_path)
            
            if not project_files:
                return {
                    'success': False,
                    'error': 'Нет готовых файлов для отправки'
                }
            
            # Отправляем файлы
            return await self.sender.send_project_files(chat_id, project_files, project_name)
            
        except Exception as e:
            logger.error(f"❌ Ошибка доставки результатов проекта: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _collect_project_files(self, project_path: str) -> Dict[str, str]:
        """Собирает файлы проекта для отправки"""
        files = {}
        
        # Ищем в папке 8_output
        output_dir = os.path.join(project_path, '8_output')
        if os.path.exists(output_dir):
            for filename in os.listdir(output_dir):
                file_path = os.path.join(output_dir, filename)
                if os.path.isfile(file_path):
                    if filename.endswith('.xlsx'):
                        files['excel'] = file_path
                    elif filename.endswith('.pdf'):
                        files['pdf'] = file_path
        
        # Ищем в корне проекта
        for filename in os.listdir(project_path):
            file_path = os.path.join(project_path, filename)
            if os.path.isfile(file_path):
                if filename.endswith('.xlsx') and 'excel' not in files:
                    files['excel'] = file_path
                elif filename.endswith('.pdf') and 'pdf' not in files:
                    files['pdf'] = file_path
        
        # Ищем в /tmp (где создаются наши тестовые файлы)
        tmp_files = [f for f in os.listdir('/tmp') if f.startswith(('Отчет_', 'Календарный_график_'))]
        for filename in tmp_files:
            file_path = os.path.join('/tmp', filename)
            if filename.endswith('.xlsx') and 'excel' not in files:
                files['xlsx'] = file_path
            elif filename.endswith('.pdf') and 'pdf' not in files:
                files['pdf'] = file_path
        
        return files


# Удобная функция для использования в pipeline
async def send_project_files_to_user(chat_id: int, project_path: str, 
                                   bot_token: str, project_name: str = None) -> Dict[str, Any]:
    """
    Отправляет готовые файлы проекта пользователю в Telegram
    
    Args:
        chat_id: ID пользователя в Telegram
        project_path: Путь к папке проекта
        bot_token: Токен Telegram бота
        project_name: Название проекта (опционально)
        
    Returns:
        Результат отправки
    """
    manager = FileDeliveryManager(bot_token)
    return await manager.deliver_project_results(chat_id, project_path, project_name)


if __name__ == "__main__":
    # Тестирование отправки файлов (требует настройки bot_token)
    import asyncio
    
    async def test_file_sending():
        # Тестовые данные
        test_chat_id = 123456789  # Замените на реальный chat_id
        test_project_path = "/home/imort/Herzog_v3/projects/34975055/a61b42bf"
        test_bot_token = "YOUR_BOT_TOKEN_HERE"  # Замените на реальный токен
        
        print("🧪 Тестирование отправки файлов...")
        print("⚠️ Для реального тестирования нужен bot_token и chat_id")
        
        # Создаем тестовые файлы для демонстрации
        manager = FileDeliveryManager()
        files = manager._collect_project_files(test_project_path)
        
        print(f"📋 Найденные файлы для отправки:")
        for file_type, file_path in files.items():
            size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            print(f"   {file_type}: {file_path} ({size} bytes)")
        
        print("✅ Тестирование сбора файлов завершено")
    
    asyncio.run(test_file_sending())