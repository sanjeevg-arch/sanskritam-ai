"""Authenticated correction reports and admin moderation; no AI calls."""
import hashlib
import json
import uuid
from urllib.parse import quote
import streamlit as st
from private_beta import _request, setting, BetaError

ISSUE_TYPES = ('Natural translation', 'Word meaning', 'Root meaning', 'Grammar', 'Sandhi', 'Other')

def is_admin(user):
    allowed = {e.strip().casefold() for e in (setting('CORRECTIONS_ADMIN_EMAILS') or '').split(',') if e.strip()}
    return bool(allowed and (user.get('email') or '').strip().casefold() in allowed)

def passage_hash(source, direction):
    return hashlib.sha256((direction.strip()+'\n'+source.strip()).encode('utf-8')).hexdigest()

def submit_report(user, source, direction, result, category, selected_word, proposed, explanation):
    if not source.strip() or len(source)>4000 or category not in ISSUE_TYPES:
        raise ValueError('Invalid report input.')
    if not proposed.strip() or len(proposed)>2000 or len(explanation)>2000 or len(selected_word)>200:
        raise ValueError('Enter a suggested correction (up to 2,000 characters).')
    payload = {'id':str(uuid.uuid4()),'user_id':str(uuid.UUID(user['id'])),
      'source_text':source[:4000], 'direction':direction[:100],
      'passage_hash':passage_hash(source,direction), 'issue_type':category,
      'selected_word':selected_word[:200], 'suggested_correction':proposed.strip(),
      'explanation':explanation.strip(),
      'original_excerpt':json.dumps(result,ensure_ascii=False)[:8000]}
    _request('POST','/rest/v1/correction_reports',service=True,payload=payload)

def my_reports(user):
    uid=str(uuid.UUID(user['id']))
    path='/rest/v1/correction_reports?select=id,issue_type,selected_word,suggested_correction,status,review_note,created_at&user_id=eq.'+uid+'&order=created_at.desc&limit=30'
    return _request('GET',path,service=True)

def admin_reports(user):
    if not is_admin(user): raise PermissionError('Administrator access required.')
    return _request('GET','/rest/v1/correction_reports?select=id,source_text,direction,issue_type,selected_word,suggested_correction,explanation,status,review_note,created_at&order=created_at.desc&limit=100',service=True)

def review_report(user, report_id, status, note):
    if not is_admin(user): raise PermissionError('Administrator access required.')
    if status not in ('approved','rejected','needs_information') or len(note)>2000:
        raise ValueError('Invalid review.')
    uid=str(uuid.UUID(user['id'])); rid=str(uuid.UUID(report_id))
    _request('PATCH','/rest/v1/correction_reports?id=eq.'+rid+'&status=eq.pending',service=True,
       payload={'status':status,'review_note':note.strip(),'reviewed_by':uid,'reviewed_at':'now()'} if False else
       {'status':status,'review_note':note.strip(),'reviewed_by':uid})

def render_corrections(user, source=None, direction=None, result=None):
    with st.expander('📝 Translation Accuracy & Corrections', expanded=False):
        st.caption('Suggest a correction for review. Suggestions do not automatically change AI translations. No additional AI tokens are used.')
        if source and isinstance(result,dict):
            with st.form('correction_submit_form',clear_on_submit=True):
                category=st.selectbox('What needs correction?',ISSUE_TYPES)
                word_options=['(Whole passage)']+[str(w.get('word')) for w in result.get('words',[]) if isinstance(w,dict) and w.get('word')]
                word=st.selectbox('Affected word (optional)',word_options)
                proposed=st.text_area('Suggested correct wording *',max_chars=2000)
                explanation=st.text_area('Why is this correction needed? (optional)',max_chars=2000)
                sent=st.form_submit_button('Submit correction for review')
                if sent:
                    try:
                        submit_report(user,source,direction or '',result,category,'' if word==word_options[0] else word,proposed,explanation)
                        st.success('Correction submitted for review. Thank you!')
                    except (BetaError,ValueError) as exc: st.error(str(exc))
        else: st.info('Translate or open a saved passage to propose a correction.')
        if st.button('Refresh my reports',key='corrections_refresh'):
            st.rerun()
        try:
            rows=my_reports(user)
            if rows:
                st.markdown('**My recent reports**')
                for r in rows[:10]:
                    st.write(f"{r.get('created_at','')[:10]} · {r.get('issue_type','')} · **{r.get('status','pending')}**")
                    if r.get('review_note'): st.caption('Reviewer: '+r['review_note'])
        except BetaError: st.warning('Could not load correction reports. Run corrections_setup.sql first.')

    if is_admin(user):
        with st.expander('🛡️ Correction Review · Admin',expanded=False):
            st.caption('Only emails in CORRECTIONS_ADMIN_EMAILS can review. Approval marks a report as reviewed; it does not automatically alter translation output.')
            try: rows=admin_reports(user)
            except BetaError:
                st.error('Could not load reports. Check corrections_setup.sql and Supabase configuration.')
                return
            pending=[r for r in rows if r.get('status')=='pending']
            st.metric('Pending reports',len(pending))
            for r in pending:
                with st.container(border=True):
                    st.write('**Passage:**',r.get('source_text',''))
                    st.write('**Issue:**',r.get('issue_type',''),'·',r.get('selected_word') or 'Whole passage')
                    st.write('**Suggested:**',r.get('suggested_correction',''))
                    if r.get('explanation'): st.write('**Reason:**',r['explanation'])
                    with st.form('review_'+r['id']):
                        decision=st.selectbox('Decision',('approved','rejected','needs_information'),key='decision_'+r['id'])
                        note=st.text_area('Reviewer note',max_chars=2000,key='note_'+r['id'])
                        if st.form_submit_button('Save review'):
                            try:
                                review_report(user,r['id'],decision,note)
                                st.success('Review recorded.')
                                st.rerun()
                            except (BetaError,ValueError,PermissionError) as exc: st.error(str(exc))
