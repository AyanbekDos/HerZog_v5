"""
Claude API клиент через OpenRouter для системы HerZog v3.0
Замена GeminiClient с сохранением совместимости API
"""

import os
import json
import logging
import asyncio
import time
import uuid
import aiohttp
import ast
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class ClaudeClient:
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY не найден в переменных окружения")

        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

        # ВСЕГДА ПРОДАКШЕН РЕЖИМ - убран тестовый режим для предотвращения ошибок
        self.test_mode = False

        # Оптимальное распределение моделей: простые агенты через Claude 3.5, сложные через Sonnet 4
        sonnet_4 = 'anthropic/claude-sonnet-4'
        claude_35 = 'anthropic/claude-3.5-sonnet-20241022'

        self.agent_models = {
            'work_packager': sonnet_4,        # Сложная группировка → Sonnet 4
            'works_to_packages': claude_35,   # Простое присвоение → Claude 3.5
            'counter': claude_35,             # Простые расчеты → Claude 3.5
            'scheduler_and_staffer': sonnet_4, # Сложное планирование → Sonnet 4
            'classifier': claude_35           # Простая классификация → Claude 3.5
        }
        default_model = sonnet_4  # По умолчанию Sonnet 4

        # Дефолтная модель для обратной совместимости
        self.model_name = default_model

        # Статистика использования для мониторинга
        self.usage_stats = {
            'total_requests': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'estimated_cost': 0.0
        }

    def get_model_for_agent(self, agent_name: str) -> str:
        """Получает имя модели для конкретного агента"""
        return self.agent_models.get(agent_name, self.model_name)

    async def generate_response(self, prompt: str, max_retries: int = 5, agent_name: str = None, system_instruction: Optional[str] = None) -> Dict[str, Any]:
        """
        Отправка запроса в Claude через OpenRouter API

        Args:
            prompt: Пользовательский промт (данные)
            max_retries: Максимальное количество попыток при ошибке
            agent_name: Имя агента для выбора оптимальной модели
            system_instruction: Системная инструкция (статические правила и шаблоны)

        Returns:
            Словарь с ответом и метаданными (совместимый с GeminiClient)
        """
        # Выбираем модель для агента
        model_name = self.get_model_for_agent(agent_name) if agent_name else self.model_name

        # Всегда используем продакшн лимиты токенов
        max_tokens = 8000  # Разумный лимит для выходных токенов

        # Формируем сообщения для Claude API
        messages = []

        if system_instruction:
            messages.append({
                "role": "system",
                "content": system_instruction
            })

        messages.append({
            "role": "user",
            "content": prompt
        })

        # Подготавливаем payload для OpenRouter
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.3,
            "top_p": 0.8,
            "max_tokens": max_tokens,
            "stream": False,
            "provider": {
                "allow_fallbacks": False  # Принудительно используем именно запрошенную модель
            },
            "usage": {
                "include": True  # Включаем детальную информацию об использовании
            }
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/imort/Herzog_v3",  # Для OpenRouter статистики
            "X-Title": "Herzog v3.0 AI Pipeline"
        }

        for attempt in range(max_retries):
            try:
                logger.info(f"📡 Claude запрос {attempt + 1}/{max_retries}: {model_name} {f'({agent_name})' if agent_name else ''} (промт: {len(prompt)} символов, лимит токенов: {max_tokens})")

                async with aiohttp.ClientSession() as session:
                    async with session.post(self.base_url, json=payload, headers=headers) as response:
                        response_data = await response.json()

                        if response.status == 200:
                            # Успешный ответ
                            choice = response_data.get('choices', [{}])[0]
                            message = choice.get('message', {})
                            content = message.get('content', '')

                            # Обновляем статистику
                            usage = response_data.get('usage', {})
                            input_tokens = usage.get('prompt_tokens', 0)
                            output_tokens = usage.get('completion_tokens', 0)
                            total_tokens = usage.get('total_tokens', input_tokens + output_tokens)

                            # Проверяем какая модель реально использовалась
                            actual_model = usage.get('model', model_name)
                            if actual_model != model_name:
                                logger.warning(f"⚠️  Запрошена {model_name}, но использована {actual_model}")
                            else:
                                logger.info(f"✅ Подтверждено использование модели: {actual_model}")

                            self.usage_stats['total_requests'] += 1
                            self.usage_stats['total_input_tokens'] += input_tokens
                            self.usage_stats['total_output_tokens'] += output_tokens

                            # Реальная стоимость для Claude через OpenRouter (anthropic/claude-sonnet-4 → 3.5 Sonnet)
                            input_cost = input_tokens * 0.000003  # $0.000003 за токен (из OpenRouter документации)
                            output_cost = output_tokens * 0.000015  # $0.000015 за токен
                            estimated_cost = input_cost + output_cost
                            self.usage_stats['estimated_cost'] += estimated_cost

                            # Парсим JSON ответ
                            try:
                                cleaned_content = self._clean_json_from_markdown(content)
                                response_json = self._try_fix_broken_json(cleaned_content)
                                json_parse_success = True
                            except (json.JSONDecodeError, SyntaxError, ValueError) as e:
                                logger.error(f"❌ Ошибка парсинга JSON от Claude: {e}")

                                if attempt < max_retries - 1:
                                    logger.info(f"🔄 Повторная попытка из-за невалидного JSON (попытка {attempt + 2}/{max_retries})")
                                    await asyncio.sleep(1 + attempt)
                                    continue
                                else:
                                    return {
                                        'success': False,
                                        'error': f'JSON парсинг не удался после {max_retries} попыток: {e}',
                                        'response': None,
                                        'raw_text': content
                                    }

                            result = {
                                'success': True,
                                'response': response_json,
                                'json_parse_success': json_parse_success,
                                'raw_text': content,
                                'model_used': model_name,
                                'agent_name': agent_name,
                                'usage_metadata': {
                                    'prompt_token_count': input_tokens,
                                    'candidates_token_count': output_tokens,
                                    'total_token_count': total_tokens
                                },
                                'attempt': attempt + 1,
                                'llm_input': prompt,
                                'estimated_cost': estimated_cost
                            }

                            logger.info(f"✅ Успешный ответ от Claude {model_name} {f'({agent_name})' if agent_name else ''} за {attempt + 1} попытку")
                            logger.info(f"💰 Токены: {total_tokens} (~${estimated_cost:.4f}), Общая стоимость сессии: ~${self.usage_stats['estimated_cost']:.4f}")

                            return result

                        elif response.status == 429:
                            # Rate limiting - переключаемся на Claude 3.5 для экономии времени
                            if model_name == 'anthropic/claude-sonnet-4' and attempt == 0:
                                logger.warning(f"⏰ 429 Rate Limit на Sonnet 4! Переключаюсь на Claude 3.5")
                                model_name = 'anthropic/claude-3.5-sonnet-20241022'
                                payload["model"] = model_name
                                continue

                            retry_after = response.headers.get('retry-after', '60')
                            retry_delay = min(int(retry_after), 10)  # Максимум 10 сек

                            if attempt < max_retries - 1:
                                logger.warning(f"⏰ 429 Rate Limit! Ждем {retry_delay} секунд перед попыткой {attempt + 2}...")
                                await asyncio.sleep(retry_delay)
                                continue
                            else:
                                logger.error(f"❌ Превышено максимальное количество попыток ({max_retries}) для rate limit")

                        else:
                            # Другие HTTP ошибки
                            error_msg = response_data.get('error', {}).get('message', f'HTTP {response.status}')
                            logger.error(f"❌ Claude API ошибка: {error_msg}")

                            if attempt == max_retries - 1:
                                return {
                                    'success': False,
                                    'error': f'Claude API error: {error_msg}',
                                    'response': None,
                                    'attempts': max_retries
                                }

                            await asyncio.sleep(1 + attempt)

            except Exception as e:
                logger.error(f"❌ Ошибка при обращении к Claude API (попытка {attempt + 1}): {e}")

                if attempt == max_retries - 1:
                    return {
                        'success': False,
                        'error': str(e),
                        'response': None,
                        'attempts': max_retries
                    }

                await asyncio.sleep(1 + attempt)

        return {
            'success': False,
            'error': "Unexpected error: exhausted all retries",
            'response': None
        }

    def _clean_json_from_markdown(self, text: str) -> str:
        """
        Очищает JSON от markdown обертки и текста, которую может добавлять Claude
        """
        import re

        text = text.strip()

        # Удаляем markdown блоки типа ```json ... ```
        markdown_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
        match = re.search(markdown_pattern, text, re.DOTALL | re.IGNORECASE)

        if match:
            cleaned = match.group(1).strip()
            return cleaned

        # Ищем JSON блок - от первой { до соответствующей }
        first_brace = text.find('{')
        if first_brace != -1:
            json_part = text[first_brace:]

            # Считаем вложенность скобок для правильного выделения JSON
            brace_count = 0
            end_pos = -1

            for i, char in enumerate(json_part):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i
                        break

            if end_pos != -1:
                return json_part[:end_pos+1].strip()

        # Ищем массив JSON - от первой [ до соответствующей ]
        first_bracket = text.find('[')
        if first_bracket != -1:
            json_part = text[first_bracket:]

            bracket_count = 0
            end_pos = -1

            for i, char in enumerate(json_part):
                if char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_pos = i
                        break

            if end_pos != -1:
                return json_part[:end_pos+1].strip()

        return text

    def _try_fix_broken_json(self, text: str):
        """
        Более надежный парсинг JSON, который пытается исправить частые ошибки LLM.
        1. Пробует стандартный json.loads
        2. Если не удалось, пробует ast.literal_eval для исправления кавычек
        3. Если и это не удалось, пробует заменять \n и другие проблемные символы
        """
        import re

        # Сначала попробуем стандартный парсинг
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("⚠️ Стандартный json.loads не удался, пробуем ast.literal_eval")

        # Попытка 2: использовать ast.literal_eval для обработки Python-like синтаксиса (например, одинарные кавычки)
        try:
            evaluated = ast.literal_eval(text)
            # Если удалось, конвертируем обратно в валидный JSON-объект
            return json.loads(json.dumps(evaluated))
        except (ValueError, SyntaxError, MemoryError, TypeError):
            logger.warning("⚠️ ast.literal_eval не удался, пробуем очистку текста")

        # Попытка 3: Очистка управляющих символов и новых строк
        cleaned_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            # Заменяем неэкранированные переносы строк внутри строковых значений
            cleaned_text = re.sub(r'\n', r'\\n', cleaned_text)
            try:
                return json.loads(cleaned_text)
            except json.JSONDecodeError:
                # Последняя попытка - удаляем все переносы строк
                cleaned_text = cleaned_text.replace('\n', ' ').replace('\r', ' ')
                return json.loads(cleaned_text) # Если и тут ошибка, то она пробросится наверх

    def get_usage_stats(self) -> Dict[str, Any]:
        """Возвращает статистику использования API"""
        return self.usage_stats.copy()

    def reset_usage_stats(self):
        """Сбрасывает статистику использования"""
        self.usage_stats = {
            'total_requests': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'estimated_cost': 0.0
        }

# Глобальный экземпляр клиента
claude_client = ClaudeClient()
