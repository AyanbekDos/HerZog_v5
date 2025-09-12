#!/usr/bin/env python3
"""
Простой тест кириллицы в PDF через reportlab
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def test_simple_cyrillic_pdf():
    """Простой тест кириллицы"""
    
    output_file = '/tmp/simple_cyrillic_test.pdf'
    
    # Регистрируем шрифт
    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('CyrillicFont', font_path))
        print(f"✅ Шрифт зарегистрирован: {font_path}")
    else:
        print("❌ Шрифт не найден")
        return False
    
    # Создаем PDF
    doc = SimpleDocTemplate(output_file, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Добавляем стиль с кириллическим шрифтом
    styles.add(ParagraphStyle('CyrillicNormal',
                            parent=styles['Normal'],
                            fontName='CyrillicFont',
                            fontSize=12))
    
    story = []
    
    # Тестовый текст с кириллицей
    test_text = """
    <b>Тест кириллицы в PDF</b><br/>
    Демонтаж перегородок<br/>
    Монтаж стяжки пола<br/>
    Устройство чистового покрытия<br/>
    Единица измерения: м²<br/>
    Объем: 150,5 м²
    """
    
    story.append(Paragraph(test_text, styles['CyrillicNormal']))
    
    # Генерируем PDF
    doc.build(story)
    
    if os.path.exists(output_file):
        file_size = os.path.getsize(output_file)
        print(f"✅ PDF создан: {output_file}")
        print(f"📊 Размер: {file_size} байт")
        return True
    else:
        print("❌ PDF не создан")
        return False

if __name__ == "__main__":
    test_simple_cyrillic_pdf()