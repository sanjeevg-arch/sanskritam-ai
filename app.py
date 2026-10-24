"""Sanskritam AI v1.1 — beginner-friendly Streamlit hackathon app."""
import json
import html
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from reference import lookup, compare_words
from feedback import save_feedback

load_dotenv()
BASE = Path(__file__).parent
st.set_page_config(page_title="Sanskritam AI | Translate & Learn", page_icon="🪷", layout="wide")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Noto+Sans+Devanagari:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap');
:root{--green:#154832;--gold:#9b6014;--blue:#174e91;--purple:#6a267d;--ink:#25372f}
.stApp{background:linear-gradient(165deg,#fff6e4,#fffdf8 42%,#f0f6f2);color:var(--ink);font-family:'DM Sans',sans-serif}
.block-container{max-width:1180px;padding-top:1rem;padding-bottom:3rem}
header[data-testid="stHeader"]{background:transparent}
h1,h2,h3{font-family:'Playfair Display',Georgia,serif!important;color:var(--green)!important}
.brand{padding:.7rem 0;border-bottom:1px solid #d8c8a6;color:var(--green);font:700 1.45rem 'Playfair Display',serif}
.brand small{display:block;font:500 .83rem 'DM Sans',sans-serif;color:#526358;letter-spacing:.08em}
.hero{margin:1.2rem 0;border:1px solid #e1c99f;border-radius:24px;padding:2.1rem 2rem;background:linear-gradient(100deg,#fff3d5d9,#fffef8eb 55%,#eaf4f2dc),url('data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 160"%3E%3Cpath d="M0 145Q180 10 310 90T600 25" fill="none" stroke="%23c89c50" stroke-width="3" opacity=".3"/%3E%3C/svg%3E');box-shadow:0 12px 28px #5b4b2414}
.hero .kicker{font-weight:700;letter-spacing:.16em;font-size:.78rem;color:#88570f}
.hero h1{font-size:clamp(2rem,4vw,3.3rem);margin:.35rem 0}.hero p{max-width:650px;font-size:1.08rem;line-height:1.65;color:#364c40}
.features{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:1.5rem}
.feature{padding:1rem;border:1px solid #e7dac1;border-radius:14px;background:#fffefa;min-height:104px}
.feature strong{display:block;margin-bottom:.35rem}.feature small{color:#46584e}
.gold{border-top:5px solid #bd7c20}.green{border-top:5px solid #267344}.blue{border-top:5px solid #215db4}.purple{border-top:5px solid #7b3591}
[data-testid="stVerticalBlockBorderWrapper"]{background:#fffefb;border:1px solid #e6d9c2!important;border-radius:18px!important}
.stButton>button[kind="primary"]{background:#175b3d!important;color:white!important;border-radius:12px!important;min-height:50px;font-weight:700;border:2px solid #175b3d!important}
.stButton>button[kind="primary"]:hover{background:#0f422d!important}
button:focus-visible,textarea:focus-visible,input:focus-visible{outline:3px solid #a6670c!important;outline-offset:3px!important}
textarea{font:1.22rem/1.8 'Noto Sans Devanagari','DM Sans',sans-serif!important}
.wordcard{padding:1rem;border:1px solid #d8e3d9;border-left:5px solid #247248;background:#f8fcf8;border-radius:12px;margin:.3rem 0 .7rem;min-height:145px}
.wordcard .dev{font:700 1.5rem 'Noto Sans Devanagari',sans-serif;color:#164d32}
.wordcard .meaning{font-weight:700;color:#263b31;margin:.4rem 0}.wordcard .meta{font-size:.88rem;color:#43594e}
/* Interactive word selector: prominent touch-friendly buttons */
div[data-testid="stButton"] button[kind="secondary"]{min-height:72px;border:1px solid #bad5c3;border-radius:14px;background:#f6fbf7;color:#174b32;white-space:normal;font-weight:700;line-height:1.5}
div[data-testid="stButton"] button[kind="secondary"]:hover{border-color:#267344;background:#eaf5ed}
.word-detail{border:2px solid #267344;border-radius:18px;background:#f3faf4;padding:1.1rem 1.3rem;margin:.7rem 0}
.word-detail-title{font:700 1.65rem 'Noto Sans Devanagari',sans-serif;color:#174b32}
/* Clean, scannable results displayed together — no tab navigation */
.note{color:#44584c;font-size:.9rem}
.result-heading{margin:1.35rem 0 .55rem;padding:.75rem 1rem;border-radius:12px;
  background:#fffefa;border-left:6px solid #bd7c20;font-weight:700;
  color:#163f2e;font-size:1.2rem}
.result-heading.green{border-left-color:#267344;border-top:0}
.result-heading.blue{border-left-color:#215db4;border-top:0}
.result-heading.purple{border-left-color:#7b3591;border-top:0}
.result-intro{color:#46584e;margin-bottom:.65rem;font-size:.95rem}
.additional-result{font-family:'Noto Sans Devanagari',sans-serif;font-size:1.3rem;line-height:1.9;background:#fff8e9;border-color:#e5d1a4;color:#423115}
.translation-result{background:#f0f8f2;border:1px solid #bed9c6;
  border-radius:14px;padding:1.25rem 1.35rem;font-size:1.2rem;line-height:1.7;
  color:#153e2c;margin:.6rem 0 1rem}
@media(max-width:650px){.hero{padding:1.25rem}.block-container{padding-left:1rem;padding-right:1rem}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}}
</style>""", unsafe_allow_html=True)

logo = (BASE / "assets" / "lotus.svg").read_text(encoding="utf-8")
header_logo, header_name = st.columns([1, 11], vertical_alignment="center")
with header_logo:
    st.image(str(BASE / "assets" / "lotus.svg"), width=70)
with header_name:
    st.markdown('<div class="brand">संस्कृतम् AI · Sanskritam AI<small>DISCOVER · TRANSLATE · UNDERSTAND</small></div>', unsafe_allow_html=True)
st.markdown('<section class="hero"><div class="kicker">ANCIENT WISDOM · MODERN INTELLIGENCE</div><h1>Discover the Beauty of Sanskrit</h1><p>Translate across languages, explore each word, and learn the grammar behind the meaning.</p></section>', unsafe_allow_html=True)


LANGUAGES = {
    "Hindi": {"native": "हिन्दी", "code": "hi"},
    "Tamil": {"native": "தமிழ்", "code": "ta"},
    "Telugu": {"native": "తెలుగు", "code": "te"},
    "Kannada": {"native": "ಕನ್ನಡ", "code": "kn"},
    "Malayalam": {"native": "മലയാളം", "code": "ml"},
    "Bengali": {"native": "বাংলা", "code": "bn"},
    "Marathi": {"native": "मराठी", "code": "mr"},
    "Gujarati": {"native": "ગુજરાતી", "code": "gu"},
    "French": {"native": "Français", "code": "fr"},
    "Spanish": {"native": "Español", "code": "es"},
    "English": {"native": "English", "code": "en"},
}

EXAMPLES = {
    "Simple sentence": "रामः पुस्तकं पठति।",
    "Gītā excerpt": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन",
    "Greeting": "नमस्ते।",
}


def api_key():
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("OPENAI_API_KEY")
    except (FileNotFoundError, KeyError):
        return None


def translate(source: str, direction: str, target_language: str) -> dict:
    schema = {
        "natural_translation": "string", "selected_language_translation": "string", "literal_translation": "string",
        "words": [{"word": "string", "meaning": "string", "grammar": "string", "note": "string", "lemma": "string", "case": "string", "number": "string", "gender": "string", "part_of_speech": "string"}],
        "grammar_explanation": "string", "sandhi_explanation": "string",
        "ambiguities": "string", "learning_tip": "string"
    }
    instructions = (
        "You are a careful Classical Sanskrit tutor. Respond with ONLY a valid JSON object, "
        "no Markdown fences. Follow the example shape supplied. "
        f"Always provide a fluent {target_language} translation in selected_language_translation. "
        f"Write the selected translation in {target_language}'s normal writing system, not transliteration. "
        "For Sanskrit-to-English, translate the Sanskrit source directly into the selected language, not via English. "
        "For English-to-Sanskrit, selected_language_translation should translate the generated Sanskrit into the selected language. "
        "natural_translation is English when direction is Sanskrit-to-English and Sanskrit when direction is English-to-Sanskrit. "
        "For Sanskrit-to-English, words are Sanskrit tokens or clearly identified segments. "
        "For English-to-Sanskrit, words are the Sanskrit words you generate. "
        "Do not fabricate sources. Clearly state uncertainty for ambiguous sandhi, "
        "compounds, morphology, or translations. Do not claim expert verification. "
        "For each word include lemma (dictionary form or verb root), case, number, gender, and part_of_speech; use not applicable where appropriate. "
        "Keep each word's note and grammar concise; give up to 12 words. "
        "If input is a fragment, identify it as a fragment."
    )
    result = OpenAI(api_key=api_key()).responses.create(
        model="gpt-4.1-mini", instructions=instructions,
        input=f"Direction: {direction}\nSelected output language: {target_language}\nText: {source}\nJSON example shape: {json.dumps(schema, ensure_ascii=False)}",
        max_output_tokens=2400,
    )
    data = json.loads(result.output_text)
    if not isinstance(data, dict) or not isinstance(data.get("words"), list):
        raise ValueError("Unexpected response format")
    return data


st.subheader("Translation workspace")
with st.container(border=True):
    direction = st.radio("Translation direction", ["Sanskrit → English", "English → Sanskrit"], horizontal=True)
    target_language = st.selectbox(
        "Additional translation language",
        list(LANGUAGES), index=0,
        format_func=lambda name: f"{name} · {LANGUAGES[name]['native']}",
        help="English is always shown for Sanskrit input. Choose another language to see its translation underneath."
    )
    example = st.selectbox("Try an example", ["Your own text", *EXAMPLES]) if direction.startswith("Sanskrit") else "Your own text"
    starter = EXAMPLES.get(example, "") if direction.startswith("Sanskrit") else ""
    if st.session_state.get("last_example") != (direction, example):
        st.session_state["source_text"] = starter
        st.session_state["last_example"] = (direction, example)
    source = st.text_area("Enter text", key="source_text", height=150, max_chars=1600,
                          placeholder="Type or paste Sanskrit here…" if direction.startswith("Sanskrit") else "Type English here…")
    learn = st.toggle("Beginner learning mode", value=True, help="Show word cards and an extra learning tip.")
    submitted = st.button("✦ Translate & Analyze", type="primary", use_container_width=True)
    st.caption("AI-generated explanations may contain mistakes. Verify important interpretations.")

if submitted:
    if not source.strip():
        st.warning("Enter text before translating.")
    elif not api_key():
        st.error("API key not found. Add OPENAI_API_KEY to your local .env or Streamlit Cloud secrets.")
    else:
        with st.spinner("Translating and analyzing…"):
            try:
                st.session_state["result"] = translate(source.strip(), direction, target_language)
                st.session_state["last_target_language"] = target_language
                st.session_state["last_source"] = source.strip()
                st.session_state["last_direction"] = direction
                st.session_state["selected_word"] = 0
            except (ValueError, json.JSONDecodeError):
                st.error("The AI response was incomplete. Please try again.")
            except Exception as exc:
                st.error("Could not translate. Check your API key, billing, and internet connection.")
                st.caption(f"Error category: {type(exc).__name__}")
data = st.session_state.get("result")
st.subheader("Your translation & analysis")
if not data:
    st.info("Enter a passage above and select Translate & Analyze. Your translation and explanations will appear together below.")
else:
    st.caption("Results for: " + st.session_state.get("last_source", source)[:180])
    st.markdown('<div class="result-heading">✦ Translation</div>', unsafe_allow_html=True)
    st.markdown('<p class="result-intro">Start with the meaning, then explore how each word works.</p>', unsafe_allow_html=True)
    if st.session_state.get("last_target_language") != target_language:
        st.info("Language selection changed. Click Translate & Analyze to update this result.")
    st.markdown("**Natural translation (English)**" if st.session_state.get("last_direction", "").startswith("Sanskrit") else "**Natural translation (Sanskrit)**")
    st.markdown('<div class="translation-result">' + html.escape(str(data.get("natural_translation") or "Not available")) + '</div>', unsafe_allow_html=True)
    result_language = st.session_state.get("last_target_language", "Hindi")
    lang_info = LANGUAGES.get(result_language, LANGUAGES["Hindi"])
    st.markdown(f"**{lang_info['native']} · {result_language} translation**")
    translated = str(data.get("selected_language_translation") or "").strip()
    if translated:
        st.markdown(
            '<div class="translation-result additional-result" lang="' + lang_info['code'] + '">' +
            html.escape(translated) + '</div>', unsafe_allow_html=True
        )
    else:
        st.info(f"{result_language} translation unavailable. Please try again.")
    st.markdown("**Literal translation**")
    st.write(str(data.get("literal_translation") or "Not available"))
    ambiguities = str(data.get("ambiguities") or "").strip()
    if ambiguities and ambiguities.lower() not in ("none", "n/a", "not applicable"):
        with st.expander("Other possible interpretations"):
            st.write(ambiguities)

    st.markdown('<div class="result-heading green">🌿 Word Explorer</div>', unsafe_allow_html=True)
    st.markdown('<p class="result-intro">See each word’s meaning and select one for a closer look.</p>', unsafe_allow_html=True)
    available = [w for w in data.get("words", []) if isinstance(w, dict) and w.get("word")]
    if available:
        st.caption("Select any word below to see its grammatical details. The selected word is highlighted in the panel beneath.")
        if st.session_state.get("selected_word", 0) >= len(available):
            st.session_state["selected_word"] = 0
        for offset in range(0, len(available), 4):
            cols = st.columns(min(4, len(available[offset:offset + 4])))
            for index, col in enumerate(cols, start=offset):
                item = available[index]
                selected = index == st.session_state.get("selected_word", 0)
                label = f"{'● ' if selected else ''}{item['word']}\n{item.get('meaning', '')}"
                with col:
                    if st.button(label, key=f"word_{index}", use_container_width=True,
                                 help=f"Explore grammar for {item['word']}"):
                        st.session_state["selected_word"] = index
                        st.rerun()
        item = available[st.session_state.get("selected_word", 0)]
        st.markdown('<div class="word-detail"><div class="word-detail-title">' +
                    html.escape(str(item.get("word", ""))) +
                    '</div><strong>' + html.escape(str(item.get("meaning", ""))) +
                    '</strong><br><small>Selected word · AI-generated analysis</small></div>',
                    unsafe_allow_html=True)
        left, right = st.columns(2)
        fields = [("Root / lemma", "lemma"), ("Part of speech", "part_of_speech"),
                  ("Case", "case"), ("Number", "number"), ("Gender", "gender"),
                  ("Grammar", "grammar")]
        for idx, (label, key) in enumerate(fields):
            with (left if idx % 2 == 0 else right):
                st.markdown(f"**{label}**")
                st.write(str(item.get(key) or "Not specified"))
        if item.get("note"):
            st.info("In context: " + str(item["note"]))
        reference = lookup(str(item.get("word", "")))
        if reference:
            with st.expander("View curated reference entry (exact-form match)"):
                st.json(reference)
                st.caption("A reference match is not independent verification of the full analysis.")
        else:
            st.caption("No exact match in the small reference lexicon; grammar is AI-generated and unverified.")
        if learn:
            st.info("Learning tip: " + str(data.get("learning_tip") or "Review each form in context."))
        with st.expander("📖 Reference cross-check (limited coverage)"):
            matches = compare_words(available)
            st.write(f"Exact forms found: {len(matches)} / {len(available)}")
            for match in matches:
                st.markdown(f"**{match['word']}** — {match['reference']['meaning']} · {match['reference']['note']}")
            st.caption("Dictionary matching is not a general Sanskrit morphological parser.")
    else:
        st.info("No word-by-word analysis was returned.")

    st.markdown('<div class="result-heading blue">▦ Grammar</div>', unsafe_allow_html=True)
    st.markdown('<p class="result-intro">Understand the sentence structure and grammatical forms.</p>', unsafe_allow_html=True)
    st.write(str(data.get("grammar_explanation") or "No grammar explanation available."))

    st.markdown('<div class="result-heading purple">🔗 Sandhi & Compounds</div>', unsafe_allow_html=True)
    st.markdown('<p class="result-intro">Explore how sounds and words join together.</p>', unsafe_allow_html=True)
    st.write(str(data.get("sandhi_explanation") or "No sandhi analysis available."))

    st.download_button("↓ Download complete analysis (JSON)",
                       data=json.dumps(data, ensure_ascii=False, indent=2),
                       file_name="sanskritam-analysis.json", mime="application/json")

if data:
    with st.expander("📝 Report an issue with this translation"):
        with st.form("translation_feedback", clear_on_submit=True):
            rating = st.radio("Was this result helpful?", ["Yes", "Partly", "No"], horizontal=True)
            category = st.selectbox("Issue type", ["Translation", "Word meaning", "Grammar", "Sandhi", "Other"])
            comment = st.text_area("What should be corrected? (optional)", max_chars=1000)
            sent = st.form_submit_button("Submit feedback")
            if sent:
                try:
                    save_feedback(st.session_state.get("last_source", ""),
                                  st.session_state.get("last_direction", ""), rating, category, comment)
                    st.success("Feedback saved locally. Thank you!")
                except Exception:
                    st.error("Could not save feedback. Check write permissions on the server.")
        st.caption("Feedback and source text are saved in a local SQLite file. On free ephemeral hosting, feedback may be lost after restarts. Do not enter private information.")

    st.warning("Educational prototype: translations, segmentation, and grammar may be incorrect. Not scholar-reviewed.")


st.divider()
st.caption("Sanskritam AI · Ancient Wisdom. Modern Intelligence. · sanskritam.ai · Hackathon v1.1")
