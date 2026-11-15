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


def render_sanskrit_beginners(user):
    with st.expander('📚 Sanskrit for Beginners · 18 guided lessons', expanded=False):
        st.caption('Start with Devanagari or jump to Lesson 7 if you already read the script. Lessons and quizzes do not consume OpenAI tokens.')
        try:
            progress = progress_for_current_user(user)
        except BetaError as exc:
            st.warning('Progress tracking is not available yet. Run sanskrit_beginners_setup.sql in Supabase, then reload. ' + str(exc))
            return
        completed = sum(1 for x in progress.values() if x.get('completed_at'))
        st.progress(completed / len(LESSONS), text=f'{completed} of {len(LESSONS)} lessons completed')
        level_key = 'beginner_start_level'
        if level_key not in st.session_state:
            st.session_state[level_key] = 'Start with Devanagari'
        choice = st.radio('Your starting point', ['Start with Devanagari','I can already read Devanagari'],
                          key=level_key, horizontal=True)
        default_lesson = 'beginner-07' if choice.startswith('I can') else 'beginner-01'
        options = {f"{lesson['number']:02}. {lesson['title']} {'✓' if lesson['id'] in progress and progress[lesson['id']].get('completed_at') else ''}":lesson['id'] for lesson in LESSONS}
        labels = list(options)
        lesson_key = 'beginner_lesson_selection'
        if lesson_key not in st.session_state:
            st.session_state[lesson_key] = next(k for k,v in options.items() if v == default_lesson)
        if st.session_state[lesson_key] not in options:
            previous = re.match(r'^\d+', st.session_state[lesson_key])
            number = int(previous.group()) if previous else int(default_lesson[-2:])
            st.session_state[lesson_key] = next((k for k,v in options.items() if int(v[-2:]) == number),labels[0])
        label = st.selectbox('Choose a lesson', labels, key=lesson_key)
        lesson = LESSON_BY_ID[options[label]]
        st.markdown(f"#### Lesson {lesson['number']}: {lesson['title']}")
        st.caption(f"Stage: {lesson['stage']} · Approximately 5–10 minutes")
        st.write(lesson['description'])
        show_iast = st.session_state.get('access_iast', True)
        for item in lesson['examples']:
            st.markdown('**' + item['devanagari'] + '**' + (' · *'+item['iast']+'*' if show_iast else '') + ' — ' + item['meaning'])
        st.markdown('##### Quick check')
        answer_prefix = 'beginners_answer_' + lesson['id'] + '_'
        selected = []
        for idx,q in enumerate(lesson['questions']):
            answer = st.radio(f"{idx+1}. {q['prompt']}", q['options'], index=None,
                              key=answer_prefix+str(idx))
            selected.append(answer)
        result_key = 'beginners_result_'+lesson['id']
        if st.button('Check answers and save progress', key='beginners_check_'+lesson['id'],
                     disabled=any(a is None for a in selected), use_container_width=True, type='primary'):
            score = sum(q['options'].index(a)==q['answer'] for q,a in zip(lesson['questions'],selected))
            try:
                save_lesson_attempt(user,lesson['id'],score,len(selected))
            except (BetaError,ValueError) as exc:
                st.error('Could not save progress: '+str(exc))
            else:
                st.session_state[result_key] = score
                st.rerun()
        if result_key in st.session_state:
            score = st.session_state[result_key]
            st.success(f'Saved! {score}/{len(lesson["questions"])} correct.' if score == len(lesson['questions']) else f'Saved: {score}/{len(lesson["questions"])}. Review and retry to improve.')
            for q in lesson['questions']:
                st.caption(q['explanation'])
        st.caption('A lesson is marked completed when you answer at least 2 of 3 questions correctly. You can retry anytime.')
