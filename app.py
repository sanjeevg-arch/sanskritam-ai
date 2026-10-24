
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    api_key = st.secrets.get("OPENAI_API_KEY")

if api_key:
    os.environ["OPENAI_API_KEY"] = api_key
    
st.set_page_config(
    page_title="Sanskritam AI",
    page_icon="📜"
)

st.title("📜 Sanskritam AI")
st.caption("Ancient Wisdom. Modern Intelligence.")

direction = st.radio(
    "Choose translation direction",
    ["Sanskrit → English", "English → Sanskrit"]
)

default_text = (
    "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन"
    if direction == "Sanskrit → English"
    else "The student reads a book."
)

text = st.text_area(
    "Enter text",
    value=default_text,
    height=130
)

if st.button("Translate & Analyze", type="primary"):
    if not text.strip():
        st.warning("Please enter text.")
    elif not os.getenv("OPENAI_API_KEY"):
        st.error("OpenAI API key is missing. Check your .env file.")
    else:
        with st.spinner("Analyzing Sanskrit..."):
            try:
                client = OpenAI()

                prompt = f"""
Translation direction: {direction}

Text:
{text}

You are a careful Classical Sanskrit language assistant.

Provide the following sections:

## Natural Translation
Translate the text accurately.

## Literal Translation
Give a close, literal translation.

## Word-by-word Analysis
Provide a Markdown table with:
- Original word
- Segmentation if applicable
- Meaning
- Grammatical analysis

## Sandhi and Compounds
Explain identifiable sandhi and compounds.

## Grammar Explanation
Explain relevant case endings, verb forms,
and syntactic relationships.

## Ambiguities
Identify uncertain analyses and alternative meanings.

Do not invent grammatical certainty.
If the text is incomplete, say so.
For English-to-Sanskrit translation, explain
the Sanskrit forms you generated.
"""

                response = client.responses.create(
                    model="gpt-4.1-mini",
                    input=prompt,
                    max_output_tokens=1800
                )

                st.markdown(response.output_text)
                st.caption(
                    "AI-generated analysis. Verify important "
                    "translations with a Sanskrit expert."
                )

            except Exception as error:
                st.error(
                    "Translation failed. Check your API key, "
                    "billing, network, and model access."
                )
                st.code(str(error))

st.divider()
st.caption("sanskritam.ai | Hackathon MVP v0.1")
