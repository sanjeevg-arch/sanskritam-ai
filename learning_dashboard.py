"""Private per-user learning analytics; all database calls run server-side."""
from collections import Counter
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
import uuid
import streamlit as st
from private_beta import _request, BetaError


def record_lesson_attempt(user_id, lesson_key, source, correct, total):
    uid = str(uuid.UUID(user_id))
    if not 0 <= correct <= total <= 5 or total == 0:
        raise ValueError("Invalid lesson score")
    payload = {"id": str(uuid.uuid4()), "user_id": uid,
               "lesson_key": lesson_key, "source_preview": source[:180],
               "correct": correct, "total": total}
    return _request("POST", "/rest/v1/learning_attempts", service=True, payload=payload)


def _load_attempts(user_id):
    uid = quote(str(uuid.UUID(user_id)), safe="")
    path = ("/rest/v1/learning_attempts?select=id,lesson_key,source_preview,correct,total,completed_at"
            f"&user_id=eq.{uid}&order=completed_at.desc&limit=500")
    result = _request("GET", path, service=True)
    return result if isinstance(result, list) else []


def render_dashboard(user):
    with st.expander("📊 My Learning Dashboard", expanded=False):
        st.caption("Your personal quiz progress. Only you can see your learning activity; no AI tokens are used.")
        try:
            rows = _load_attempts(user["id"])
        except (BetaError, ValueError, KeyError):
            st.warning("Learning dashboard is unavailable. Run dashboard_setup.sql in Supabase.")
            return
        if not rows:
            st.info("Complete a quiz in ‘Learn This Sentence’ to begin tracking your progress.")
            return
        attempts = len(rows)
        unique_lessons = len({r.get("lesson_key") for r in rows})
        answered = sum(int(r.get("total") or 0) for r in rows)
        correct = sum(int(r.get("correct") or 0) for r in rows)
        percent = round(100 * correct / answered) if answered else 0
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Quiz attempts", attempts)
        c2.metric("Lessons practiced", unique_lessons)
        c3.metric("Questions answered", answered)
        c4.metric("Accuracy", f"{percent}%")
        days = set()
        for r in rows:
            try:
                day = datetime.fromisoformat(str(r["completed_at"]).replace("Z", "+00:00")).date()
                days.add(day)
            except (KeyError, ValueError, TypeError):
                pass
        today = datetime.now(timezone.utc).date()
        streak = 0
        cursor = today if today in days else today - timedelta(days=1)
        while cursor in days:
            streak += 1
            cursor -= timedelta(days=1)
        st.metric("Practice streak (UTC days)", f"{streak} day{'s' if streak != 1 else ''}")
        st.markdown("**Recent practice**")
        for r in rows[:8]:
            date = str(r.get("completed_at") or "")[:10]
            st.write(f"{date} · {r.get('correct', 0)}/{r.get('total', 0)} correct · {str(r.get('source_preview') or '')[:70]}")
        if attempts >= 3:
            last = rows[:3]
            last_correct = sum(int(r.get("correct") or 0) for r in last)
            last_total = sum(int(r.get("total") or 0) for r in last)
            if last_total and last_correct / last_total < 0.7:
                st.info("Learning tip: revisit Word Explorer and retry a few vocabulary questions.")
            else:
                st.success("Keep practicing! Try longer Sanskrit passages to build vocabulary.")
        st.caption("Dashboard shows your 500 most recent attempts. Streak uses UTC calendar days; quiz accuracy is based on AI-generated vocabulary.")
