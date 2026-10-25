"""No-extra-API-call practice from existing AI word analysis.

Quizzes are intentionally conservative: only words with distinct nonempty meanings
are used; source AI analyses may be wrong and should be verified by learners.
"""
import html
import hashlib
import json
import random
import re

import streamlit as st


def build_questions(data: dict, source: str) -> list[dict]:
    words = data.get("words") or []
    pairs = []
    seen_words = set()
    seen_meanings = set()
    for entry in words:
        if not isinstance(entry, dict):
            continue
        word = str(entry.get("word") or "").strip()
        meaning = str(entry.get("meaning") or "").strip()
        if not word or not meaning or len(word) > 80 or len(meaning) > 90:
            continue
        key = re.sub(r"\s+", " ", meaning.casefold())
        if word in seen_words or key in seen_meanings:
            continue
        seen_words.add(word)
        seen_meanings.add(key)
        pairs.append((word, meaning, str(entry.get("grammar") or "")))
    if len(pairs) < 3:
        return []
    seed = int(hashlib.sha256(source.encode("utf-8")).hexdigest()[:12], 16)
    rng = random.Random(seed)
    chosen = pairs[:min(5, len(pairs))]
    questions = []
    for index, (word, meaning, grammar) in enumerate(chosen):
        distractors = [w for w, _, _ in pairs if w != word]
        rng.shuffle(distractors)
        options = [word, *distractors[:3]]
        rng.shuffle(options)
        questions.append({
            "id": str(index),
            "prompt": f"Which Sanskrit word means ‘{meaning}’?",
            "options": options,
            "answer": word,
            "explanation": f"{word} — {meaning}. " + (f"Grammar note: {grammar}" if grammar else ""),
        })
    return questions


def render_learning_mode(data: dict, source: str, direction: str, user_id: str):
    st.markdown('<div class="result-heading green">📚 Learn This Sentence · Interactive Learning</div>', unsafe_allow_html=True)
    if not direction.startswith("Sanskrit"):
        st.info("Practice questions are available for Sanskrit source text. Switch to Sanskrit → English to try them.")
        return
    st.caption("Practice using the existing word analysis—no additional AI request or tokens are needed.")
    words = [w for w in data.get("words", []) if isinstance(w, dict) and w.get("word")]
    with st.expander("Step 1 · Explore sentence structure", expanded=True):
        if not words:
            st.info("No words available for this sentence.")
        else:
            for word in words[:12]:
                label = str(word.get("part_of_speech") or "Not specified")
                st.markdown(f"**{html.escape(str(word.get('word', '')))}** — {html.escape(str(word.get('meaning', '')))} · *{html.escape(label)}*")
            st.caption("Word meanings and grammatical labels are AI-generated, not independently verified.")
    with st.expander("Step 2 · Grammar in simple language", expanded=False):
        st.write(str(data.get("grammar_explanation") or "Grammar explanation not available."))
        if data.get("learning_tip"):
            st.info(str(data["learning_tip"]))
    questions = build_questions(data, source)
    if not questions:
        st.info("A quiz needs at least three distinct words with meanings. Try a longer Sanskrit sentence.")
        return
    fingerprint = hashlib.sha256((user_id + source + json.dumps(data.get("words", []), ensure_ascii=False, sort_keys=True)).encode()).hexdigest()[:20]
    if st.session_state.get("lesson_fingerprint") != fingerprint:
        st.session_state["lesson_fingerprint"] = fingerprint
        st.session_state["lesson_attempts"] = {}
    answers = st.session_state.setdefault("lesson_attempts", {})
    st.markdown("#### Step 3 · Practice your vocabulary")
    st.progress(len(answers) / len(questions), text=f"{len(answers)} of {len(questions)} questions answered")
    for index, question in enumerate(questions, start=1):
        key = question["id"]
        st.markdown(f"**Question {index}. {question['prompt']}**")
        if key in answers:
            chosen = answers[key]
            if chosen == question["answer"]:
                st.success("✓ Correct! " + question["explanation"])
            else:
                st.warning(f"Not quite. You chose {chosen}. Correct answer: {question['answer']}. {question['explanation']}")
            continue
        with st.form(f"lesson_{fingerprint}_{key}", clear_on_submit=False):
            choice = st.radio("Choose an answer", question["options"], index=None,
                              key=f"lesson_choice_{fingerprint}_{key}", label_visibility="collapsed")
            submitted = st.form_submit_button("Check answer")
        if submitted:
            if choice is None:
                st.warning("Select an answer first.")
            else:
                answers[key] = choice
                st.rerun()
    correct = sum(answers.get(q["id"]) == q["answer"] for q in questions)
    st.markdown("#### Step 4 · Your progress")
    st.metric("Quiz score", f"{correct} / {len(questions)}")
    if len(answers) == len(questions):
        st.success(f"Lesson complete! You answered {correct} out of {len(questions)} correctly.")
    if st.button("↻ Retry this lesson", key=f"lesson_reset_{fingerprint}"):
        st.session_state["lesson_attempts"] = {}
        for q in questions:
            st.session_state.pop(f"lesson_choice_{fingerprint}_{q['id']}", None)
        st.rerun()
    st.caption("Progress is stored only in this browser session; it is not yet saved to your Supabase account.")
