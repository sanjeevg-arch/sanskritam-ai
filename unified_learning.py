"""v2.9: Read-only, per-user unified learning snapshot and deterministic study suggestions.

Uses existing tables; each source can fail independently. No new AI requests.
"""
from datetime import datetime, timezone
import streamlit as st
from private_beta import BetaError
from sanskrit_beginners import progress_for_current_user
from sanskrit_beginners_content import LESSONS
from grammar_lab import _attempts as grammar_attempts, BANK
from flashcards import _cards
from learning_dashboard import _load_attempts
from daily_plan import _progress as daily_progress, _due


def summarize(progress, grammar, cards, quizzes, daily, now=None):
    """Pure aggregation; absent sources are None, not misleading zeroes."""
    now = now or datetime.now(timezone.utc)
    completed = None if progress is None else sum(
        bool(progress.get(lesson['id'], {}).get('completed_at')) for lesson in LESSONS)
    due = None if cards is None else sum(_due(card, now) for card in cards)
    grammar_total = None if grammar is None else sum(int(x.get('total') or 0) for x in grammar)
    grammar_correct = None if grammar is None else sum(int(x.get('correct') or 0) for x in grammar)
    quiz_total = None if quizzes is None else sum(int(x.get('total') or 0) for x in quizzes)
    quiz_correct = None if quizzes is None else sum(int(x.get('correct') or 0) for x in quizzes)
    return {
        'completed': completed,
        'lesson_count': len(LESSONS),
        'saved_words': None if cards is None else len(cards),
        'due_words': due,
        'grammar_sessions': None if grammar is None else len(grammar),
        'grammar_accuracy': None if not grammar_total else grammar_correct / grammar_total,
        'quiz_attempts': None if quizzes is None else len(quizzes),
        'quiz_accuracy': None if not quiz_total else quiz_correct / quiz_total,
        'daily_done': None if daily is None else len(set(daily).intersection({'review','translate','quiz'})),
    }


def recommendation(summary, progress, grammar):
    """Return (description, navigation target), with actionable priorities."""
    if summary['due_words'] is not None and summary['due_words'] > 0:
        return (f"Review {min(summary['due_words'], 5)} due vocabulary cards.", '🧠 Practice')
    if summary['completed'] is not None and summary['completed'] < summary['lesson_count']:
        for lesson in LESSONS:
            if not progress.get(lesson['id'], {}).get('completed_at'):
                return (f"Continue Lesson {lesson['number']}: {lesson['title']}.", '📚 Learn')
    if summary['grammar_accuracy'] is not None and summary['grammar_accuracy'] < .7:
        return ('Review grammar fundamentals and retry a practice topic.', '🧠 Practice')
    if summary['quiz_accuracy'] is not None and summary['quiz_accuracy'] < .7:
        return ('Translate a short sentence and retry its vocabulary quiz.', '🌐 Translate')
    return ('Try a short Sanskrit sentence, then practice its vocabulary.', '🌐 Translate')


def load_snapshot(user):
    """Load only data for the authenticated user; never cache across accounts."""
    uid = user['id']
    today = datetime.now(timezone.utc).date().isoformat()
    sources = {
        'progress': lambda: progress_for_current_user(user),
        'grammar': lambda: grammar_attempts(user),
        'cards': lambda: _cards(user),
        'quizzes': lambda: _load_attempts(uid),
        'daily': lambda: daily_progress(user, today),
    }
    values, errors = {}, []
    for name, fetch in sources.items():
        try:
            values[name] = fetch()
        except (BetaError, KeyError, ValueError, TypeError) as exc:
            values[name] = None
            errors.append(name)
    return values, errors


def render_unified_learning(user):
    st.subheader('📈 Your learning journey')
    st.caption('One view of your beginner lessons, vocabulary, grammar, quizzes, and daily activities.')
    data, unavailable = load_snapshot(user)
    summary = summarize(**data)
    a, b, c = st.columns(3)
    a.metric('Beginner lessons', '—' if summary['completed'] is None else f"{summary['completed']}/{summary['lesson_count']}")
    b.metric('Saved words', '—' if summary['saved_words'] is None else summary['saved_words'])
    c.metric('Words due', '—' if summary['due_words'] is None else summary['due_words'])
    d, e, f = st.columns(3)
    d.metric('Grammar sessions', '—' if summary['grammar_sessions'] is None else summary['grammar_sessions'])
    e.metric('Sentence quizzes', '—' if summary['quiz_attempts'] is None else summary['quiz_attempts'])
    f.metric('Today’s activities', '—' if summary['daily_done'] is None else f"{summary['daily_done']}/3")
    if summary['completed'] is not None:
        st.progress(summary['completed'] / summary['lesson_count'])
    with st.expander('Practice accuracy', expanded=False):
        for label, value in [('Grammar', summary['grammar_accuracy']), ('Sentence quizzes', summary['quiz_accuracy'])]:
            st.write(f"{label}: {'Not enough data' if value is None else f'{value:.0%}'}")
    if unavailable:
        st.info('Some progress sources are unavailable: ' + ', '.join(unavailable) + '. Other results remain available.')
    suggestion, destination = recommendation(summary, data['progress'] or {}, data['grammar'] or [])
    st.markdown('**Recommended next activity**')
    st.write(suggestion)
    if st.button('Go to recommended activity →', key='unified_go_recommendation', use_container_width=True):
        st.session_state['pending_navigation'] = destination
        st.rerun()
    st.caption('Recommendations use saved activity, not AI. Counts are limited by each module’s existing history query.')
