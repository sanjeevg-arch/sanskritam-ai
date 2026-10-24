"""Sanskritam AI v0.4 — beginner-friendly Streamlit hackathon app."""
import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

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
.stTabs [role="tab"]{font-weight:700}.note{color:#44584c;font-size:.9rem}
@media(max-width:750px){.block-container{padding:1rem .8rem}.features{grid-template-columns:repeat(2,1fr)}.hero{padding:1.5rem 1rem}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}}
</style>""", unsafe_allow_html=True)

logo = (BASE / "assets" / "lotus.svg").read_text(encoding="utf-8")
header_logo, header_name = st.columns([1, 11], vertical_alignment="center")
with header_logo:
    st.image(str(BASE / "assets" / "lotus.svg"), width=70)
with header_name:
    st.markdown('<div class="brand">संस्कृतम् AI · Sanskritam AI<small>DISCOVER · TRANSLATE · UNDERSTAND</small></div>', unsafe_allow_html=True)
st.markdown('<section class="hero"><div class="kicker">ANCIENT WISDOM · MODERN INTELLIGENCE</div><h1>Discover the Beauty of Sanskrit</h1><p>Translate across languages, explore each word, and learn the grammar behind the meaning.</p></section>', unsafe_allow_html=True)
st.markdown('<div class="features"><div class="feature gold"><strong>✦ Translation</strong><small>Natural and literal meaning</small></div><div class="feature green"><strong>🌿 Word Explorer</strong><small>Understand each word</small></div><div class="feature blue"><strong>▦ Grammar</strong><small>Learn the structure</small></div><div class="feature purple"><strong>ॐ Sandhi</strong><small>Explore word connections</small></div></div>', unsafe_allow_html=True)

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


def translate(source: str, direction: str) -> dict:
    schema = {
        "natural_translation": "string", "literal_translation": "string",
        "words": [{"word": "string", "meaning": "string", "grammar": "string", "note": "string"}],
        "grammar_explanation": "string", "sandhi_explanation": "string",
        "ambiguities": "string", "learning_tip": "string"
    }
    instructions = (
        "You are a careful Classical Sanskrit tutor. Respond with ONLY a valid JSON object, "
        "no Markdown fences. Follow the example shape supplied. "
        "For Sanskrit-to-English, words are Sanskrit tokens or clearly identified segments. "
        "For English-to-Sanskrit, words are the Sanskrit words you generate. "
        "Do not fabricate sources. Clearly state uncertainty for ambiguous sandhi, "
        "compounds, morphology, or translations. Do not claim expert verification. "
        "Keep each word's note and grammar concise; give up to 12 words. "
        "If input is a fragment, identify it as a fragment."
    )
    result = OpenAI(api_key=api_key()).responses.create(
        model="gpt-4.1-mini", instructions=instructions,
        input=f"Direction: {direction}\nText: {source}\nJSON example shape: {json.dumps(schema, ensure_ascii=False)}",
        max_output_tokens=2400,
    )
    data = json.loads(result.output_text)
    if not isinstance(data, dict) or not isinstance(data.get("words"), list):
        raise ValueError("Unexpected response format")
    return data


st.subheader("Translation workspace")
left, right = st.columns([1, 1], gap="large")
with left:
    with st.container(border=True):
        direction = st.radio("Translation direction", ["Sanskrit → English", "English → Sanskrit"], horizontal=True)
        example = st.selectbox("Try an example", ["Your own text", *EXAMPLES]) if direction.startswith("Sanskrit") else "Your own text"
        starter = EXAMPLES.get(example, "") if direction.startswith("Sanskrit") else ""
        if st.session_state.get("last_example") != (direction, example):
            st.session_state["source_text"] = starter
            st.session_state["last_example"] = (direction, example)
        source = st.text_area("Enter text", key="source_text", height=185, max_chars=1600,
                              placeholder="Type or paste Sanskrit here…" if direction.startswith("Sanskrit") else "Type English here…")
        learn = st.toggle("Beginner learning mode", value=True, help="Show word cards and an extra learning tip.")
        submitted = st.button("✦ Translate & Analyze", type="primary", use_container_width=True)
        st.caption("AI-generated explanations may contain mistakes. Verify important interpretations.")

with right:
    with st.container(border=True):
        st.markdown("### Translation result")
        if submitted:
            if not source.strip():
                st.warning("Enter text before translating.")
            elif not api_key():
                st.error("API key not found. Add OPENAI_API_KEY to your local .env or Streamlit Cloud secrets.")
            else:
                with st.spinner("Translating and analyzing…"):
                    try:
                        st.session_state["result"] = translate(source.strip(), direction)
                        st.session_state["last_source"] = source.strip()
                    except (ValueError, json.JSONDecodeError):
                        st.error("The AI response was incomplete. Please try again.")
                    except Exception as exc:
                        st.error("Could not translate. Check your API key, billing, and internet connection.")
                        st.caption(f"Error category: {type(exc).__name__}")
        data = st.session_state.get("result")
        if data:
            st.markdown("**Natural translation**")
            st.success(str(data.get("natural_translation", "Not available")))
            st.markdown("**Literal translation**")
            st.write(str(data.get("literal_translation", "Not available")))
            st.download_button("↓ Download analysis (JSON)", data=json.dumps(data, ensure_ascii=False, indent=2),
                               file_name="sanskritam-analysis.json", mime="application/json")
        else:
            st.info("Your translation will appear here after you select Translate & Analyze.")

if data:
    st.subheader("Explore the meaning")
    words_tab, grammar_tab, sandhi_tab, alternatives_tab = st.tabs(["🌿 Words", "▦ Grammar", "ॐ Sandhi", "✦ Alternatives"])
    with words_tab:
        words = data.get("words", [])
        if learn:
            st.caption("Word cards help you study one form at a time. AI analyses require verification.")
            for offset in range(0, min(len(words), 12), 3):
                cols = st.columns(3)
                for col, item in zip(cols, words[offset:offset+3]):
                    with col:
                        with st.container(border=True):
                            st.markdown(f"**{item.get('word', '')}**")
                            st.write(item.get("meaning", ""))
                            st.caption(item.get("grammar", ""))
                            if item.get("note"):
                                st.caption(item["note"])
            st.info("Learning tip: " + str(data.get("learning_tip", "Review each form in context.")))
        else:
            st.dataframe([{"Word": x.get("word", ""), "Meaning": x.get("meaning", ""),
                           "Grammar": x.get("grammar", "")} for x in words],
                         use_container_width=True, hide_index=True)
    with grammar_tab:
        st.write(str(data.get("grammar_explanation", "No explanation provided.")))
    with sandhi_tab:
        st.write(str(data.get("sandhi_explanation", "No sandhi analysis provided.")))
    with alternatives_tab:
        st.write(str(data.get("ambiguities", "No alternatives identified.")))
    st.warning("Educational prototype: translations, segmentation, and grammar may be incorrect. Not scholar-reviewed.")

st.divider()
st.caption("Sanskritam AI · Ancient Wisdom. Modern Intelligence. · sanskritam.ai · Hackathon v0.4")
