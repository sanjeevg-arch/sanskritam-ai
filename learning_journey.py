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
    done = lesson['id'] in data['completed_ids']
    current = bool(data['next_lesson'] and lesson['id'] == data['next_lesson']['id'])
    status = 'Completed' if done else 'Up next' if current else 'Available'
    state_class = 'is-done' if done else 'is-current' if current else 'is-available'
    st.markdown(
        f'<div class="sa-journey-tile {state_class}">'
        f'<div class="sa-journey-tile-top"><span class="sa-journey-number">{lesson["number"]:02}</span>'
        f'<span class="sa-journey-status">{html.escape(status)}</span></div>'
        f'<strong>{html.escape(lesson["title"])}</strong>'
        f'<small>{html.escape(lesson["stage"])}</small></div>',
        unsafe_allow_html=True,
    )
    if st.button('Review lesson' if done else 'Continue lesson' if current else 'Open lesson',
                 key=f'journey_lesson_{lesson["id"]}', use_container_width=True,
                 type='primary' if current else 'secondary'):
        open_lesson(lesson, progress)


def render_learning_journey(user):
    st.markdown(
        '<section class="sa-journey-hero"><div class="sa-eyebrow">YOUR LEARNING JOURNEY</div>'
        '<h1>Every lesson brings you closer.</h1>'
        '<p>See your progress, pick up where you left off, and explore Sanskrit at your own pace.</p>'
        '</section>', unsafe_allow_html=True,
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

    st.markdown('### Your progress')
    stats = st.columns(3, gap='small')
    with stats[0]:
        _metric('Lessons completed', f'{completed} / {total}', f'{percent}% complete')
    with stats[1]:
        _metric('Devanagari', f'{data["script_completed"]} / 6', 'Script foundations')
    with stats[2]:
        _metric('Sanskrit essentials', f'{data["core_completed"]} / 12', 'Beyond the script')
    st.progress(completed / total if total else 0, text=f'{percent}% of the 18-lesson curriculum complete')

    st.markdown('### Continue your journey')
    next_lesson = data['next_lesson']
    with st.container(border=True):
        if next_lesson:
            st.caption('YOUR NEXT LESSON')
            st.markdown(f'#### {next_lesson["number"]:02}. {next_lesson["title"]}')
            st.write(next_lesson.get('description', 'Continue building your Sanskrit skills.'))
            st.caption('Learn → Explore → Practice → Review')
            if st.button('Continue learning →', key='journey_continue', type='primary', use_container_width=True):
                open_lesson(next_lesson, progress)
        else:
            st.success('You have completed your selected learning path. Excellent progress!')
            if st.button('Review the curriculum →', key='journey_review', use_container_width=True):
                open_lesson(LESSONS[6] if skip else LESSONS[0], progress)

    st.markdown('### Explore the lesson roadmap')
    st.caption('Choose any lesson to begin or review. Lessons are always available, including Devanagari foundations.')
    phase = st.segmented_control('Roadmap section',
        options=['All lessons', 'Devanagari', 'Sanskrit essentials'],
        default='All lessons', key='journey_phase_filter')
    phases = [
        ('01', 'Devanagari foundations', LESSONS[:6]),
        ('02', 'Sanskrit essentials', LESSONS[6:]),
    ]
    for index, title, lessons in phases:
        if phase == 'Devanagari' and index != '01':
            continue
        if phase == 'Sanskrit essentials' and index != '02':
            continue
        finished = sum(lesson['id'] in data['completed_ids'] for lesson in lessons)
        st.markdown(f'#### {index} · {title}  ·  {finished}/{len(lessons)}')
        # Compact 3-column visual tiles on desktop; Streamlit stacks columns on narrow screens.
        for start in range(0, len(lessons), 3):
            cols = st.columns(3, gap='small')
            for col, lesson in zip(cols, lessons[start:start + 3]):
                with col:
                    _lesson_tile(lesson, data, progress)

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
