"""Private, server-side translation history for signed-in beta users."""
import json
import uuid
from urllib.parse import quote
import streamlit as st
from private_beta import _request, BetaError


def save_translation(user, source, direction, languages, result):
    """Store one successful AI response; never expose the service key to the browser."""
    payload = {
        'id': str(uuid.uuid4()), 'user_id': user['id'], 'source_text': source,
        'direction': direction, 'languages': list(languages), 'result': result,
    }
    _request('POST', '/rest/v1/translation_history', service=True, payload=payload)
    return payload['id']


def list_translations(user, bookmarked_only=False):
    user_id = str(uuid.UUID(user['id']))
    path = ('/rest/v1/translation_history?select=id,source_text,direction,languages,'
            'result,bookmarked,created_at&user_id=eq.' + quote(user_id, safe='')
            + ('&bookmarked=eq.true' if bookmarked_only else '')
            + '&order=created_at.desc&limit=50')
    rows = _request('GET', path, service=True)
    return rows if isinstance(rows, list) else []


def update_bookmark(user, record_id, value):
    uid, rid = str(uuid.UUID(user['id'])), str(uuid.UUID(record_id))
    path = ('/rest/v1/translation_history?user_id=eq.' + uid + '&id=eq.' + rid)
    _request('PATCH', path, service=True, payload={'bookmarked': bool(value)})


def delete_translation(user, record_id):
    uid, rid = str(uuid.UUID(user['id'])), str(uuid.UUID(record_id))
    path = ('/rest/v1/translation_history?user_id=eq.' + uid + '&id=eq.' + rid)
    _request('DELETE', path, service=True)


def render_history(user):
    st.markdown('### 📚 Translation History & Bookmarks')
    st.caption('Your recent translations are saved privately in Supabase. Reopening a saved translation does not use AI tokens.')
    only_bookmarks = st.checkbox('⭐ Show bookmarks only', key='history_bookmarks_only')
    try:
        rows = list_translations(user, only_bookmarks)
    except BetaError:
        st.error('History could not load. Run history_setup.sql in Supabase and check the application logs.')
        return
    if not rows:
        st.info('No saved translations found yet. Translate a sentence to create your first entry.')
        return
    st.caption(f'Showing {len(rows)} most recent matching entries (maximum 50).')
    for row in rows:
        rid = row['id']
        preview = (row.get('source_text') or '').replace('\n', ' ')[:95]
        mark = '⭐' if row.get('bookmarked') else '☆'
        with st.expander(f"{mark} {preview} · {str(row.get('created_at', ''))[:10]}"):
            st.caption(row.get('direction', ''))
            st.write('**Natural translation:**', str((row.get('result') or {}).get('natural_translation', '')))
            actions = st.columns(3)
            if actions[0].button('📖 Open', key='hist_open_'+rid, use_container_width=True):
                st.session_state['history_pending_open'] = row
                st.rerun()
            if actions[1].button('Remove ⭐' if row.get('bookmarked') else '⭐ Bookmark', key='hist_mark_'+rid, use_container_width=True):
                try:
                    update_bookmark(user, rid, not row.get('bookmarked'))
                    st.rerun()
                except BetaError as exc:
                    st.error(str(exc))
            if actions[2].button('🗑️ Delete', key='hist_delete_'+rid, use_container_width=True):
                try:
                    delete_translation(user, rid)
                    st.rerun()
                except BetaError as exc:
                    st.error(str(exc))
