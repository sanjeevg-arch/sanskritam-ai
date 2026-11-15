"""Sanskrit for Beginners: guided, low-cost curated lessons and owner-scoped progress."""
import re
from urllib.parse import quote
import streamlit as st
from private_beta import _request, BetaError
from sanskrit_beginners_content import LESSONS

LESSON_BY_ID = {lesson['id']: lesson for lesson in LESSONS}


def progress_for_current_user(user):
    """Use the signed-in learner's JWT, not the service role, so Supabase RLS applies."""
    token = st.session_state.get('beta_access_token')
    if not token or not user.get('id'):
        raise BetaError('Please sign in again.')
    uid = quote(str(user['id']), safe='')
    rows = _request('GET', '/rest/v1/sanskrit_beginner_progress?select=lesson_id,best_score,attempts,completed_at&user_id=eq.' + uid,
                    token=token)
    return {row['lesson_id']: row for row in rows if row.get('lesson_id') in LESSON_BY_ID}


def save_lesson_attempt(user, lesson_id, score, total):
    """An authenticated JWT and an owner-only RLS policy protect this write."""
    if lesson_id not in LESSON_BY_ID or not 0 <= score <= total or total != len(LESSON_BY_ID[lesson_id]['questions']):
        raise ValueError('Invalid lesson score.')
    token = st.session_state.get('beta_access_token')
    if not token or not user.get('id'):
        raise BetaError('Please sign in again.')
    # Database RPC uses auth.uid() and derives user_id from the verified JWT.
    # Client cannot choose which account receives progress.
    result = _request('POST', '/rest/v1/rpc/record_beginner_attempt', token=token,
                      payload={'p_lesson_id': lesson_id, 'p_score': score, 'p_total': total})
    return result




def _lesson_label(lesson, progress):
    mark = '✓' if progress.get(lesson['id'], {}).get('completed_at') else ''
    return f"{lesson['number']:02}. {lesson['title']} {mark}"


def _step_key(lesson_id):
    return 'beginners_step_' + lesson_id


def _go_to_step(lesson_id, step):
    st.session_state[_step_key(lesson_id)] = step


def render_sanskrit_beginners(user):
    """Four focused screens: Learn, Examples, Practice, and Review."""
    st.subheader('📚 Sanskrit for Beginners')
    st.caption('18 short lessons · Learn → Explore → Practice → Review · No OpenAI tokens used')
    try:
        progress = progress_for_current_user(user)
    except BetaError as exc:
        st.warning('Progress unavailable. Check the existing sanskrit_beginners_setup.sql migration. ' + str(exc))
        return

    completed = sum(bool(x.get('completed_at')) for x in progress.values())
    st.progress(completed / len(LESSONS), text=f'{completed} of {len(LESSONS)} lessons completed')
    level_key = 'beginner_start_level'
    if level_key not in st.session_state:
        st.session_state[level_key] = 'Start with Devanagari'
    choice = st.radio('Your starting point', ['Start with Devanagari', 'I can already read Devanagari'],
                      key=level_key, horizontal=True)
    default_id = 'beginner-07' if choice.startswith('I can') else 'beginner-01'
    labels_to_ids = {_lesson_label(lesson, progress): lesson['id'] for lesson in LESSONS}
    labels = list(labels_to_ids)
    lesson_key = 'beginner_lesson_selection'
    if lesson_key not in st.session_state:
        st.session_state[lesson_key] = next(k for k,v in labels_to_ids.items() if v == default_id)
    if st.session_state[lesson_key] not in labels_to_ids:
        old = re.match(r'^\d+', str(st.session_state[lesson_key]))
        number = int(old.group()) if old else int(default_id[-2:])
        st.session_state[lesson_key] = next((k for k,v in labels_to_ids.items() if int(v[-2:]) == number), labels[0])
    selected_label = st.selectbox('Choose a lesson', labels, key=lesson_key)
    lesson = LESSON_BY_ID[labels_to_ids[selected_label]]
    lesson_id = lesson['id']
    steps = ['Learn', 'Explore', 'Practice', 'Review']
    step_key = _step_key(lesson_id)
    if st.session_state.get(step_key) not in steps:
        st.session_state[step_key] = 'Learn'
    step = st.session_state[step_key]
    step_index = steps.index(step)
    st.markdown(f"### Lesson {lesson['number']}: {lesson['title']}")
    st.caption(f"{lesson['stage']} · About 5–10 minutes · Step {step_index + 1} of 4")
    st.progress((step_index + 1) / len(steps))
    st.markdown(' · '.join(('**' + name + '**') if name == step else name for name in steps))
    show_iast = st.session_state.get('access_iast', True)

    if step == 'Learn':
        with st.container(border=True):
            st.markdown('#### The idea')
            st.write(lesson['description'])
            st.caption('Read the explanation, then explore the examples.')
        st.button('Explore examples →', type='primary', use_container_width=True,
                  on_click=_go_to_step, args=(lesson_id, 'Explore'), key=f'beginner_next_learn_{lesson_id}')

    elif step == 'Explore':
        st.markdown('#### Look, read, and understand')
        for item in lesson['examples']:
            with st.container(border=True):
                st.markdown(f"### {item['devanagari']}")
                if show_iast:
                    st.caption(item['iast'])
                st.write(item['meaning'])
        a,b = st.columns(2)
        a.button('← Back', use_container_width=True, on_click=_go_to_step,
                 args=(lesson_id, 'Learn'), key=f'beginner_back_explore_{lesson_id}')
        b.button('Start practice →', type='primary', use_container_width=True,
                 on_click=_go_to_step, args=(lesson_id, 'Practice'), key=f'beginner_next_explore_{lesson_id}')

    elif step == 'Practice':
        st.markdown('#### Quick check')
        st.caption('Choose an answer for each question. You can retry without penalty.')
        answer_prefix = 'beginners_answer_' + lesson_id + '_'
        answers = []
        for idx, q in enumerate(lesson['questions']):
            with st.container(border=True):
                answer = st.radio(f"{idx + 1}. {q['prompt']}", q['options'], index=None,
                                  key=answer_prefix + str(idx))
                answers.append(answer)
        a,b = st.columns(2)
        a.button('← Examples', use_container_width=True, on_click=_go_to_step,
                 args=(lesson_id, 'Explore'), key=f'beginner_back_practice_{lesson_id}')
        if b.button('Check answers →', type='primary', use_container_width=True,
                    disabled=any(x is None for x in answers), key=f'beginner_check_{lesson_id}'):
            score = sum(q['options'].index(answer) == q['answer']
                        for q,answer in zip(lesson['questions'],answers))
            try:
                save_lesson_attempt(user, lesson_id, score, len(answers))
            except (BetaError, ValueError) as exc:
                st.error('Could not save progress: ' + str(exc))
            else:
                # Save the answers that were actually submitted, not later edits.
                st.session_state['beginners_review_' + lesson_id] = {
                    'score': score, 'answers': list(answers)}
                st.session_state[step_key] = 'Review'
                st.rerun()

    else:
        review = st.session_state.get('beginners_review_' + lesson_id)
        if not review:
            st.info('Complete the practice questions to see your review.')
            st.button('Go to practice', on_click=_go_to_step, args=(lesson_id, 'Practice'))
            return
        score = review['score']
        total = len(lesson['questions'])
        if score >= 2:
            st.success(f'Lesson completed! {score}/{total} correct. Your progress was saved.')
        else:
            st.info(f'{score}/{total} correct. Review the explanations and try again.')
        for idx, (q, answer) in enumerate(zip(lesson['questions'], review['answers'])):
            correct = q['options'][q['answer']]
            with st.container(border=True):
                st.markdown(f"**{idx + 1}. {q['prompt']}**")
                if answer == correct:
                    st.success(f'Correct: {correct}')
                else:
                    st.error(f'Your answer: {answer}')
                    st.write(f'Correct answer: **{correct}**')
                st.caption(q['explanation'])
        a,b = st.columns(2)
        if a.button('Retry practice', use_container_width=True, key=f'beginner_retry_{lesson_id}'):
            for idx in range(total):
                st.session_state.pop('beginners_answer_' + lesson_id + '_' + str(idx), None)
            st.session_state.pop('beginners_review_' + lesson_id, None)
            st.session_state[step_key] = 'Practice'
            st.rerun()
        next_index = lesson['number']
        if next_index < len(LESSONS):
            if b.button('Next lesson →', type='primary', use_container_width=True,
                        key=f'beginner_next_lesson_{lesson_id}'):
                next_lesson = LESSONS[next_index]
                st.session_state[lesson_key] = _lesson_label(next_lesson, progress)
                st.session_state[_step_key(next_lesson['id'])] = 'Learn'
                st.rerun()
        else:
            b.info('You reached the final lesson!')
