"""v3.2 Interactive Learning Journey, using existing per-user beginner progress.

No new tables, no client-side credentials, no synthetic progress metrics.
"""
import streamlit as st
from sanskrit_beginners_content import LESSONS
from sanskrit_beginners import progress_for_current_user
from home_ux import next_beginner_lesson
from unified_learning import render_unified_learning


def journey_state(progress, skip_script=False):
    """Pure derived roadmap state, respecting the existing skip-script preference."""
    completed_ids = {lesson['id'] for lesson in LESSONS
                     if progress.get(lesson['id'], {}).get('completed_at')}
    first = 7 if skip_script else 1
    next_lesson = next_beginner_lesson(progress, LESSONS, starts_at=first)
    return {'completed_ids': completed_ids, 'completed': len(completed_ids),
            'total': len(LESSONS), 'next_lesson': next_lesson,
            'script_completed': sum(lesson['id'] in completed_ids for lesson in LESSONS[:6]),
            'core_completed': sum(lesson['id'] in completed_ids for lesson in LESSONS[6:])}


def _lesson_label(lesson, progress):
    done = bool(progress.get(lesson['id'], {}).get('completed_at'))
    return f"{lesson['number']:02}. {lesson['title']} {'✓' if done else ''}"


def open_lesson(lesson, progress):
    """Select the actual existing lesson widget before navigating to the Learn hub."""
    st.session_state['beginner_lesson_selection'] = _lesson_label(lesson, progress)
    st.session_state['learning_hub_section'] = 'Learn'
    st.session_state['navigation_menu_open'] = False
    st.session_state['pending_navigation'] = '📚 Learn & Practice'
    st.rerun()


def render_learning_journey(user):
    st.markdown("""<section class="sa-page-intro"><div class="sa-eyebrow">YOUR LEARNING JOURNEY</div><h1>Small steps. Lasting progress<span class="sa-accent">.</span></h1><p>Follow your own path through Sanskrit, revisit completed lessons, and choose what to learn next.</p></section>""", unsafe_allow_html=True)
    try:
        progress = progress_for_current_user(user)
    except Exception:
        st.warning('Your lesson progress could not be loaded. Please retry after checking your connection and account access.')
        if st.button('Open Learn & Practice', key='journey_fallback_learn'):
            st.session_state['pending_navigation'] = '📚 Learn & Practice'
            st.rerun()
        return

    skip = st.session_state.get('beginner_start_level') == 'I can already read Devanagari'
    data = journey_state(progress, skip_script=skip)
    completed = data['completed']
    st.markdown('### Your progress at a glance')
    a, b, c = st.columns(3)
    a.metric('Lessons completed', f"{completed}/{data['total']}")
    b.metric('Devanagari foundations', f"{data['script_completed']}/6")
    c.metric('Beyond the script', f"{data['core_completed']}/{data['total']-6}")
    st.progress(completed / data['total'], text=f"{round(100*completed/data['total'])}% of all lessons completed")

    lesson = data['next_lesson']
    with st.container(border=True):
        st.markdown('#### ✨ Your next step')
        if lesson:
            st.markdown(f"**Lesson {lesson['number']}: {lesson['title']}**")
            st.caption(f"{lesson['stage']} · Approximately 5–10 minutes · Learn → Explore → Practice → Review")
            if st.button('Continue this lesson →', key='journey_continue', type='primary', use_container_width=True):
                open_lesson(lesson, progress)
        else:
            st.success('All lessons in your chosen starting path are complete! You can revisit any lesson below.')
            if st.button('Review lessons →', key='journey_review', use_container_width=True):
                open_lesson(LESSONS[6] if skip else LESSONS[0], progress)

    st.markdown('### Your lesson roadmap')
    st.caption('Select any lesson to start or review it. You can skip the Devanagari foundations if you already read the script.')
    for heading, lessons in [('01 · Devanagari foundations', LESSONS[:6]),
                             ('02 · Sanskrit essentials', LESSONS[6:])]:
        st.markdown(f'#### {heading}')
        for lesson in lessons:
            done = lesson['id'] in data['completed_ids']
            current = lesson == data['next_lesson']
            label = ('✓ Completed' if done else '● Up next' if current else '○ Not completed')
            with st.container(border=True):
                title_col, action_col = st.columns([4, 1], vertical_alignment='center')
                with title_col:
                    st.markdown(f"**{lesson['number']:02}. {lesson['title']}**")
                    st.caption(f"{lesson['stage']} · {label}")
                with action_col:
                    if st.button('Review' if done else 'Open lesson', key=f"journey_lesson_{lesson['id']}", use_container_width=True):
                        open_lesson(lesson, progress)

    st.markdown('### Milestones')
    for label, achieved, goal in [
        ('Read the script', data['script_completed'], 6),
        ('First Sanskrit lesson beyond the script', data['core_completed'], 1),
        ('Halfway through the curriculum', completed, 9),
        ('Complete the beginner curriculum', completed, data['total']),
    ]:
        st.markdown(f"{'✅' if achieved >= goal else '◯'} **{label}**")
        st.caption(f'{min(achieved, goal)} of {goal} required lessons')

    st.markdown('### Your wider learning activity')
    st.caption('Flashcards, grammar, quizzes and daily-plan progress are shown using your existing learning records.')
    render_unified_learning(user)
