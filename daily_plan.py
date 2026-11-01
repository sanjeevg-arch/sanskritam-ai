"""Personalized daily study plan. Deterministic, no additional AI requests."""
from datetime import datetime, timezone
from urllib.parse import quote
import uuid
import streamlit as st
from private_beta import _request, BetaError
from flashcards import _cards
from learning_dashboard import _load_attempts


def _user_id(user):
    return str(uuid.UUID(str(user["id"])))


def _progress(user, day):
    uid = quote(_user_id(user), safe="")
    result = _request("GET", "/rest/v1/daily_learning_progress?select=task_key"
                      + f"&user_id=eq.{uid}&study_day=eq.{day}", service=True)
    return {row["task_key"] for row in (result or [])}


def _mark(user, day, task):
    # An RPC handles duplicates safely without relying on _request(prefer=...).
    return _request("POST", "/rest/v1/rpc/complete_daily_learning_task", service=True,
                    payload={"p_user_id": _user_id(user), "p_study_day": day,
                             "p_task_key": task})


def _due(card, now):
    try:
        return datetime.fromisoformat(str(card["next_review"]).replace("Z", "+00:00")) <= now
    except (KeyError, ValueError, TypeError):
        return True


def render_daily_plan(user):
    with st.expander("🌅 My Daily Learning Plan", expanded=False):
        st.caption("A small, personalized study routine using your saved words and quiz history. No extra AI tokens are used to build the plan. Day resets at midnight UTC.")
        today = datetime.now(timezone.utc).date().isoformat()
        try:
            cards = _cards(user)
            attempts = _load_attempts(user["id"])
            completed = _progress(user, today)
        except (BetaError, KeyError, ValueError, TypeError) as exc:
            st.warning("Daily Learning Plan is unavailable. Run daily_plan_setup.sql in Supabase and check database access.")
            st.caption(str(exc))
            return
        now = datetime.now(timezone.utc)
        due = [c for c in cards if _due(c, now)]
        # Use recent accuracy to recommend an appropriate quiz goal.
        recent = attempts[:5]
        total = sum(int(a.get("total") or 0) for a in recent)
        correct = sum(int(a.get("correct") or 0) for a in recent)
        accuracy = (correct / total) if total else None
        review_goal = min(5, len(due))
        tasks = [
            ("review", "🗂️ Review vocabulary", f"Review {review_goal} due word(s) using Smart Vocabulary Flashcards." if due else "No words due today. Practice saved cards, or add new words from Word Explorer."),
            ("translate", "📖 Explore a Sanskrit sentence", "Translate a short passage, or reopen one from Translation History and inspect its word roots and grammar."),
            ("quiz", "🧠 Practice with a quiz", "Complete one Learn This Sentence quiz. " + ("Focus on difficult words (recent accuracy below 70%)." if accuracy is not None and accuracy < 0.7 else "Aim to explain why each answer is correct.")),
        ]
        st.markdown(f"**Today's plan · {today} (UTC)**")
        st.progress(len(completed.intersection({x[0] for x in tasks})) / len(tasks))
        st.caption(f"{len(completed.intersection({x[0] for x in tasks}))} of {len(tasks)} activities marked complete")
        for key, title, description in tasks:
            with st.container(border=True):
                st.markdown("**" + title + "**")
                st.write(description)
                if key == "review" and due:
                    st.caption("Suggested review: " + " · ".join(str(c.get("word") or "") for c in due[:5]))
                if key == "quiz" and accuracy is not None:
                    st.caption(f"Recent quiz accuracy: {accuracy:.0%} across {len(recent)} attempts")
                done = key in completed
                st.button("✓ Completed" if done else "Mark complete", key="daily_plan_" + key,
                          disabled=done, on_click=_mark_task_callback,
                          args=(user, today, key))
        if st.session_state.get("daily_plan_save_error"):
            st.error("Could not save daily progress: " + st.session_state["daily_plan_save_error"])
        if not cards:
            st.info("Start by translating a sentence and saving its words as flashcards.")
        if not attempts:
            st.info("Complete a Learn This Sentence quiz to personalize your study guidance.")
        st.caption("Activities are marked complete manually. The plan does not claim to detect whether a translation or quiz was performed. Progress is saved in Supabase.")


def _mark_task_callback(user, day, key):
    try:
        _mark(user, day, key)
    except (BetaError, ValueError, TypeError, KeyError) as exc:
        st.session_state["daily_plan_save_error"] = str(exc)
    else:
        st.session_state.pop("daily_plan_save_error", None)
