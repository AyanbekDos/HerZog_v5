"""
Мок-клиент для тестирования без реальных вызовов Gemini API
"""

import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MockGeminiClient:
    """
    Мок-клиент, который имитирует ответы Gemini API для тестирования
    """
    
    def __init__(self):
        self.call_count = 0
        
    async def generate_response(self, prompt: str) -> Dict[str, Any]:
        """
        Имитирует ответ Gemini API с тестовыми данными
        """
        self.call_count += 1
        
        logger.info(f"🤖 MockGemini вызов #{self.call_count}, промт: {len(prompt)} символов")
        
        # Определяем тип запроса по промпту для генерации соответствующего ответа
        if "work_packages" in prompt and "package_id" in prompt:
            # Это work_packager
            mock_response = {
                "work_packages": [
                    {
                        "package_id": "pkg_001",
                        "name": "Демонтаж конструкций",
                        "description": "Снос перегородок, демонтаж покрытий пола и потолка"
                    },
                    {
                        "package_id": "pkg_002", 
                        "name": "Электромонтажные работы",
                        "description": "Прокладка кабелей, установка розеток и выключателей"
                    },
                    {
                        "package_id": "pkg_003",
                        "name": "Отделочные работы стен",
                        "description": "Штукатурка и покраска стен помещений"
                    },
                    {
                        "package_id": "pkg_004",
                        "name": "Устройство полов",
                        "description": "Стяжка и укладка напольных покрытий"
                    },
                    {
                        "package_id": "pkg_005",
                        "name": "Работы по потолкам",
                        "description": "Монтаж подвесных и натяжных потолков"
                    },
                    {
                        "package_id": "pkg_006",
                        "name": "Сантехнические работы",
                        "description": "Прокладка труб и установка сантехники"
                    }
                ]
            }
            
        elif "assignments" in prompt and "work_id" in prompt:
            # Это works_to_packages
            mock_response = {
                "assignments": [
                    {"work_id": "work_001", "package_id": "pkg_001"},
                    {"work_id": "work_002", "package_id": "pkg_001"}, 
                    {"work_id": "work_003", "package_id": "pkg_002"},
                    {"work_id": "work_004", "package_id": "pkg_002"},
                    {"work_id": "work_005", "package_id": "pkg_002"},
                    {"work_id": "work_006", "package_id": "pkg_003"},
                    {"work_id": "work_007", "package_id": "pkg_003"},
                    {"work_id": "work_008", "package_id": "pkg_004"},
                    {"work_id": "work_009", "package_id": "pkg_004"},
                    {"work_id": "work_010", "package_id": "pkg_005"},
                    {"work_id": "work_011", "package_id": "pkg_006"},
                    {"work_id": "work_012", "package_id": "pkg_006"}
                ]
            }
            
        elif "calculation" in prompt and "final_unit" in prompt:
            # Это counter  
            mock_response = {
                "calculation": {
                    "final_unit": "м²",
                    "final_quantity": 120.0,
                    "calculation_logic": "Применено правило максимума для площадных работ",
                    "component_analysis": [
                        {
                            "work_name": "Демонтаж перегородок",
                            "unit": "м²", 
                            "quantity": 80.0,
                            "included": "full",
                            "role": "base_surface"
                        }
                    ]
                }
            }
            
        elif "scheduled_packages" in prompt and "schedule_blocks" in prompt:
            # Это scheduler_and_staffer
            mock_response = {
                "scheduled_packages": [
                    {
                        "package_id": "pkg_001",
                        "name": "Демонтаж конструкций",
                        "calculations": {"unit": "м²", "quantity": 100.0},
                        "schedule_blocks": [1, 2],
                        "progress_per_block": {"1": 60, "2": 40},
                        "staffing_per_block": {"1": 8, "2": 6}
                    },
                    {
                        "package_id": "pkg_002",
                        "name": "Электромонтажные работы", 
                        "calculations": {"unit": "м", "quantity": 200.0},
                        "schedule_blocks": [3, 4],
                        "progress_per_block": {"3": 70, "4": 30},
                        "staffing_per_block": {"3": 4, "4": 3}
                    }
                ]
            }
            
        else:
            # Общий ответ по умолчанию
            mock_response = {
                "result": "mock_response",
                "message": "Тестовый ответ от MockGemini"
            }
        
        return {
            'success': True,
            'response': mock_response,
            'json_parse_success': True,
            'raw_text': json.dumps(mock_response, ensure_ascii=False),
            'prompt_feedback': None,
            'usage_metadata': {
                'prompt_token_count': len(prompt) // 4,  # Примерная оценка
                'candidates_token_count': 100,
                'total_token_count': len(prompt) // 4 + 100
            }
        }

# Глобальный мок-экземпляр для тестов
mock_gemini_client = MockGeminiClient()