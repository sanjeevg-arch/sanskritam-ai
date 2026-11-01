"""Server-side flashcard storage and deterministic spaced repetition. No AI calls."""
import uuid
from datetime import datetime, timezone
from urllib.parse import quote
import streamlit as st
from private_beta import _request, BetaError


def _uid(user):
    return str(uuid.UUID(str(user["id"])))


def _cards(user):
    uid = quote(_uid(user), safe="")
    path = ("/rest/v1/vocabulary_cards?select=id,word,meaning,lemma,grammar,"
            "next_review,interval_days,ease,repetitions,review_count,created_at"
            f"&user_id=eq.{uid}&order=next_review.asc&limit=500")
    result = _request("GET", path, service=True)
    return result if isinstance(result, list) else []


def save_words(user, words):
    """Save up to 12 analyzed words, ignoring existing entries for this user."""
    uid = _uid(user)
    rows = []
    seen = set()
    for w in words[:12]:
        if not isinstance(w, dict):
            continue
        word = str(w.get("word") or "").strip()[:120]
        meaning = str(w.get("meaning") or "").strip()[:240]
        if not word or not meaning or word in seen:
            continue
        seen.add(word)
        # Deterministic ID prevents duplicate cards and preserves existing review progress.
        card_id = str(uuid.uuid5(uuid.NAMESPACE_URL, uid + ":" + word))
        rows.append({"id": card_id, "user_id": uid, "word": word,
                     "meaning": meaning, "lemma": str(w.get("lemma") or "")[:120],
                     "grammar": str(w.get("grammar") or "")[:400]})
    if not rows:
        return 0
    # RPC performs INSERT ... ON CONFLICT DO NOTHING on the database side.
    # Unlike the old REST call, this does not depend on private_beta._request(prefer=...).
    result = _request("POST", "/rest/v1/rpc/save_vocabulary_words", service=True,
                      payload={"p_user_id": uid, "p_words": rows})
    return int(result or 0)


def grade_card(user, card, rating):
    if rating not in ("Again", "Hard", "Easy"):
        raise ValueError("Invalid rating")
    uid = _uid(user)
    card_id = str(uuid.UUID(str(card["id"])))
    # Database RPC validates ownership and calculates the next due date atomically.
    return _request("POST", "/rest/v1/rpc/review_vocabulary_card", service=True,
                    payload={"p_user_id": uid, "p_card_id": card_id, "p_rating": rating})


def render_flashcards(user, words=None, *, widget_id="review"):
    """Unique widget keys allow both the dashboard and lesson sections to render."""
    prefix = "flash_" + widget_id + "_"
    with st.expander("🗂️ Smart Vocabulary Flashcards", expanded=False):
        st.caption("Save Sanskrit words from Word Explorer, then review them with spaced repetition. No extra AI tokens are used.")
        if words:
            if st.button("＋ Save these words as flashcards", key=prefix + "save_words", use_container_width=True):
                try:
                    count = save_words(user, words)
                    st.success(f"Saved {count} new vocabulary cards. Existing cards and review progress were preserved.")
                except (BetaError, ValueError, KeyError, TypeError) as exc:
                    st.error(f"Unable to save cards: {exc}")
        try:
            cards = _cards(user)
        except (BetaError, ValueError, KeyError):
            st.warning("Flashcards are unavailable. Run flashcards_setup.sql in Supabase, then refresh.")
            return
        now = datetime.now(timezone.utc)
        def due(card):
            try:
                return datetime.fromisoformat(str(card["next_review"]).replace("Z", "+00:00")) <= now
            except (ValueError, TypeError):
                return True
        pending = [c for c in cards if due(c)]
        a,b,c = st.columns(3)
        a.metric("Saved words", len(cards))
        b.metric("Due for review", len(pending))
        c.metric("Reviewed at least once", sum(int(x.get("review_count") or 0)>0 for x in cards))
        if not cards:
            st.info("Translate a Sanskrit sentence and select ‘Save these words as flashcards’ to start.")
            return
        show_all = st.checkbox("Practice all cards (including those not yet due)", key=prefix + "all")
        pool = cards if show_all else pending
        if not pool:
            st.success("You're all caught up! Come back when your next review is due.")
            return
        # Stable selection by card ID prevents jumps when a card is reviewed.
        selected = st.session_state.get(prefix + "selected_id")
        current = next((x for x in pool if x["id"] == selected), pool[0])
        st.session_state[prefix + "selected_id"] = current["id"]
        st.markdown("#### " + str(current["word"]))
        st.caption("Try to recall the meaning before revealing it.")
        revealed = st.session_state.get(prefix + "revealed_id") == current["id"]
        if not revealed:
            if st.button("Reveal meaning", key=prefix + "reveal", use_container_width=True):
                st.session_state[prefix + "revealed_id"] = current["id"]
                st.rerun()
        else:
            st.markdown("**Meaning:** " + str(current["meaning"]))
            if current.get("lemma"):
                st.write("**Lemma:**", current["lemma"])
            if current.get("grammar"):
                st.write("**Grammar:**", current["grammar"])
            st.caption("Again = review shortly · Hard = review tomorrow · Easy = longer interval")
            cols = st.columns(3)
            for col, rating in zip(cols, ("Again", "Hard", "Easy")):
                with col:
                    if st.button(rating, key=prefix + "rate_" + rating, use_container_width=True):
                        try:
                            grade_card(user, current, rating)
                            st.session_state.pop(prefix + "revealed_id", None)
                            st.session_state.pop(prefix + "selected_id", None)
                            st.rerun()
                        except (BetaError, ValueError, KeyError, TypeError) as exc:
                            st.error(f"Review could not be saved: {exc}")
        st.caption("Your cards and review schedule are saved privately in Supabase. Meanings are AI-generated; verify uncertain forms.")
