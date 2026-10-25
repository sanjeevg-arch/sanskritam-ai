"""Portable offline PDF study notes using Pillow + ReportLab.

Text is drawn as images to preserve Indic shaping without WeasyPrint's
Pango/GObject system libraries. PDF text is therefore not selectable.
"""
from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont, features
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

SCRIPTS = {
    'Devanagari': (0x0900, 0x097F), 'Bengali': (0x0980, 0x09FF),
    'Gujarati': (0x0A80, 0x0AFF), 'Tamil': (0x0B80, 0x0BFF),
    'Telugu': (0x0C00, 0x0C7F), 'Kannada': (0x0C80, 0x0CFF),
    'Malayalam': (0x0D00, 0x0D7F),
}
FONT_DIRS = [Path('/usr/share/fonts/truetype/noto'), Path('/usr/share/fonts/truetype/dejavu'),
             Path('/usr/local/share/fonts'), Path(__file__).resolve().parent / 'fonts']


def _font_path(script: str) -> str:
    names = ([f'NotoSans{script}-Regular.ttf'] if script != 'Latin'
             else ['NotoSans-Regular.ttf', 'DejaVuSans.ttf'])
    for directory in FONT_DIRS:
        for name in names:
            candidate = directory / name
            if candidate.is_file():
                return str(candidate)
    raise RuntimeError('Required Noto fonts are missing. Install fonts-noto-core via packages.txt.')


def _script(character: str) -> str:
    cp = ord(character)
    for name, (start, end) in SCRIPTS.items():
        if start <= cp <= end:
            return name
    return 'Latin'


def _runs(text: str):
    """Keep combining marks and punctuation with the preceding script."""
    result = []
    for ch in text:
        script = _script(ch)
        if script == 'Latin' and result and (ch.isspace() or not ch.isalpha()):
            script = result[-1][0]
        if result and result[-1][0] == script:
            result[-1] = (script, result[-1][1] + ch)
        else:
            result.append((script, ch))
    return result


def make_study_notes_pdf(source: str, direction: str, languages: list[str], data: dict,
                         include_words: bool = True, include_grammar: bool = True,
                         include_sandhi: bool = True) -> bytes:
    if not isinstance(data, dict) or not source or not source.strip():
        raise ValueError('A completed translation is required.')
    if not features.check('raqm'):
        raise RuntimeError('Pillow was built without RAQM text shaping support.')

    # A4 at approximately 125 dpi. Multi-page, with generous margins.
    W, H = 1034, 1462
    left, right, top, bottom = 82, 82, 90, 85
    max_width = W - left - right
    pages = []
    page = Image.new('RGB', (W, H), '#fffdf8')
    draw = ImageDraw.Draw(page)
    y = top
    fonts = {}

    def font(script, size):
        key = (script, size)
        if key not in fonts:
            fonts[key] = ImageFont.truetype(_font_path(script), size,
                                           layout_engine=ImageFont.Layout.RAQM)
        return fonts[key]

    def draw_line(line, size, color, line_height):
        nonlocal y, page, draw
        if y + line_height > H - bottom:
            pages.append(page)
            page = Image.new('RGB', (W, H), '#fffdf8')
            draw = ImageDraw.Draw(page)
            y = top
        x = left
        for script, part in _runs(line):
            f = font(script, size)
            draw.text((x, y), part, font=f, fill=color, anchor='lt')
            x += draw.textlength(part, font=f)
        y += line_height

    def width(s, size):
        return sum(draw.textlength(part, font=font(script, size)) for script, part in _runs(s))

    def paragraph(value, size=24, color='#243c30'):
        nonlocal y
        text = str(value or '').replace('\r', '')
        for para in text.split('\n'):
            if not para.strip():
                y += 12
                continue
            words = re.findall(r'\S+\s*', para)
            line = ''
            for word in words:
                if width(line + word, size) <= max_width:
                    line += word
                    continue
                if line.strip():
                    draw_line(line.rstrip(), size, color, int(size * 1.65))
                    line = ''
                # Long unspaced strings must still wrap within page margins.
                for char in word:
                    if line and width(line + char, size) > max_width:
                        draw_line(line.rstrip(), size, color, int(size * 1.65))
                        line = ''
                    line += char
            if line.strip():
                draw_line(line.rstrip(), size, color, int(size * 1.65))
        y += 10

    def section(label, value):
        nonlocal y
        if value is None or str(value).strip() == '':
            return
        y += 15
        paragraph(label, 28, '#18533c')
        paragraph(value)

    paragraph('Sanskritam AI - Study Notes', 37, '#17533c')
    paragraph('Ancient Wisdom. Modern Intelligence. | Offline learning copy', 20, '#9b6d29')
    paragraph(datetime.now(timezone.utc).strftime('Created %d %B %Y, %H:%M UTC') + ' | ' + str(direction), 18, '#52655b')
    section('Original passage', source)
    section('Natural translation', data.get('natural_translation'))
    translations = data.get('translations') or {}
    if isinstance(translations, dict):
        for lang in languages or []:
            if translations.get(lang):
                section(f'{lang} translation', translations[lang])
    section('Literal translation', data.get('literal_translation'))
    if include_words:
        words = [x for x in (data.get('words') or [])[:100] if isinstance(x, dict)]
        if words:
            section('Word-by-word analysis', ' ')
            for item in words:
                gram = ', '.join(str(item.get(k)) for k in ('part_of_speech', 'grammar') if item.get(k))
                paragraph(f"{item.get('word', '')}  -  {item.get('meaning', '')}  |  {gram}", 22)
    if include_grammar:
        section('Grammar explained', data.get('grammar_explanation'))
    if include_sandhi:
        section('Sandhi & compounds', data.get('sandhi_explanation'))
    section('Study reminder', 'AI-generated translations and grammatical explanations may contain errors. Verify important passages against authoritative sources.')
    pages.append(page)

    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=A4, pageCompression=1)
    for i, image in enumerate(pages, 1):
        img_buf = BytesIO()
        image.save(img_buf, format='PNG', optimize=True)
        img_buf.seek(0)
        pdf.drawImage(ImageReader(img_buf), 0, 0, width=A4[0], height=A4[1])
        pdf.setFont('Helvetica', 8)
        pdf.setFillColorRGB(.25, .35, .29)
        pdf.drawCentredString(A4[0] / 2, 20, f'Sanskritam AI | Page {i} of {len(pages)}')
        pdf.showPage()
    pdf.save()
    return output.getvalue()
