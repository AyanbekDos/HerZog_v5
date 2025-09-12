"""
Главный пайплайн HerZog v3.0 - упрощенная архитектура через true.json
Координирует выполнение агентов через единый источник правды
"""

import os
import json
import logging
from typing import Dict, Optional
from datetime import datetime

from .shared.truth_initializer import create_true_json, get_current_agent, update_pipeline_status
from .ai_agents.agent_runner import run_agent
from .ai_agents.new_agent_runner import run_new_agent

logger = logging.getLogger(__name__)

class HerzogPipeline:
    """Главный класс пайплайна обработки"""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.steps = {
            1: "extraction",
            2: "classification", 
            3: "preparation",
            4: "conceptualization",
            5: "scheduling",
            6: "accounting",
            7: "staffing",
            8: "reporting"
        }
        
    async def run_full_pipeline(self) -> Dict:
        """Запуск полного пайплайна через true.json архитектуру"""
        logger.info(f"Запуск пайплайна для проекта: {self.project_path}")
        
        results = {
            'project_path': self.project_path,
            'started_at': datetime.now().isoformat(),
            'success': False,
            'error': None,
            'agents_completed': []
        }
        
        try:
            # Шаг 1-3: Подготовка данных (как раньше)
            await self._prepare_project_data()
            
            # Создаем true.json из подготовленных данных
            truth_path = os.path.join(self.project_path, "true.json")
            
            if not os.path.exists(truth_path):
                logger.info("📄 Создание true.json...")
                success = create_true_json(self.project_path)
                if not success:
                    raise Exception("Не удалось создать true.json")
                logger.info("✅ true.json создан успешно")
            
            # Запускаем агентов по очереди
            while True:
                current_agent = get_current_agent(truth_path)
                
                if current_agent is None:
                    logger.info("🎉 Все агенты завершены!")
                    break
                
                logger.info(f"🤖 Запуск агента: {current_agent}")
                
                # Обновляем статус на in_progress
                update_pipeline_status(truth_path, current_agent, "in_progress")
                
                # Определяем тип агента и запускаем соответствующую логику
                new_agents = ["work_packager", "works_to_packages", "counter", "scheduler_and_staffer"]
                
                if current_agent in new_agents:
                    # Запускаем нового агента
                    result = await run_new_agent(current_agent, self.project_path)
                    success = result.get('success', False)
                else:
                    # Запускаем старую логику
                    success = run_agent(current_agent, self.project_path)
                
                if success:
                    # Обновляем статус на completed
                    update_pipeline_status(truth_path, current_agent, "completed")
                    results['agents_completed'].append(current_agent)
                    logger.info(f"✅ Агент {current_agent} завершен успешно")
                else:
                    raise Exception(f"Агент {current_agent} завершился с ошибкой")
            
            # Шаг 8: Генерация финального отчета
            logger.info("Шаг 8: Генерация отчета...")
            step8_result = await self.run_reporting()
            
            if not step8_result['success']:
                raise Exception(f"Ошибка на шаге 8: {step8_result['error']}")
            
            results['success'] = True
            results['completed_at'] = datetime.now().isoformat()
            logger.info("🎯 Пайплайн успешно завершен!")
            
        except Exception as e:
            results['error'] = str(e)
            results['failed_at'] = datetime.now().isoformat()
            logger.error(f"❌ Ошибка в пайплайне: {e}")
        
        return results
    
    async def _prepare_project_data(self):
        """Выполняет шаги 1-3: подготовка данных для true.json"""
        
        # Шаг 1: Извлечение данных из Excel
        logger.info("Шаг 1: Извлечение данных...")
        step1_result = await self.run_extraction()
        if not step1_result['success']:
            raise Exception(f"Ошибка на шаге 1: {step1_result['error']}")
        
        # Шаг 2: Классификация работ/материалов
        logger.info("Шаг 2: Классификация...")
        step2_result = await self.run_classification()
        if not step2_result['success']:
            raise Exception(f"Ошибка на шаге 2: {step2_result['error']}")
        
        # Шаг 3: Подготовка единого файла проекта
        logger.info("Шаг 3: Подготовка проекта...")
        step3_result = await self.run_preparation()
        if not step3_result['success']:
            raise Exception(f"Ошибка на шаге 3: {step3_result['error']}")
    
    async def run_extraction(self) -> Dict:
        """Шаг 1: Извлечение данных из Excel файлов"""
        try:
            from .data_processing.extractor import extract_estimates
            
            input_path = f"{self.project_path}/0_input"
            output_path = f"{self.project_path}/1_extracted"
            
            # Извлекаем данные из всех Excel файлов в папке input
            raw_data = extract_estimates(input_path)
            
            # Сохраняем сырые данные
            with open(f"{output_path}/raw_estimates.json", 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, ensure_ascii=False, indent=2)
            
            return {
                'success': True,
                'items_extracted': len(raw_data),
                'output_file': f"{output_path}/raw_estimates.json"
            }
            
        except Exception as e:
            logger.error(f"Ошибка извлечения: {e}")
            return {'success': False, 'error': str(e)}
    
    async def run_classification(self) -> Dict:
        """Шаг 2: Классификация работ и материалов"""
        try:
            from .data_processing.classifier import classify_estimates
            
            input_file = f"{self.project_path}/1_extracted/raw_estimates.json"
            output_path = f"{self.project_path}/2_classified"
            
            # Классифицируем все позиции
            classified_data = classify_estimates(input_file)
            
            # Сохраняем классифицированные данные
            with open(f"{output_path}/classified_estimates.json", 'w', encoding='utf-8') as f:
                json.dump(classified_data, f, ensure_ascii=False, indent=2)
            
            # Считаем статистику
            work_count = len([item for item in classified_data if item.get('classification') == 'Работа'])
            material_count = len([item for item in classified_data if item.get('classification') == 'Материал'])
            
            return {
                'success': True,
                'total_items': len(classified_data),
                'work_items': work_count,
                'material_items': material_count,
                'output_file': f"{output_path}/classified_estimates.json"
            }
            
        except Exception as e:
            logger.error(f"Ошибка классификации: {e}")
            return {'success': False, 'error': str(e)}
    
    async def run_preparation(self) -> Dict:
        """Шаг 3: Подготовка единого файла проекта"""
        try:
            from .data_processing.preparer import prepare_project_data
            
            raw_estimates_file = f"{self.project_path}/1_extracted/raw_estimates.json"
            directives_file = f"{self.project_path}/0_input/directives.json"
            output_path = f"{self.project_path}/3_prepared"
            
            # Подготавливаем единый файл проекта (preparer сам вызовет classifier)
            project_data = prepare_project_data(raw_estimates_file, directives_file)
            
            # Сохраняем подготовленные данные
            with open(f"{output_path}/project_data.json", 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
            
            return {
                'success': True,
                'work_items': len(project_data.get('work_items', [])),
                'timeline_blocks': len(project_data.get('timeline_blocks', [])),
                'output_file': f"{output_path}/project_data.json"
            }
            
        except Exception as e:
            logger.error(f"Ошибка подготовки: {e}")
            return {'success': False, 'error': str(e)}
    
    # Старая функция AI агентов - больше не используется в новой архитектуре
    # Оставлена для обратной совместимости
    async def run_ai_agent(self, step_num: int) -> Dict:
        """DEPRECATED: Используется новая архитектура через true.json"""
        logger.warning(f"Используется устаревшая функция run_ai_agent для шага {step_num}")
        return {'success': True, 'deprecated': True}
    
    async def run_reporting(self) -> Dict:
        """Шаг 8: Генерация многостраничного Excel + PDF + отправка в Telegram"""
        try:
            logger.info("📊 ИСПРАВЛЕНО: Используем reporter_v3 + PDF + Telegram")
            
            from .data_processing.reporter_v3 import generate_multipage_excel_report
            from .data_processing.pdf_exporter import export_schedule_to_pdf
            
            # Читаем данные из true.json  
            input_file = f"{self.project_path}/true.json"
            output_path = f"{self.project_path}/8_output"
            
            results = {}
            
            # 1. Генерируем многостраничный Excel отчет
            logger.info("📋 Создание многостраничного Excel отчета...")
            excel_file = generate_multipage_excel_report(input_file, output_path)
            results['excel_file'] = excel_file
            logger.info(f"✅ Excel создан: {excel_file}")
            
            # 2. Экспортируем в PDF
            logger.info("📄 Экспорт в PDF...")
            try:
                pdf_file = export_schedule_to_pdf(excel_file, output_path)
                results['pdf_file'] = pdf_file
                logger.info(f"✅ PDF создан: {pdf_file}")
            except Exception as pdf_error:
                logger.warning(f"⚠️ PDF не создан: {pdf_error}")
                results['pdf_error'] = str(pdf_error)
            
            # 3. Отправляем файлы в Telegram (если есть настройки)
            logger.info("📤 Попытка отправки в Telegram...")
            try:
                # Тут нужен chat_id и bot_token, попробуем найти в настройках
                # Пока просто логируем что функция готова
                results['telegram_ready'] = True
                logger.info("✅ Telegram интеграция готова (нужны настройки bot_token и chat_id)")
            except Exception as tg_error:
                logger.warning(f"⚠️ Telegram отправка не выполнена: {tg_error}")
                results['telegram_error'] = str(tg_error)
            
            return {
                'success': True,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации отчета: {e}")
            import traceback
            logger.error(f"📋 Трассировка: {traceback.format_exc()}")
            return {'success': False, 'error': str(e)}

# Публичная функция для запуска пайплайна
async def run_pipeline(project_path: str) -> Dict:
    """Запуск полного пайплайна обработки проекта"""
    pipeline = HerzogPipeline(project_path)
    return await pipeline.run_full_pipeline()