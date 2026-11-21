"""Visual Learning Journey: 18-lesson roadmap backed by existing learner progress.

The UI never fabricates progress or writes to the database. It reuses the
existing authenticated learner progress and lesson selection behavior.
"""
import html
import streamlit as st
from sanskrit_beginners_content import LESSONS
from sanskrit_beginners import progress_for_current_user
from home_ux import next_beginner_lesson
from unified_learning import render_unified_learning


def journey_state(progress, skip_script=False):
    completed_ids = {lesson['id'] for lesson in LESSONS
                     if progress.get(lesson['id'], {}).get('completed_at')}
    next_lesson = next_beginner_lesson(progress, LESSONS, starts_at=7 if skip_script else 1)
    return {
        'completed_ids': completed_ids,
        'completed': len(completed_ids),
        'total': len(LESSONS),
        'next_lesson': next_lesson,
        'script_completed': sum(lesson['id'] in completed_ids for lesson in LESSONS[:6]),
        'core_completed': sum(lesson['id'] in completed_ids for lesson in LESSONS[6:]),
    }


def _lesson_label(lesson, progress):
    done = bool(progress.get(lesson['id'], {}).get('completed_at'))
    return f"{lesson['number']:02}. {lesson['title']} {'✓' if done else ''}"


def open_lesson(lesson, progress):
    st.session_state['beginner_lesson_selection'] = _lesson_label(lesson, progress)
    st.session_state['learning_hub_section'] = 'Learn'
    st.session_state['navigation_menu_open'] = False
    st.session_state['pending_navigation'] = '📚 Learn & Practice'
    st.rerun()


def _metric(label, value, detail):
    st.markdown(
        f'<div class="sa-journey-stat"><span>{html.escape(label)}</span>'
        f'<strong>{html.escape(str(value))}</strong><small>{html.escape(detail)}</small></div>',
        unsafe_allow_html=True,
    )


def _milestone(label, achieved, goal, description):
    done = achieved >= goal
    icon = '✓' if done else '◇'
    status = 'Achieved' if done else f'{min(achieved, goal)} / {goal}'
    st.markdown(
        f'<div class="sa-journey-milestone {"is-done" if done else ""}">'
        f'<div class="sa-journey-milestone-icon">{icon}</div>'
        f'<div><strong>{html.escape(label)}</strong><p>{html.escape(description)}</p>'
        f'<span>{html.escape(status)}</span></div></div>',
        unsafe_allow_html=True,
    )


def _lesson_tile(lesson, data, progress):
    """Small, genuinely clickable tile. Later lessons are available, not locked."""
    done = lesson['id'] in data['completed_ids']
    current = bool(data['next_lesson'] and lesson['id'] == data['next_lesson']['id'])
    icon = '✓' if done else '◉' if current else '○'
    st.markdown(
        f'<div class="sa-journey-compact-tile {"is-done" if done else "is-current" if current else ""}" '
        f'title="{html.escape(lesson["title"], quote=True)}">'
        f'<span>{icon}</span><strong>{lesson["number"]}</strong></div>',
        unsafe_allow_html=True,
    )
    if st.button('Review' if done else 'Start', key=f'journey_lesson_{lesson["id"]}',
                 use_container_width=True, type='primary' if current else 'secondary',
                 help=f'Open Lesson {lesson["number"]}: {lesson["title"]}'):
        open_lesson(lesson, progress)


def render_learning_journey(user):
    st.markdown(
        '<section class="sa-journey-prototype-heading"><h2>🪷 Your Learning Journey</h2>'
        '<p>Your path to understanding Sanskrit</p></section>', unsafe_allow_html=True,
    )
    try:
        progress = progress_for_current_user(user)
    except Exception:
        st.warning('Your lesson progress could not be loaded. Please retry after checking your connection and account access.')
        if st.button('Open Learn & Practice', key='journey_fallback_learn'):
            st.session_state['navigation_menu_open'] = False
            st.session_state['pending_navigation'] = '📚 Learn & Practice'
            st.rerun()
        return

    skip = st.session_state.get('beginner_start_level') == 'I can already read Devanagari'
    data = journey_state(progress, skip_script=skip)
    completed, total = data['completed'], data['total']
    percent = round(100 * completed / total) if total else 0

    st.markdown('<div class="sa-journey-kicker">YOUR PROGRESS</div>', unsafe_allow_html=True)
    stats = st.columns(3, gap='small')
    with stats[0]:
        _metric('Lessons', f'{completed}/{total}', 'Completed')
    with stats[1]:
        _metric('Complete', f'{percent}%', 'Curriculum')
    with stats[2]:
        milestone_count = sum((data['script_completed'] >= 6, data['core_completed'] >= 1,
                               completed >= 9, completed >= total))
        _metric('Milestones', milestone_count, 'Of 4 achieved')
    st.progress(completed / total if total else 0, text=f'{completed} of {total} lessons complete')

    st.markdown('### Your lesson roadmap')
    st.caption('Select any lesson to begin or review. All 18 lessons are available; later lessons are not locked.')
    for title, lessons in [('Devanagari foundations', LESSONS[:6]),
                           ('Sanskrit essentials', LESSONS[6:])]:
        st.markdown(f'**{title}**')
        for start in range(0, len(lessons), 6):
            cols = st.columns(6, gap='small')
            for col, lesson in zip(cols, lessons[start:start + 6]):
                with col:
                    _lesson_tile(lesson, data, progress)

    next_lesson = data['next_lesson']
    with st.container(border=True):
        if next_lesson:
            st.caption('UP NEXT · YOUR NEXT LESSON')
            st.markdown(f'#### {next_lesson["number"]:02}. {next_lesson["title"]}')
            st.write(next_lesson.get('description', 'Continue building your Sanskrit skills.'))
            st.caption('Learn → Explore → Practice → Review')
            if st.button('Continue learning →', key='journey_continue', type='primary', use_container_width=True):
                open_lesson(next_lesson, progress)
        else:
            st.success('You have completed your selected learning path. Excellent progress!')
            if st.button('Review the curriculum →', key='journey_review', use_container_width=True):
                open_lesson(LESSONS[6] if skip else LESSONS[0], progress)

    st.markdown('### Milestones worth celebrating')
    milestones = [
        ('Script explorer', data['script_completed'], 6, 'Complete all six Devanagari lessons'),
        ('First Sanskrit steps', data['core_completed'], 1, 'Finish your first essentials lesson'),
        ('Halfway there', completed, 9, 'Complete nine lessons'),
        ('Beginner journey complete', completed, total, 'Finish all eighteen lessons'),
    ]
    for start in range(0, len(milestones), 2):
        cols = st.columns(2, gap='small')
        for col, item in zip(cols, milestones[start:start + 2]):
            with col:
                _milestone(*item)

    with st.expander('See your wider learning activity', expanded=False):
        st.caption('Flashcards, grammar, quizzes and daily-plan progress from your existing learning records.')
        render_unified_learning(user)
