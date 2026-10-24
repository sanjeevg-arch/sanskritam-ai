import os
import re
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
st.set_page_config(page_title="Sanskritam AI | Discover · Translate · Understand", page_icon="🪷", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Noto+Sans+Devanagari:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap');
:root{color-scheme:light;--ink:#143b2b;--green:#195a35;--gold:#bd7510;--blue:#124a92;--purple:#6a267d;--cream:#fff9ed;--text:#24342f}
.stApp{background:linear-gradient(180deg,#fdf4df 0%,#fffaf1 30%,#f6f9f4 100%);color:var(--text);font-family:'DM Sans',sans-serif}
.block-container{max-width:1100px;padding-top:1.2rem;padding-bottom:3rem}
header[data-testid='stHeader']{background:transparent}
h1,h2,h3{font-family:'Playfair Display',Georgia,serif!important;color:var(--ink)!important}
.brandbar{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:.8rem 0 1.1rem;border-bottom:1px solid #dfcda8}
.brandname{font:700 1.45rem 'Playfair Display',Georgia,serif;color:#154a30}.brandname span{color:#ae690e}
.brandtag{font-size:.82rem;color:#42584b;letter-spacing:.06em}
.hero{position:relative;overflow:hidden;border-radius:24px;margin:1.25rem 0 1.5rem;padding:2.3rem 2rem;text-align:center;background:radial-gradient(circle at 9% 20%,#f2c47790,transparent 27%),radial-gradient(circle at 91% 80%,#8ec4e277,transparent 32%),linear-gradient(115deg,#fff4d8,#fffdf7 48%,#e9f4ee);border:1px solid #e7d4ad;box-shadow:0 12px 30px #4e552010}
.hero:before,.hero:after{content:'✦';position:absolute;color:#c28b31;opacity:.3;font-size:4rem;top:10%;left:5%}.hero:after{top:auto;left:auto;right:5%;bottom:5%;color:#235e8d}
.eyebrow{font-size:.8rem;font-weight:700;letter-spacing:.2em;color:#86520c;margin-bottom:.6rem}
.hero h1{font-size:clamp(2rem,4.4vw,3.4rem);margin:.2rem 0 .6rem}
.hero p{font-size:1.06rem;color:#354e45;margin:0 auto;max-width:620px;line-height:1.7}
.pillars{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:.6rem 0 1.6rem}
.pillar{background:#fffdf9;border:1px solid #e8dfcc;border-radius:14px;padding:1rem .8rem;box-shadow:0 4px 12px #3145210a}
.pillar strong{display:block;font-size:.96rem;margin:.15rem 0}.pillar small{color:#43564f;line-height:1.4;display:block}.pillar .icon{font-size:1.35rem}
.gold{border-top:4px solid #c17a16;color:#955c0c}.green{border-top:4px solid #267042;color:#195a35}.blue{border-top:4px solid #185cb2;color:#164e94}.purple{border-top:4px solid #7e3093;color:#692780}
.section-heading{font:700 1.45rem 'Playfair Display',Georgia,serif;color:#163e2d;margin:0 0 .4rem}
.section-sub{color:#455e52;margin-bottom:1.1rem}
[data-testid='stVerticalBlockBorderWrapper']{background:#fffefa;border:1px solid #e5d8bf!important;border-radius:18px!important;box-shadow:0 6px 22px #5846200c}
.stButton>button[kind='primary']{background:#185a39!important;color:white!important;border:2px solid #185a39!important;border-radius:12px;min-height:52px;font-size:1rem;font-weight:700}
.stButton>button[kind='primary']:hover{background:#103f2b!important;border-color:#103f2b!important}
.stButton button:focus-visible,button:focus-visible,textarea:focus-visible,input:focus-visible{outline:3px solid #a5670a!important;outline-offset:3px!important}
textarea{font-family:'Noto Sans Devanagari','DM Sans',sans-serif!important;font-size:1.2rem!important;line-height:1.85!important}
[data-testid='stMarkdownContainer'] p,[data-testid='stMarkdownContainer'] li{line-height:1.7}
[data-testid='stTabs'] button{font-weight:700!important}
.footer{text-align:center;color:#3e554a;font-size:.86rem;padding:1rem}
@media(max-width:720px){.block-container{padding:1rem .8rem 2rem}.brandbar{flex-direction:column;align-items:flex-start}.hero{padding:1.7rem .9rem}.pillars{grid-template-columns:repeat(2,minmax(0,1fr))}.hero:before,.hero:after{display:none}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}}
</style>""",unsafe_allow_html=True)

st.markdown('<div class="brandbar"><div class="brandname">🪷 संस्कृतम् <span>AI</span> · Sanskritam AI</div><div class="brandtag">DISCOVER · EXPLORE · UNDERSTAND</div></div>',unsafe_allow_html=True)
st.markdown('<section class="hero"><div class="eyebrow">ANCIENT WISDOM · MODERN INTELLIGENCE</div><h1>Discover the Beauty of Sanskrit</h1><p>Bridge timeless knowledge and modern discovery. Translate Sanskrit, explore every word, and understand the meaning behind the language.</p></section>',unsafe_allow_html=True)
st.markdown('''<div class="pillars"><div class="pillar gold"><div class="icon">✦</div><strong>Translation</strong><small>Clear, natural meaning</small></div><div class="pillar green"><div class="icon">🌿</div><strong>Word Analysis</strong><small>Learn word by word</small></div><div class="pillar blue"><div class="icon">▦</div><strong>Grammar</strong><small>Explore language structure</small></div><div class="pillar purple"><div class="icon">ॐ</div><strong>Sandhi</strong><small>Uncover word connections</small></div></div>''',unsafe_allow_html=True)

st.markdown('<div class="section-heading">Your translation workspace</div><div class="section-sub">Start with an example or paste your own text below.</div>',unsafe_allow_html=True)
with st.container(border=True):
    direction=st.radio('Translation direction',['Sanskrit → English','English → Sanskrit'],horizontal=True)
    examples={'Bhagavad Gītā excerpt':'कर्मण्येवाधिकारस्ते मा फलेषु कदाचन','Simple sentence':'रामः पुस्तकं पठति।','Greeting':'नमस्ते।'}
    if direction=='Sanskrit → English':
        chosen=st.selectbox('Explore an example',['Choose your own',*examples.keys()])
        initial=examples.get(chosen,'')
    else:
        initial='The student reads a book.'
    source=st.text_area('Text to translate',value=initial,height=150,placeholder='Type or paste text here…',max_chars=2000)
    translate=st.button('✦ Translate & Analyze',type='primary',use_container_width=True)

if translate:
    if not source.strip():
        st.warning('Please enter some text to translate.')
    else:
        key=os.getenv('OPENAI_API_KEY')
        if not key:
            try: key=st.secrets.get('OPENAI_API_KEY')
            except Exception: key=None
        if not key:
            st.error('API key missing. Set OPENAI_API_KEY in your local .env file or in Streamlit Cloud secrets.')
        else:
            with st.spinner('Exploring the language and meaning…'):
                try:
                    result=OpenAI(api_key=key).responses.create(
                        model='gpt-4.1-mini',
                        instructions='You are a careful Classical Sanskrit assistant. Respond with exactly these Markdown level-2 headings in order: Natural Translation, Literal Translation, Word-by-word Analysis, Grammar, Sandhi and Compounds, Ambiguities. Word-by-word Analysis should contain a Markdown table. Identify uncertainty honestly; never fabricate sources or claim that analysis is verified. For English to Sanskrit, explain generated Sanskrit forms.',
                        input=f'Direction: {direction}\nText:\n{source}',max_output_tokens=1800)
                    st.session_state['translation_result']=result.output_text
                    st.session_state['translation_source']=source
                    st.session_state['translation_direction']=direction
                except Exception as exc:
                    st.error('Translation could not be completed. Check your API billing, model access, and network connection.')
                    st.caption(f'Error type: {type(exc).__name__}')

if st.session_state.get('translation_result'):
    st.markdown('### Translation & language insights')
    raw=st.session_state['translation_result']
    parts=re.split(r'(?m)^##\s+(.+?)\s*$',raw)
    sections={parts[i].strip().lower():parts[i+1].strip() for i in range(1,len(parts)-1,2)}
    titles=[('Natural Translation','Translation'),('Literal Translation','Literal'),('Word-by-word Analysis','Words'),('Grammar','Grammar'),('Sandhi and Compounds','Sandhi'),('Ambiguities','Alternatives')]
    if sections:
        tabs=st.tabs([label for _,label in titles])
        for tab,(heading,label) in zip(tabs,titles):
            with tab:
                content=sections.get(heading.lower())
                if content: st.markdown(content)
                else: st.info('No separate analysis was provided for this section.')
    else:
        st.markdown(raw)
    st.download_button('↓ Download full analysis',data=raw,file_name='sanskritam-analysis.md',mime='text/markdown')
    st.info('AI-generated Sanskrit translations and grammatical analyses may contain errors. Consult a qualified scholar for important interpretations.')

st.markdown('<div class="footer">Sanskritam AI · Ancient Wisdom. Modern Intelligence. · sanskritam.ai<br>Hackathon MVP v0.3</div>',unsafe_allow_html=True)
