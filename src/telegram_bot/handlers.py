"""
Обработчики команд и сообщений для телеграм-бота HerZog
"""

import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from .questionnaire import ProjectQuestionnaire, STEP_MESSAGES

logger = logging.getLogger(__name__)
questionnaire = ProjectQuestionnaire()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - начало работы с ботом"""
    user = update.effective_user
    
    welcome_text = f"""
🏗️ **Добро пожаловать в HerZog v3.0!**

Привет, {user.first_name}! 

Я помогу создать календарный план строительных работ на основе ваших смет.

Для начала используйте команду /new чтобы создать новый проект.

📋 **Доступные команды:**
/new - Создать новый проект  
/test - Создать тестовый проект с готовыми данными 🧪
/help - Помощь
/cancel - Отменить текущий проект
    """
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def new_project_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /new - создание нового проекта"""
    user_id = update.effective_user.id
    
    # Сброс данных предыдущего проекта
    context.user_data.clear()
    context.user_data['user_id'] = user_id
    context.user_data['current_step'] = 'files'
    context.user_data['files'] = []
    
    # Отправляем первый шаг
    await update.message.reply_text(
        STEP_MESSAGES['files'],
        parse_mode='Markdown'
    )

async def test_project_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /test - создание тестового проекта с выбором этапа пайплайна"""
    user_id = update.effective_user.id
    
    # Путь к эталонному проекту
    test_source_project = "/home/imort/Herzog_v3/projects/34975055/da1ac471"
    
    if not os.path.exists(test_source_project):
        await update.message.reply_text(
            "❌ Эталонный проект не найден! Проверьте путь к da1ac471."
        )
        return
    
    # Показываем доступные этапы пайплайна
    stages = {
        "0": "0️⃣ Начать с загрузки файлов (0_input)",
        "1": "1️⃣ После извлечения (1_extracted)", 
        "2": "2️⃣ После классификации (2_classified)",
        "3": "3️⃣ После подготовки (3_prepared)",
        "4": "4️⃣ После work_packager (4_work_packager)",
        "5": "5️⃣ После works_to_packages (5_works_to_packages)",
        "6": "6️⃣ После counter (6_counter)",
        "7": "7️⃣ После scheduler_and_staffer (7_scheduler_and_staffer)",
        "8": "8️⃣ Полный проект (все этапы)"
    }
    
    keyboard = []
    for stage_key, stage_name in stages.items():
        keyboard.append([InlineKeyboardButton(stage_name, callback_data=f"test_stage_{stage_key}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🧪 **Создание тестового проекта**\n\n"
        "Выберите с какого этапа пайплайна начать:\n\n"
        "• Выберите этап 0 для полного прохождения\n"
        "• Выберите более поздний этап для отладки\n"
        "• Все файлы до выбранного этапа будут скопированы",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_test_stage_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора этапа для тестового проекта"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    stage = query.data.split('_')[-1]  # Извлекаем номер этапа
    
    test_source_project = "/home/imort/Herzog_v3/projects/34975055/da1ac471"
    
    await query.edit_message_text(
        f"🔄 **Создание тестового проекта...**\n\n"
        f"Копирую файлы до этапа {stage}...",
        parse_mode='Markdown'
    )
    
    try:
        # Создаем структуру проекта
        project_path = questionnaire.create_project_structure(user_id)
        
        # Копируем файлы до выбранного этапа
        success = _copy_project_files_up_to_stage(test_source_project, project_path, stage)
        
        if success:
            # Сохраняем информацию о выбранном этапе
            context.user_data['test_stage'] = stage
            context.user_data['project_path'] = project_path
            
            # Создаем информацию о файлах для совместимости с /process
            input_folder = os.path.join(project_path, "0_input")
            files_info = []
            
            # Ищем Excel файлы в input папке
            if os.path.exists(input_folder):
                for file_name in os.listdir(input_folder):
                    if file_name.endswith(('.xlsx', '.xls')):
                        file_path = os.path.join(input_folder, file_name)
                        file_info = {
                            'file_name': file_name,
                            'file_id': f'test_{file_name}',
                            'file_size': os.path.getsize(file_path),
                            'local_path': file_path,
                            'uploaded_at': datetime.now().isoformat()
                        }
                        files_info.append(file_info)
            
            context.user_data['files'] = files_info
            context.user_data['user_id'] = user_id
            
            await query.edit_message_text(
                f"✅ **Тестовый проект создан!**\n\n"
                f"📁 Путь: `{project_path}`\n"
                f"🎯 Этап: до {stage}\n\n"
                f"Теперь вы можете:\n"
                f"• Продолжить обработку с этапа {int(stage)+1 if stage.isdigit() and int(stage) < 8 else 'финального'}\n"
                f"• Изучить промежуточные результаты\n"
                f"• Отладить конкретный агент",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "❌ **Ошибка создания тестового проекта**\n\n"
                "Не удалось скопировать файлы. Проверьте логи.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Ошибка создания тестового проекта: {e}")
        await query.edit_message_text(
            f"❌ **Ошибка**: {str(e)}",
            parse_mode='Markdown'
        )

def _copy_project_files_up_to_stage(source_project: str, target_project: str, stage: str) -> bool:
    """Копирует файлы проекта до указанного этапа"""
    import shutil
    
    try:
        # Определяем какие папки копировать
        stage_folders = {
            "0": ["0_input"],
            "1": ["0_input", "1_extracted"], 
            "2": ["0_input", "1_extracted", "2_classified"],
            "3": ["0_input", "1_extracted", "2_classified", "3_prepared"],
            "4": ["0_input", "1_extracted", "2_classified", "3_prepared", "4_work_packager"],
            "5": ["0_input", "1_extracted", "2_classified", "3_prepared", "4_work_packager", "5_works_to_packages"],
            "6": ["0_input", "1_extracted", "2_classified", "3_prepared", "4_work_packager", "5_works_to_packages", "6_counter"],
            "7": ["0_input", "1_extracted", "2_classified", "3_prepared", "4_work_packager", "5_works_to_packages", "6_counter", "7_scheduler_and_staffer"],
            "8": ["0_input", "1_extracted", "2_classified", "3_prepared", "4_work_packager", "5_works_to_packages", "6_counter", "7_scheduler_and_staffer", "8_output"]
        }
        
        folders_to_copy = stage_folders.get(stage, ["0_input"])
        
        # Копируем каждую папку
        for folder in folders_to_copy:
            source_folder = os.path.join(source_project, folder)
            target_folder = os.path.join(target_project, folder)
            
            if os.path.exists(source_folder):
                if os.path.exists(target_folder):
                    shutil.rmtree(target_folder)
                shutil.copytree(source_folder, target_folder)
                logger.info(f"Скопирована папка: {folder}")
        
        # Копируем true.json если есть
        source_truth = os.path.join(source_project, "true.json")
        target_truth = os.path.join(target_project, "true.json")
        
        if os.path.exists(source_truth):
            shutil.copy2(source_truth, target_truth)
            logger.info("Скопирован true.json")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка копирования файлов: {e}")
        return False

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help - справка"""
    help_text = """
🆘 **Справка по использованию HerZog**

**Процесс работы:**
1. Создайте проект командой /new
2. Загрузите Excel-файлы смет  
3. Ответьте на вопросы бота
4. Получите готовый календарный план

**Команды:**
/new - Новый проект
/test - Тестовый проект (готовые данные) 🧪
/next - Следующий шаг (если применимо)
/skip - Пропустить текущий шаг
/cancel - Отменить проект
/help - Эта справка

**Поддерживаемые форматы:**
- Excel файлы (.xlsx) со сметами
- Даты в формате ДД.ММ.ГГГГ
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /cancel - отмена текущего проекта"""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Текущий проект отменен. Используйте /new для создания нового проекта."
    )

async def next_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /next - переход к следующему шагу"""
    current_step = questionnaire.get_current_step(context)
    
    if current_step == 'files' and not context.user_data.get('files'):
        await update.message.reply_text(
            "⚠️ Сначала загрузите хотя бы один Excel-файл с сметой!"
        )
        return
    
    next_step = questionnaire.next_step(context)
    await update.message.reply_text(
        STEP_MESSAGES[next_step],
        parse_mode='Markdown'
    )

async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /skip - пропуск текущего шага"""
    current_step = questionnaire.get_current_step(context)
    
    # Сохраняем пустое значение для пропущенного шага
    context.user_data[current_step] = ''
    
    next_step = questionnaire.next_step(context)
    await update.message.reply_text(
        f"➡️ Шаг пропущен\n\n{STEP_MESSAGES[next_step]}",
        parse_mode='Markdown'
    )

async def process_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /process - запуск обработки проекта"""
    user_id = update.effective_user.id
    
    if not context.user_data.get('files'):
        await update.message.reply_text(
            "❌ Нет загруженных файлов для обработки!"
        )
        return
    
    # Создаем структуру проекта
    project_path = questionnaire.create_project_structure(user_id)
    context.user_data['project_path'] = project_path
    
    # Копируем загруженные файлы в папку проекта
    import shutil
    for file_info in context.user_data['files']:
        if 'local_path' in file_info and os.path.exists(file_info['local_path']):
            target_path = f"{project_path}/0_input/{file_info['file_name']}"
            shutil.copy2(file_info['local_path'], target_path)
            logger.info(f"Скопирован файл: {file_info['file_name']}")
    
    # Сохраняем директивы
    directives_path = questionnaire.save_directives(context, project_path)
    
    await update.message.reply_text(
        f"🚀 **Запуск обработки...**\n\n"
        f"📁 Проект создан: `{project_path}`\n"
        f"📋 Директивы сохранены: `{directives_path}`\n\n"
        f"⏳ Обработка может занять несколько минут...",
        parse_mode='Markdown'
    )
    
    # Запуск главного пайплайна
    try:
        from ..pipeline_launcher import launch_pipeline
        result = await launch_pipeline(project_path)
        
        if result['success']:
            # Собираем информацию о созданных отчетах
            output_path = f"{project_path}/8_output"
            excel_files = []
            pdf_files = []
            
            if os.path.exists(output_path):
                for file in os.listdir(output_path):
                    if file.endswith('.xlsx'):
                        excel_files.append(file)
                    elif file.endswith('.pdf'):
                        pdf_files.append(file)
            
            # Загружаем краткую информацию из true.json
            summary_info = await _get_project_summary(f"{project_path}/true.json")
            
            # Формируем детальное сообщение
            message_parts = [
                "✅ **ОБРАБОТКА ЗАВЕРШЕНА УСПЕШНО!**",
                "",
                "📊 **РЕЗУЛЬТАТЫ ОБРАБОТКИ:**"
            ]
            
            # Информация о пакетах работ
            if summary_info:
                message_parts.extend([
                    f"📦 Пакетов работ: `{summary_info['packages_count']}`",
                    f"📅 Продолжительность: `{summary_info['duration_weeks']} недель`",
                    f"👥 Пиковая нагрузка: `{summary_info['peak_workers']} человек`"
                ])
            
            message_parts.append("")
            message_parts.append("📋 **СОЗДАННЫЕ ОТЧЕТЫ:**")
            
            # Excel отчеты
            if excel_files:
                for excel_file in excel_files:
                    file_path = f"{output_path}/{excel_file}"
                    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    message_parts.append(f"📄 Excel: `{excel_file}` ({file_size} байт)")
            else:
                message_parts.append("📄 Excel: ❌ Не создан")
            
            # PDF отчеты
            if pdf_files:
                for pdf_file in pdf_files:
                    file_path = f"{output_path}/{pdf_file}"
                    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    message_parts.append(f"📑 PDF: `{pdf_file}` ({file_size} байт)")
            else:
                message_parts.append("📑 PDF: ⚠️ Не создан")
            
            message_parts.extend([
                "",
                f"⏱️ **Время завершения:** {result.get('completed_at', 'N/A')}",
                f"🔧 **Агентов завершено:** `{len(result.get('agents_completed', []))}`"
            ])
            
            await update.message.reply_text(
                "\n".join(message_parts),
                parse_mode='Markdown'
            )
            
            # Отправляем файлы пользователю
            await _send_project_files(update, output_path, excel_files, pdf_files)
        else:
            await update.message.reply_text(
                f"❌ **Ошибка при обработке:**\n\n"
                f"`{result.get('error', 'Неизвестная ошибка')}`",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"💥 Критическая ошибка в пайплайне: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ **Критическая ошибка:**\n\n`{str(e)}`",
            parse_mode='Markdown'
        )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка загруженных файлов"""
    current_step = questionnaire.get_current_step(context)
    
    if current_step != 'files':
        await update.message.reply_text(
            "❌ Сейчас не время для загрузки файлов. Используйте /new для создания нового проекта."
        )
        return
    
    document = update.message.document
    
    if not document.file_name.endswith('.xlsx'):
        await update.message.reply_text(
            "❌ Поддерживаются только Excel-файлы (.xlsx)!"
        )
        return
    
    try:
        # Скачиваем файл из Telegram
        file = await document.get_file()
        
        # Создаем временную папку для пользователя если её нет
        user_id = update.effective_user.id
        temp_path = f"temp_uploads/{user_id}"
        os.makedirs(temp_path, exist_ok=True)
        
        # Сохраняем файл локально
        local_file_path = f"{temp_path}/{document.file_name}"
        await file.download_to_drive(local_file_path)
        
        # Сохраняем информацию о файле
        file_info = {
            'file_name': document.file_name,
            'file_id': document.file_id,
            'file_size': document.file_size,
            'local_path': local_file_path,
            'uploaded_at': datetime.now().isoformat()
        }
        
        if 'files' not in context.user_data:
            context.user_data['files'] = []
        
        context.user_data['files'].append(file_info)
        
        # Отправляем краткое подтверждение без спама
        await update.message.reply_text(f"📁 +{document.file_name}")
        
        # Отправляем общий статус каждые 3 файла или если это первый файл
        if len(context.user_data['files']) == 1 or len(context.user_data['files']) % 3 == 0:
            await update.message.reply_text(
                f"📊 **Загружено файлов: {len(context.user_data['files'])}**\n\n"
                f"Можете добавить еще или использовать /next для продолжения.",
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Ошибка загрузки файла: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при загрузке файла: {str(e)}"
        )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений по шагам опроса"""
    current_step = questionnaire.get_current_step(context)
    text = update.message.text.strip()
    
    if current_step == 'work_count':
        try:
            work_count = int(text)
            if work_count <= 0:
                raise ValueError
            context.user_data['work_count'] = work_count
            next_step = questionnaire.next_step(context)
            await update.message.reply_text(
                f"✅ Количество строк: {work_count}\n\n{STEP_MESSAGES[next_step]}",
                parse_mode='Markdown'
            )
        except ValueError:
            await update.message.reply_text(
                "❌ Введите положительное число (например: 15)"
            )
    
    elif current_step == 'timeline':
        # Улучшенный парсинг дат - принимаем разные разделители
        try:
            # Убираем лишние пробелы и ищем разделители
            clean_text = text.strip()
            
            # Пробуем разные разделители: -, –, —, пробел
            separators = [' - ', '-', ' – ', '–', ' — ', '—', ' ']
            parts = None
            
            for sep in separators:
                if sep in clean_text:
                    temp_parts = clean_text.split(sep)
                    if len(temp_parts) >= 2:
                        parts = [temp_parts[0].strip(), temp_parts[-1].strip()]
                        break
            
            if not parts:
                raise ValueError("Не найдены две даты")
            
            start_date = parts[0]
            end_date = parts[1]
            
            # Проверяем и нормализуем формат дат
            try:
                start_parsed = datetime.strptime(start_date, '%d.%m.%Y')
                start_normalized = start_parsed.strftime('%d.%m.%Y')
            except ValueError:
                raise ValueError(f"Неверная дата начала: {start_date}")
            
            try:
                end_parsed = datetime.strptime(end_date, '%d.%m.%Y')
                end_normalized = end_parsed.strftime('%d.%m.%Y')
            except ValueError:
                raise ValueError(f"Неверная дата окончания: {end_date}")
            
            context.user_data['timeline'] = {
                'start_date': start_normalized,
                'end_date': end_normalized
            }
            
            next_step = questionnaire.next_step(context)
            await update.message.reply_text(
                f"✅ Период: {start_normalized} - {end_normalized}\n\n{STEP_MESSAGES[next_step]}",
                parse_mode='Markdown'
            )
        except (ValueError, IndexError) as e:
            await update.message.reply_text(
                "❌ Проблема с датами! Укажите две даты в формате ДД.ММ.ГГГГ\n"
                "Примеры: `01.01.2024 - 30.06.2024` или `01.01.2024 30.06.2024`\n"
                f"Ошибка: {str(e)}"
            )
    
    elif current_step == 'workforce':
        # Улучшенный парсинг количества рабочих
        try:
            # Убираем все лишнее и ищем числа
            import re
            clean_text = text.strip().replace(' ', '').replace(',', '')
            
            # Ищем паттерны: 10-20, 10–20, 10 20, 10до20, от10до20
            range_patterns = [
                r'(\d+)[-–—](\d+)',
                r'(\d+)\s+(\d+)',
                r'от\s*(\d+)\s*до\s*(\d+)',
                r'(\d+)\s*до\s*(\d+)'
            ]
            
            found_range = False
            for pattern in range_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    min_workers = int(match.group(1))
                    max_workers = int(match.group(2))
                    context.user_data['workforce'] = {
                        'min': min_workers,
                        'max': max_workers
                    }
                    workers_text = f"{min_workers}-{max_workers} человек"
                    found_range = True
                    break
            
            if not found_range:
                # Просто одно число
                workers = int(re.search(r'\d+', text).group())
                context.user_data['workforce'] = {
                    'min': workers,
                    'max': workers
                }
                workers_text = f"{workers} человек"
            
            next_step = questionnaire.next_step(context)
            await update.message.reply_text(
                f"✅ Количество рабочих: {workers_text}\n\n{STEP_MESSAGES[next_step]}",
                parse_mode='Markdown'
            )
        except (ValueError, AttributeError):
            await update.message.reply_text(
                "❌ Укажите количество рабочих!\n"
                "Примеры: `15`, `10-20`, `от 10 до 20`"
            )
    
    elif current_step in ['conceptualizer', 'strategist', 'accountant', 'foreman']:
        # Сохраняем директиву для соответствующего агента
        context.user_data[current_step] = text
        next_step = questionnaire.next_step(context)
        await update.message.reply_text(
            f"✅ Указание сохранено\n\n{STEP_MESSAGES[next_step]}",
            parse_mode='Markdown'
        )
    
    else:
        await update.message.reply_text(
            "❓ Используйте /new для создания нового проекта или /help для справки."
        )

async def _send_project_files(update: Update, output_path: str, excel_files: list, pdf_files: list):
    """Отправляет созданные файлы пользователю"""
    try:
        # Отправляем Excel файлы
        for excel_file in excel_files:
            file_path = f"{output_path}/{excel_file}"
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                await update.message.reply_document(
                    document=open(file_path, 'rb'),
                    filename=excel_file,
                    caption=f"📄 {excel_file}"
                )
            else:
                logger.warning(f"Excel файл не найден или пуст: {file_path}")
        
        # Отправляем PDF файлы  
        for pdf_file in pdf_files:
            file_path = f"{output_path}/{pdf_file}"
            if os.path.exists(file_path) and os.path.getsize(file_path) > 100:  # PDF должен быть больше 100 байт
                await update.message.reply_document(
                    document=open(file_path, 'rb'),
                    filename=pdf_file,
                    caption=f"📑 {pdf_file}"
                )
            else:
                logger.warning(f"PDF файл не найден или слишком маленький: {file_path}")
                
    except Exception as e:
        logger.error(f"Ошибка отправки файлов: {e}")
        await update.message.reply_text(
            f"⚠️ Файлы созданы, но не удалось их отправить: {e}"
        )

async def _get_project_summary(true_json_path: str) -> dict:
    """Извлекает краткую информацию о проекте из true.json"""
    try:
        import json
        
        if not os.path.exists(true_json_path):
            return None
            
        with open(true_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Извлекаем основную информацию
        results = data.get('results', {})
        work_packages = results.get('work_packages', [])
        schedule = results.get('schedule', {})
        staffing = results.get('staffing', {})
        
        return {
            'packages_count': len(work_packages),
            'duration_weeks': schedule.get('project_duration_weeks', 'N/A'),
            'peak_workers': staffing.get('peak_workforce', 'N/A'),
            'total_workers': schedule.get('weekly_workload', {})
        }
        
    except Exception as e:
        logger.warning(f"Не удалось загрузить сводку проекта: {e}")
        return None

# Функция для добавления всех обработчиков
def setup_handlers(application):
    """Настройка всех обработчиков команд"""
    # Команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("new", new_project_command))  
    application.add_handler(CommandHandler("test", test_project_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("next", next_command))
    application.add_handler(CommandHandler("skip", skip_command))
    application.add_handler(CommandHandler("process", process_command))
    
    # Обработчики callback'ов
    application.add_handler(CallbackQueryHandler(handle_test_stage_selection, pattern="^test_stage_"))
    
    # Обработчики сообщений
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))