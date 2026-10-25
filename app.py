"""Sanskritam AI v1.4 — Accessibility & Learning Edition."""
import json
import html
import os
import streamlit.components.v1 as components
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from reference import lookup, compare_words
from feedback import save_feedback
from indic_transliteration import sanscript

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
.comparison-text{font-family:'DM Sans','Noto Sans Devanagari',sans-serif;font-size:1.18rem;line-height:1.9;min-height:75px;overflow-wrap:anywhere;color:#164832}
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


def translate(source: str, direction: str, target_languages: list[str]) -> dict:
    schema = {
        "natural_translation": "string", "translations": {lang: "string" for lang in target_languages}, "literal_translation": "string",
        "words": [{"word": "string", "meaning": "string", "grammar": "string", "note": "string", "lemma": "string", "case": "string", "number": "string", "gender": "string", "part_of_speech": "string"}],
        "grammar_explanation": "string", "sandhi_explanation": "string",
        "ambiguities": "string", "learning_tip": "string"
    }
    instructions = (
        "You are a careful Classical Sanskrit tutor. Respond with ONLY a valid JSON object, "
        "no Markdown fences. Follow the example shape supplied. "
        "Return a translations JSON object with exactly the requested language names as keys. "
        "Each translation must be fluent and in its language’s native script. "
        "Translate directly from the original Sanskrit wherever possible, not through English. "
        "For English-to-Sanskrit, translate the generated Sanskrit into each requested language. "
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
        input=f"Direction: {direction}\nComparison languages: {json.dumps(target_languages)}\nText: {source}\nJSON example shape: {json.dumps(schema, ensure_ascii=False)}",
        max_output_tokens=2400,
    )
    data = json.loads(result.output_text)
    if not isinstance(data, dict) or not isinstance(data.get("words"), list):
        raise ValueError("Unexpected response format")
    if not isinstance(data.get("translations"), dict):
        raise ValueError("Missing comparison translations")
    return data


# Accessibility controls apply to the results without triggering a new API request.
st.markdown("### ♿ Accessibility & Learning Settings")
with st.expander("Customize reading and listening", expanded=False):
    size_choice = st.select_slider("Text size", options=["Small", "Medium", "Large", "Extra large"], value="Medium")
    high_contrast = st.checkbox("High contrast", value=False)
    show_iast = st.checkbox("Show Sanskrit transliteration (IAST)", value=True)
    simple_reading = st.checkbox("Simplified reading mode", value=False,
                                help="Reduce decorative elements and increase reading space.")
    audio_speed = st.select_slider("Audio speed", options=["Slow (0.75×)", "Normal (1×)", "Fast (1.25×)"], value="Normal (1×)")

size_px = {"Small": 17, "Medium": 20, "Large": 25, "Extra large": 30}[size_choice]
rate = {"Slow (0.75×)": 0.75, "Normal (1×)": 1.0, "Fast (1.25×)": 1.25}[audio_speed]
# Controlled values only: no user text is inserted into CSS.
st.markdown(f"""<style>
.translation-result,.comparison-text,.word-detail,.stMarkdown p{{font-size:{size_px}px!important;line-height:1.85!important}}
textarea{{font-size:{size_px}px!important}}
.stButton button:focus-visible,[data-baseweb] *:focus-visible,select:focus-visible{{outline:3px solid #a6670c!important;outline-offset:3px!important}}
{'.stApp{background:#fff!important;color:#111!important} .translation-result,.word-detail,.comparison-text{background:#fff!important;color:#111!important;border:2px solid #111!important} .result-heading{color:#111!important;border-color:#111!important;background:#fff!important} .stMarkdown p,.stMarkdown span{color:#111!important}' if high_contrast else ''}
{'.hero,.features{display:none!important} .block-container{max-width:1000px!important}' if simple_reading else ''}
</style>""", unsafe_allow_html=True)


def iast(text: str) -> str:
    """Deterministic Devanagari to IAST transliteration; not phonetic audio."""
    return sanscript.transliterate(text, sanscript.DEVANAGARI, sanscript.IAST)


def show_transliteration(text: str):
    if show_iast and text and re.search(r"[\u0900-\u097f]", text):
        st.caption("IAST transliteration: " + iast(text))

st.subheader("Translation workspace")
with st.container(border=True):
    direction = st.radio("Translation direction", ["Sanskrit → English", "English → Sanskrit"], horizontal=True)
    target_languages = st.multiselect(
        "Compare Languages — choose up to 3",
        [name for name in LANGUAGES if name != "English"],
        default=["Hindi"],
        format_func=lambda name: f"{name} · {LANGUAGES[name]['native']}",
        max_selections=3,
        help="English is shown automatically for Sanskrit input. Select up to three additional languages."
    )
    st.caption(f"{len(target_languages)} of 3 comparison languages selected")
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
                st.session_state["result"] = translate(source.strip(), direction, target_languages)
                st.session_state["last_target_languages"] = target_languages.copy()
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
    show_transliteration(st.session_state.get("last_source", ""))
    st.markdown('<div class="result-heading">✦ Translation</div>', unsafe_allow_html=True)
    st.markdown('<p class="result-intro">Start with the meaning, then explore how each word works.</p>', unsafe_allow_html=True)
    if st.session_state.get("last_target_languages", []) != target_languages:
        st.info("Language selection changed. Click Translate & Analyze to refresh the comparison.")
    st.markdown("**Natural translation (English)**" if st.session_state.get("last_direction", "").startswith("Sanskrit") else "**Natural translation (Sanskrit)**")
    st.markdown('<div class="translation-result">' + html.escape(str(data.get("natural_translation") or "Not available")) + '</div>', unsafe_allow_html=True)
    if not st.session_state.get("last_direction", "").startswith("Sanskrit"):
        show_transliteration(str(data.get("natural_translation") or ""))
    selected = st.session_state.get("last_target_languages", [])
    if selected:
        st.markdown("### 🌐 Compare Languages")
        st.caption("Compare how the same passage is expressed across languages.")
        translations = data.get("translations") or {}
        cards = (["English"] if st.session_state.get("last_direction", "").startswith("Sanskrit") else ["Sanskrit"]) + selected
        # Use Streamlit columns for responsive comparison; on narrow screens Streamlit stacks columns.
        for start_index in range(0, len(cards), 2):
            row = cards[start_index:start_index + 2]
            cols = st.columns(len(row), gap="medium")
            for col, language in zip(cols, row):
                with col:
                    if language == "English" or language == "Sanskrit":
                        value = str(data.get("natural_translation") or "Not available")
                        code = "en" if language == "English" else "sa"
                        native = language
                    else:
                        value = str(translations.get(language) or "Translation unavailable")
                        code = LANGUAGES[language]["code"]
                        native = LANGUAGES[language]["native"]
                    with st.container(border=True):
                        st.markdown(f"**{html.escape(native)} · {language}**")
                        st.markdown('<div class="comparison-text" lang="' + code + '">' + html.escape(value) + '</div>', unsafe_allow_html=True)
    else:
        st.caption("Select comparison languages above and translate to see them side by side.")
    # Browser-native speech synthesis: no audio API key, no extra dependencies.
    # A single component owns playback controls, so Stop can cancel any active speech.
    speech_items = []
    if st.session_state.get("last_direction", "").startswith("Sanskrit"):
        speech_items.append({"name": "Sanskrit original", "text": st.session_state.get("last_source", ""), "lang": "sa-IN"})
        speech_items.append({"name": "English translation", "text": str(data.get("natural_translation") or ""), "lang": "en-US"})
    else:
        speech_items.append({"name": "English original", "text": st.session_state.get("last_source", ""), "lang": "en-US"})
        speech_items.append({"name": "Sanskrit translation", "text": str(data.get("natural_translation") or ""), "lang": "sa-IN"})
    speech_codes = {"Hindi": "hi-IN", "Tamil": "ta-IN", "Telugu": "te-IN", "Kannada": "kn-IN", "Malayalam": "ml-IN", "Bengali": "bn-IN", "Marathi": "mr-IN", "Gujarati": "gu-IN", "French": "fr-FR", "Spanish": "es-ES", "English": "en-US"}
    for language in selected:
        translated = str((data.get("translations") or {}).get(language) or "").strip()
        if translated:
            speech_items.append({"name": language + " translation", "text": translated, "lang": speech_codes[language]})
    st.markdown("### 🔊 Listen to Translation")
    st.caption("Listen to the original and each available translation. Audio speed is set in Accessibility Settings. Voices depend on your browser; Sanskrit pronunciation may be inaccurate.")
    # JSON encoding prevents translation content from being interpreted as HTML or JS.
    speech_json = json.dumps(speech_items, ensure_ascii=False).replace("<", "\\u003c")
    speech_html = """<!doctype html><html><head><meta charset="utf-8"><style>
    body{font:15px system-ui,sans-serif;color:#214333;margin:0;padding:4px;background:transparent}
    .controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
    select,button{border:1px solid #b5cdbb;border-radius:10px;padding:10px;background:#fff;max-width:100%;font:inherit}
    button{background:#175b3d;color:#fff;cursor:pointer;font-weight:650}
    button.stop{background:#fff;color:#175b3d}
    button:disabled{opacity:.5;cursor:not-allowed}
    #status{margin:9px 0;color:#486052;font-size:13px}
    </style></head><body><div class="controls"><label for="speech-choice">Read aloud:</label>
    <select id="speech-choice"></select><button id="play">▶ Listen</button><button class="stop" id="stop">■ Stop</button></div>
    <div id="status" role="status" aria-live="polite">Choose a language and press Listen.</div>
    <script>
    const items=__ITEMS__;
    const select=document.getElementById('speech-choice');
    const status=document.getElementById('status');
    const synth=window.speechSynthesis;
    for(const [i,item] of items.entries()) {const o=document.createElement('option');o.value=i;o.textContent=item.name;select.appendChild(o);}
    if(!synth){document.getElementById('play').disabled=true;status.textContent='Speech playback is not supported in this browser.';}
    document.getElementById('play').onclick=()=>{
      if(!synth)return;
      synth.cancel();
      const item=items[Number(select.value)];
      if(!item||!item.text.trim()){status.textContent='No text available to read.';return;}
      const utterance=new SpeechSynthesisUtterance(item.text);
      utterance.lang=item.lang;utterance.rate=__RATE__;
      const voices=synth.getVoices();
      const exact=voices.find(v=>v.lang.toLowerCase()===item.lang.toLowerCase());
      const similar=voices.find(v=>v.lang.toLowerCase().split('-')[0]===item.lang.toLowerCase().split('-')[0]);
      if(exact||similar)utterance.voice=exact||similar;
      else status.textContent='No matching '+item.name+' voice found; your browser may use a fallback voice.';
      utterance.onstart=()=>{if(exact||similar)status.textContent='Playing '+item.name+'…';};
      utterance.onend=()=>{status.textContent='Playback finished.';};
      utterance.onerror=(e)=>{if(e.error!=='canceled')status.textContent='Unable to play audio: '+e.error;};
      synth.speak(utterance);
    };
    document.getElementById('stop').onclick=()=>{if(synth)synth.cancel();status.textContent='Playback stopped.';};
    window.addEventListener('pagehide',()=>{if(synth)synth.cancel();});
    </script></body></html>""".replace("__ITEMS__", speech_json).replace("__RATE__", str(rate))
    components.html(speech_html, height=112, scrolling=False)
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
        show_transliteration(str(item.get("word", "")))
        st.markdown('<div class="word-detail"><div class="word-detail-title">' +
                    html.escape(str(item.get("word", ""))) +
                    '</div><strong>' + html.escape(str(item.get("meaning", ""))) +
                    '</strong><br><small>Selected word · AI-generated analysis</small></div>',
                    unsafe_allow_html=True)
        # A dedicated speech control for the selected word; browser voices are approximate.
        word_speech = json.dumps(str(item.get("word", "")), ensure_ascii=False).replace("<", "\\u003c")
        word_audio_html = """<!doctype html><html><head><meta charset="utf-8"><style>
        body{margin:0;font:15px system-ui,sans-serif}button{padding:10px 16px;border:2px solid #175b3d;
        border-radius:10px;background:#175b3d;color:white;cursor:pointer}button:focus-visible{outline:3px solid #a6670c;outline-offset:3px}
        #word-status{padding-left:10px;font-size:13px;color:#243e31}</style></head><body>
        <button id="say" aria-label="Pronounce selected Sanskrit word">🔊 Pronounce word</button>
        <button id="halt" aria-label="Stop word pronunciation">■ Stop</button>
        <span id="word-status" role="status" aria-live="polite"></span><script>
        const word=__WORD__,synth=window.speechSynthesis,status=document.getElementById('word-status');
        if(!synth){document.getElementById('say').disabled=true;status.textContent='Speech is unavailable.';}
        document.getElementById('say').onclick=()=>{if(!synth)return;synth.cancel();
          const u=new SpeechSynthesisUtterance(word);u.lang='sa-IN';u.rate=__RATE__;
          const voices=synth.getVoices();const voice=voices.find(v=>v.lang.toLowerCase().startsWith('sa'));
          if(voice){u.voice=voice;status.textContent='Playing…';}
          else status.textContent='No Sanskrit voice detected. Pronunciation may be inaccurate.';
          u.onend=()=>status.textContent='Finished.';u.onerror=e=>{if(e.error!=='canceled')status.textContent='Speech unavailable.'};synth.speak(u)};
        document.getElementById('halt').onclick=()=>{if(synth)synth.cancel();status.textContent='Stopped.'};
        window.addEventListener('pagehide',()=>{if(synth)synth.cancel()});
        </script></body></html>""".replace("__WORD__", word_speech).replace("__RATE__", str(rate))
        components.html(word_audio_html, height=60, scrolling=False)
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
st.caption("Sanskritam AI · Ancient Wisdom. Modern Intelligence. · sanskritam.ai · Hackathon v1.2")
