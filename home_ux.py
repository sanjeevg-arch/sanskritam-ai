"""v2.8.1 learner-first landing page. No new tables, keys, or API calls."""
import streamlit as st


def next_beginner_lesson(progress, lessons, starts_at=1):
    """Return first incomplete lesson at or after the selected starting point."""
    for lesson in lessons:
        if lesson['number'] >= starts_at and not progress.get(lesson['id'], {}).get('completed_at'):
            return lesson
    return None


def render_home(user):
    """Render lightweight home screen; return selected navigation destination or None."""
    from sanskrit_beginners_content import LESSONS
    from sanskrit_beginners import progress_for_current_user

    st.header("Welcome to Sanskritam AI 🪷")
    st.write("Learn Sanskrit at your own pace, or explore a passage with translation and grammar tools.")
    try:
        progress = progress_for_current_user(user)
        progress_available = True
    except Exception:
        # Landing page should remain usable even before the v2.8 SQL setup.
        progress = {}
        progress_available = False
        st.info("Lesson progress is temporarily unavailable. You can still use translation and practice.")

    completed = sum(bool(progress.get(lesson['id'], {}).get('completed_at')) for lesson in LESSONS)
    start_level = st.session_state.get('beginner_start_level', 'Start with Devanagari')
    start_at = 7 if start_level == 'I can already read Devanagari' else 1
    lesson = next_beginner_lesson(progress, LESSONS, starts_at=start_at)

    with st.container(border=True):
        st.subheader("Your next lesson")
        if lesson:
            st.markdown(f"**Lesson {lesson['number']}: {lesson['title']}**")
            st.caption("Sanskrit for Beginners · About 5–10 minutes")
        else:
            st.success("You've completed the lessons in your selected learning path!")
        st.progress(completed / len(LESSONS), text=f"{completed} of {len(LESSONS)} lessons completed")
        if st.button("📚 Continue Learning", type="primary", use_container_width=True, key="home_continue"):
            if lesson:
                # Existing lesson selectbox uses this exact label format.
                st.session_state['beginner_lesson_selection'] = (
                    f"{lesson['number']:02}. {lesson['title']} "
                    f"{'✓' if progress.get(lesson['id'], {}).get('completed_at') else ''}"
                )
            return '📚 Learn'

    first, second = st.columns(2)
    with first:
        with st.container(border=True):
            st.markdown("#### 🌐 Translate")
            st.caption("Explore Sanskrit sentences, roots, and grammar.")
            if st.button("Open Translation", use_container_width=True, key="home_translate"):
                return '🌐 Translate'
    with second:
        with st.container(border=True):
            st.markdown("#### 🧠 Practice")
            st.caption("Review flashcards and strengthen grammar.")
            if st.button("Open Practice", use_container_width=True, key="home_practice"):
                return '🧠 Practice'

    st.markdown("#### Your progress")
    a, b = st.columns(2)
    a.metric("Lessons completed", f"{completed}/{len(LESSONS)}" if progress_available else "Unavailable")
    b.metric("Lessons remaining", str(len(LESSONS) - completed) if progress_available else "Unavailable")
    st.caption("Your detailed learning dashboard is available below.")
    return None
