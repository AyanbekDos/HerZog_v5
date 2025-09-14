"""
Общий клиент для работы с Gemini API
"""

import os
import json
import logging
import asyncio
import time
import uuid
import google.generativeai as genai
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY не найден в переменных окружения")
        
        genai.configure(api_key=self.api_key)
        
        # Модели для разных агентов с учетом их задач и оптимизации токенов
        self.agent_models = {
            'work_packager': 'gemini-2.5-pro',        # Сложное группирование работ - нужны мощности
            'works_to_packages': 'gemini-2.5-flash-lite',  # Простое назначение - экономим токены
            'counter': 'gemini-2.5-flash-lite',       # Подсчеты - быстро и дешево
            'scheduler_and_staffer': 'gemini-2.5-pro', # Сложное планирование - нужны мощности
            'classifier': 'gemini-2.5-flash-lite'     # Классификация работ - быстро и дешево
        }
        
        # Кэш моделей для избежания пересозданий
        self._model_cache = {}
        
        # Дефолтная модель для обратной совместимости
        self.model = self._get_model('gemini-2.5-pro')

    
    def _get_model(self, model_name: str):
        """Получает модель из кэша или создает новую"""
        if model_name not in self._model_cache:
            self._model_cache[model_name] = genai.GenerativeModel(model_name)
            logger.info(f"📋 Создана модель: {model_name}")
        return self._model_cache[model_name]
    
    def get_model_for_agent(self, agent_name: str):
        """Получает оптимальную модель для конкретного агента"""
        model_name = self.agent_models.get(agent_name, 'gemini-2.5-pro')
        return self._get_model(model_name)
        
    async def generate_response(self, prompt: str, max_retries: int = 5, agent_name: str = None, system_instruction: Optional[str] = None) -> Dict[str, Any]:
        """
        Отправка запроса в Gemini и получение ответа с retry логикой

        Args:
            prompt: Пользовательский промт (данные)
            max_retries: Максимальное количество попыток при 429 ошибке
            agent_name: Имя агента для выбора оптимальной модели
            system_instruction: Системная инструкция (статические правила и шаблоны)

        Returns:
            Словарь с ответом и метаданными
        """
        # Выбираем модель для агента или используем дефолтную
        if agent_name and agent_name in self.agent_models:
            model_name = self.agent_models[agent_name]
        else:
            model_name = 'gemini-2.5-pro'

        # Если есть system_instruction, создаем новую модель с системной инструкцией
        if system_instruction:
            model = genai.GenerativeModel(model_name, system_instruction=system_instruction)
            logger.info(f"🧠 Создана модель с системной инструкцией: {model_name}")
        else:
            # Используем кэшированные модели
            if agent_name and agent_name in self.agent_models:
                model = self.get_model_for_agent(agent_name)
            else:
                model = self.model

        for attempt in range(max_retries):
            try:
                logger.info(f"📡 Попытка {attempt + 1}/{max_retries}: {model_name} {f'({agent_name})' if agent_name else ''} (промт: {len(prompt)} символов)")
                
                # Динамически выбираем лимит токенов в зависимости от агента
                if agent_name == 'work_packager':
                    max_tokens = 8000
                elif agent_name == 'counter':
                    max_tokens = 8000  # Counter генерирует очень большие ответы
                else:
                    max_tokens = 4000
                    
                
                response = await model.generate_content_async(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        top_p=0.8,
                        max_output_tokens=max_tokens,
                        response_mime_type="application/json"
                    )
                )
                
                # Проверяем наличие ответа от API
                if not response.candidates:
                    logger.warning(f"⚠️ Пустой ответ от Gemini API")
                    if response.prompt_feedback:
                        feedback_reason = getattr(response.prompt_feedback, 'block_reason', 'UNKNOWN')
                        logger.warning(f"⚠️ Причина блокировки: {feedback_reason}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 + attempt)
                        continue
                    else:
                        raise Exception("API вернул пустой ответ после всех попыток")

                # Проверяем finish_reason для критических ошибок
                finish_reason = getattr(response.candidates[0], 'finish_reason', None)

                if finish_reason == 2:  # RECITATION - контент заблокирован
                    raise Exception(f"Контент заблокирован Gemini из-за RECITATION")

                if finish_reason == 3:  # SAFETY - заблокировано из-за безопасности
                    raise Exception("Контент заблокирован Gemini из-за политики безопасности")
                
                # Пытаемся получить текст ответа
                try:
                    response_text = response.text
                except Exception as text_error:
                    logger.warning(f"⚠️ Не удалось получить response.text: {text_error}")
                    if finish_reason == 4:  # MAX_TOKENS - ответ обрезан
                        logger.warning("⚠️ Ответ обрезан из-за лимита токенов. Увеличиваю лимит...")
                        # Повторяем с увеличенным лимитом токенов
                        if attempt < max_retries - 1:
                            continue
                    raise Exception(f"Не удалось получить ответ от Gemini: {text_error}")
                
                # Парсим JSON ответ с учетом markdown обертки
                try:
                    cleaned_text = self._clean_json_from_markdown(response_text)
                    response_json = self._try_fix_broken_json(cleaned_text)
                    json_parse_success = True
                except json.JSONDecodeError as e:
                    logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА парсинга JSON от Gemini: {e}")

                    # JSONDecodeError считается неуспешной попыткой - ретраим
                    if attempt < max_retries - 1:
                        logger.info(f"🔄 Повторная попытка из-за невалидного JSON (попытка {attempt + 2}/{max_retries})")
                        await asyncio.sleep(1 + attempt)
                        continue
                    else:
                        # На последней попытке возвращаем ошибку
                        return {
                            'success': False,
                            'error': f'JSON парсинг не удался после {max_retries} попыток: {e}',
                            'response': None,
                            'raw_text': response_text
                        }
                
                result = {
                    'success': True,
                    'response': response_json,
                    'json_parse_success': json_parse_success,
                    'raw_text': response_text,
                    'model_used': model_name,
                    'agent_name': agent_name,
                    'prompt_feedback': str(response.prompt_feedback) if response.prompt_feedback else None,
                    'usage_metadata': {
                        'prompt_token_count': getattr(response.usage_metadata, 'prompt_token_count', 0),
                        'candidates_token_count': getattr(response.usage_metadata, 'candidates_token_count', 0),
                        'total_token_count': getattr(response.usage_metadata, 'total_token_count', 0)
                    },
                    'attempt': attempt + 1,
                    'llm_input': prompt  # Сохраняем отправленный промпт
                }
                
                logger.info(f"✅ Успешный ответ от {model_name} {f'({agent_name})' if agent_name else ''} за {attempt + 1} попытку, токенов: {result['usage_metadata']['total_token_count']}")
                return result
                
            except Exception as e:
                error_str = str(e)
                
                # Проверяем на 429 ошибку (rate limiting)
                if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                    # Извлекаем задержку из ошибки если есть
                    retry_delay = self._extract_retry_delay(error_str)
                    if retry_delay is None:
                        # Экспоненциальный backoff: 2^attempt секунд
                        retry_delay = 2 ** attempt
                    
                    if attempt < max_retries - 1:  # Не последняя попытка
                        logger.warning(f"⏰ 429 Rate Limit! Ждем {retry_delay} секунд перед попыткой {attempt + 2}...")
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"❌ Превышено максимальное количество попыток ({max_retries}) для rate limit")
                
                # Другие ошибки или последняя попытка
                logger.error(f"❌ Ошибка при обращении к Gemini (попытка {attempt + 1}): {e}")
                
                if attempt == max_retries - 1:  # Последняя попытка
                    return {
                        'success': False,
                        'error': error_str,
                        'response': None,
                        'attempts': max_retries
                    }
                
                # Небольшая задержка между обычными попытками
                await asyncio.sleep(1)
        
        # Никогда не должно дойти сюда, но на всякий случай
        return {
            'success': False,
            'error': "Unexpected error: exhausted all retries",
            'response': None
        }
    
    def _extract_retry_delay(self, error_str: str) -> Optional[int]:
        """Извлекает рекомендуемую задержку из ошибки 429"""
        import re
        
        # Ищем "retry_delay {\n  seconds: 44\n}"
        match = re.search(r'retry_delay\s*\{\s*seconds:\s*(\d+)', error_str)
        if match:
            return int(match.group(1))
        
        return None
    
    def _clean_json_from_markdown(self, text: str) -> str:
        """
        Очищает JSON от markdown обертки, которую часто добавляет Gemini
        
        Args:
            text: Сырой ответ от Gemini
            
        Returns:
            Очищенный JSON текст
        """
        import re
        
        # Удаляем markdown блоки типа ```json ... ```
        # Ищем паттерн: ```json или ``` в начале, затем JSON, затем ``` в конце
        markdown_pattern = r'^```(?:json)?\s*\n?(.*?)\n?```\s*$'
        match = re.search(markdown_pattern, text.strip(), re.DOTALL | re.IGNORECASE)
        
        if match:
            # Извлекаем содержимое между ```
            cleaned = match.group(1).strip()
            return cleaned
        
        # Если markdown не найден, возвращаем как есть
        return text.strip()
    
    def _try_fix_broken_json(self, text: str):
        """
        Парсинг JSON с очисткой управляющих символов

        Args:
            text: JSON текст

        Returns:
            Распарсенный объект JSON
        """
        import re

        # Удаляем управляющие символы, которые ломают JSON
        # Разрешенные управляющие символы: \n, \r, \t, \", \\
        cleaned_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

        # Пытаемся парсить как есть
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            # Если не получается, пробуем более агрессивную очистку
            # Заменяем неэкранированные переносы строк внутри строковых значений на \\n
            # Только внутри значений, а не в структуре JSON
            cleaned_text = re.sub(r'(?<="[^"]*)\n(?=[^"]*"[,}\]])', '\\\\n', cleaned_text)
            return json.loads(cleaned_text)

# Глобальный экземпляр клиента
gemini_client = GeminiClient()