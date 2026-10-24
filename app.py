import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title='Sanskritam AI | Translate & Understand', page_icon='📜', layout='wide')

st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+Devanagari:wght@400;500;600&family=Playfair+Display:wght@500;600;700&display=swap');
:root {color-scheme:light;}
.stApp {background:#FAF8F3;color:#263238;font-family:'Inter',sans-serif;}
.block-container {max-width:1050px;padding-top:2rem;padding-bottom:4rem;}
h1,h2,h3 {font-family:'Playfair Display',serif!important;color:#164A4A!important;}
.hero {text-align:center;padding:1.4rem 0 2rem;}
.hero h1 {font-size:clamp(2.2rem,5vw,3.5rem);margin-bottom:.5rem;}
.hero p {font-size:1.12rem;color:#52636B;}
.brand {color:#164A4A;font-size:1.25rem;font-weight:700;letter-spacing:.03em;}
.eyebrow {color:#176B65;font-weight:700;letter-spacing:.14em;font-size:.75rem;}
.stButton>button[kind='primary'] {background:#176B65;color:white;border:2px solid #176B65;border-radius:10px;min-height:48px;font-weight:700;}
.stButton>button[kind='primary']:hover {background:#164A4A;border-color:#164A4A;color:white;}
.stButton>button:focus-visible,textarea:focus-visible {outline:3px solid #C69C52!important;outline-offset:3px;}
textarea {font-family:'Noto Sans Devanagari','Inter',sans-serif!important;font-size:1.15rem!important;line-height:1.8!important;}
[data-testid='stVerticalBlockBorderWrapper'] {background:#fff;border-radius:16px;}
[data-testid='stMarkdownContainer'] p {line-height:1.65;}
.smallnote {color:#52636B;font-size:.9rem;}
@media (max-width:640px) {.block-container {padding:1rem;} .hero {padding:1rem 0;}}
</style>''', unsafe_allow_html=True)

st.markdown('<div class="brand">संस्कृतम् AI &nbsp; | &nbsp; Sanskritam AI</div>', unsafe_allow_html=True)
st.markdown('''<div class="hero"><div class="eyebrow">TRANSLATE · UNDERSTAND · EXPLORE</div>
<h1>Discover the Beauty of Sanskrit</h1>
<p>Ancient Wisdom. Modern Intelligence.<br>Understand the meaning behind every word.</p></div>''', unsafe_allow_html=True)

with st.container(border=True):
    st.subheader('Translation workspace')
    direction = st.radio('Translation direction', ['Sanskrit → English', 'English → Sanskrit'], horizontal=True)
    examples = {'Bhagavad Gītā excerpt': 'कर्मण्येवाधिकारस्ते मा फलेषु कदाचन', 'Simple Sanskrit sentence': 'रामः पुस्तकं पठति।'}
    if direction == 'Sanskrit → English':
        example = st.selectbox('Try an example', ['Custom text', *examples.keys()])
        initial = examples.get(example, '')
    else:
        initial = 'The student reads a book.'
    text = st.text_area('Enter text to translate', value=initial, height=150, placeholder='Type or paste Sanskrit here…')
    submitted = st.button('Translate & Analyze →', type='primary', use_container_width=True)

if submitted:
    if not text.strip():
        st.warning('Enter some text before translating.')
    elif len(text) > 2000:
        st.warning('For this demo, enter fewer than 2,000 characters.')
    else:
        key = os.getenv('OPENAI_API_KEY')
        if not key:
            try:
                key = st.secrets.get('OPENAI_API_KEY')
            except Exception:
                pass
        if not key:
            st.error('API key missing. Add OPENAI_API_KEY to your local .env file or Streamlit Cloud secrets.')
        else:
            with st.spinner('Translating and analyzing your text…'):
                try:
                    response = OpenAI(api_key=key).responses.create(
                        model='gpt-4.1-mini',
                        instructions=('You are a careful Classical Sanskrit language assistant. '
                                      'Return clearly labeled sections using Markdown headings: '
                                      'Natural translation, Literal translation, Word-by-word analysis '
                                      '(Markdown table), Grammar, Sandhi and compounds, Ambiguities. '
                                      'For English-to-Sanskrit, explain generated forms. '
                                      'Do not claim certainty when analysis is ambiguous. '
                                      'Do not fabricate citations.'),
                        input=f'Direction: {direction}\nText:\n{text}',
                        max_output_tokens=1800,
                    )
                    st.session_state['result'] = response.output_text
                except Exception as exc:
                    st.error('Could not complete translation. Check API access, billing, and connectivity.')
                    st.caption(f'Technical detail: {type(exc).__name__}')
if st.session_state.get('result'):
    st.subheader('Your translation & analysis')
    with st.container(border=True):
        st.markdown(st.session_state['result'])
        st.download_button('Download analysis', st.session_state['result'], file_name='sanskritam-analysis.md', mime='text/markdown')
    st.caption('AI-generated translation and grammar may be inaccurate. Verify important passages with a qualified Sanskrit scholar.')
st.divider()
st.markdown('<p class="smallnote">Sanskritam AI · Hackathon MVP v0.2 · sanskritam.ai</p>', unsafe_allow_html=True)
