"""Generate offline PDF study notes locally (no OpenAI calls)."""
from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from io import BytesIO

from weasyprint import HTML


def _safe(value) -> str:
    return escape(str(value or ""), quote=True).replace("\n", "<br>")


def _paragraph(label: str, value) -> str:
    if not value:
        return ""
    return f'<section><h2>{escape(label)}</h2><p>{_safe(value)}</p></section>'


def make_study_notes_pdf(source: str, direction: str, languages: list[str], data: dict,
                         include_words: bool = True, include_grammar: bool = True,
                         include_sandhi: bool = True) -> bytes:
    """Return printable PDF bytes; never contacts external services or saves user content."""
    if not isinstance(data, dict):
        raise ValueError("A completed translation is required.")
    if not source.strip():
        raise ValueError("The source text is empty.")
    pieces = [
        '<h1>Sanskritam AI <span>· Study Notes</span></h1>',
        '<p class="subtitle">Ancient Wisdom. Modern Intelligence. · Offline learning copy</p>',
        f'<p class="meta">Created {datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")} · {_safe(direction)}</p>',
        _paragraph('Original passage', source),
        _paragraph('Natural translation', data.get('natural_translation')),
    ]
    translations = data.get('translations') or {}
    if isinstance(translations, dict):
        for lang in languages:
            if lang in translations and translations[lang]:
                pieces.append(_paragraph(f'{lang} translation', translations[lang]))
    pieces.append(_paragraph('Literal translation', data.get('literal_translation')))
    if include_words:
        rows=[]
        for item in (data.get('words') or [])[:100]:
            if not isinstance(item, dict):
                continue
            gram = ', '.join(str(item.get(k) or '') for k in ('part_of_speech','grammar') if item.get(k))
            rows.append('<tr><td>'+_safe(item.get('word'))+'</td><td>'+_safe(item.get('meaning'))+'</td><td>'+_safe(gram)+'</td></tr>')
        if rows:
            pieces.append('<section><h2>Word-by-word analysis</h2><table><thead><tr><th>Word</th><th>Meaning</th><th>Grammar</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></section>')
    if include_grammar:
        pieces.append(_paragraph('Grammar explained', data.get('grammar_explanation')))
    if include_sandhi:
        pieces.append(_paragraph('Sandhi & compounds', data.get('sandhi_explanation')))
    pieces.append('<p class="disclaimer">Learning aid: AI-generated translations and grammatical explanations may contain errors. Verify important passages against authoritative sources.</p>')
    css = """@page {size:A4;margin:18mm 17mm 20mm; @bottom-center {content:"Sanskritam AI · " counter(page); color:#52655b;font-size:9pt}}
    body{font-family:"Noto Sans","Noto Sans Devanagari","Noto Sans Tamil","Noto Sans Telugu","Noto Sans Bengali","Noto Sans Gujarati","Noto Sans Kannada","Noto Sans Malayalam",sans-serif;color:#213c2f;font-size:10.5pt;line-height:1.65}
    h1{font-size:23pt;color:#17533c;margin:0} h1 span{font-size:15pt;color:#a5762c}
    .subtitle{margin:0;color:#8b6428}.meta{font-size:9pt;color:#617067;border-bottom:2px solid #c7a26a;padding-bottom:12px}
    h2{font-size:13pt;color:#18543e;margin:18px 0 6px} section{break-inside:avoid-page}p{margin:5px 0 10px;white-space:normal;overflow-wrap:anywhere}
    table{width:100%;border-collapse:collapse;table-layout:fixed}th,td{border:1px solid #d8dfd7;padding:7px;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:#edf4ee;color:#184632}tr{break-inside:avoid}
    .disclaimer{margin-top:24px;border-top:1px solid #c6d2c7;padding-top:10px;font-size:9pt;color:#58675e}
    """
    doc = '<!doctype html><html><head><meta charset="utf-8"><style>'+css+'</style></head><body>'+''.join(pieces)+'</body></html>'
    output = BytesIO()
    HTML(string=doc).write_pdf(target=output)
    return output.getvalue()
