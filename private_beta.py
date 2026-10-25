"""Server-side Supabase email OTP and atomic translation quotas.

Never put the service role key in browser JavaScript or commit it to Git.
"""
import os
import re
import uuid
import requests
import streamlit as st


def setting(name):
    value = os.environ.get(name)
    if value:
        return value
    try:
        return st.secrets.get(name)
    except (FileNotFoundError, KeyError):
        return None


class BetaError(Exception):
    pass


def _request(method, path, *, service=False, token=None, payload=None):
    url = (setting('SUPABASE_URL') or '').rstrip('/')
    key = setting('SUPABASE_SERVICE_ROLE_KEY' if service else 'SUPABASE_ANON_KEY')
    if not url or not key:
        raise BetaError('Supabase configuration is missing. Contact the administrator.')
    headers = {'apikey': key, 'Content-Type': 'application/json'}
    headers['Authorization'] = 'Bearer ' + (token or key)
    try:
        response = requests.request(method, url + path, headers=headers, json=payload, timeout=15)
    except requests.RequestException as exc:
        raise BetaError('Could not connect to the authentication service.') from exc
    if not response.ok:
        if response.status_code in (401, 403):
            raise BetaError('Access denied or session expired. Please sign in again.')
        if response.status_code == 429:
            raise BetaError('Too many attempts. Please wait before trying again.')
        # Do not expose raw upstream errors or tokens in the UI.
        raise BetaError(f'Service request failed (HTTP {response.status_code}). Check server logs.')
    return response.json() if response.content else {}


def normalize_email(email):
    email = (email or '').strip().lower()
    if len(email) > 254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
        raise BetaError('Enter a valid email address.')
    return email


def invited(email):
    # This is a server-only query with a secret service-role key.
    from urllib.parse import quote
    rows = _request('GET', '/rest/v1/beta_invites?select=email,active&email=eq.' + quote(email, safe=''), service=True)
    return bool(rows and rows[0].get('active'))


def send_code(email):
    email = normalize_email(email)
    if not invited(email):
        # Don't reveal which emails are invited to anonymous visitors.
        return False
    _request('POST', '/auth/v1/otp', payload={'email': email, 'create_user': True})
    return True


def verify_code(email, code):
    email = normalize_email(email)
    code = (code or '').strip()
    if not re.fullmatch(r'\d{6,8}', code):
        raise BetaError('Enter the numeric code sent to your email.')
    data = _request('POST', '/auth/v1/verify', payload={'email': email, 'token': code, 'type': 'email'})
    access_token = data.get('access_token')
    if not access_token:
        raise BetaError('Could not verify this code. Check your email template settings.')
    user = current_user(access_token)
    if normalize_email(user.get('email')) != email or not invited(email):
        raise BetaError('This account is not approved for the private beta.')
    return access_token


def current_user(token):
    user = _request('GET', '/auth/v1/user', token=token)
    if not isinstance(user, dict) or not user.get('id') or not user.get('email'):
        raise BetaError('Sign-in session is invalid.')
    return user


def reserve(user, request_id):
    # RPC uses a PostgreSQL transaction and advisory lock; concurrent clicks
    # cannot overspend the daily per-user/global request allowance.
    result = _request('POST', '/rest/v1/rpc/reserve_beta_request', service=True, payload={
        'p_user_id': user['id'], 'p_email': normalize_email(user['email']), 'p_request_id': request_id
    })
    if not isinstance(result, dict) or not result.get('allowed'):
        raise BetaError((result or {}).get('reason', 'Daily usage limit reached.'))
    return result


def finish(request_id, success, tokens=0):
    _request('POST', '/rest/v1/rpc/finish_beta_request', service=True, payload={
        'p_request_id': request_id, 'p_success': bool(success), 'p_tokens': max(0, int(tokens))
    })


def auth_gate():
    st.markdown('## 🔒 Sanskritam AI · Private Beta')
    token = st.session_state.get('beta_access_token')
    if token:
        try:
            user = current_user(token)  # Verified against Supabase on every rerun.
            if not invited(normalize_email(user['email'])):
                raise BetaError('Your invitation is no longer active.')
            with st.sidebar:
                st.success('Private beta access')
                st.caption(user['email'])
                if st.button('Sign out'):
                    for key in ('beta_access_token', 'beta_email', 'result', 'last_source'):
                        st.session_state.pop(key, None)
                    st.rerun()
            return user
        except BetaError:
            st.session_state.pop('beta_access_token', None)
            st.warning('Please sign in again to continue.')
    st.info('Access is limited to invited testers. Sign in using your approved email address.')
    email = st.text_input('Invited email address', key='beta_email').strip().lower()
    if st.button('Email me a sign-in code', type='primary'):
        try:
            sent = send_code(email)
            st.session_state['beta_code_requested'] = sent
            st.success('If this email is invited, a sign-in code will arrive shortly.')
        except BetaError as exc:
            st.error(str(exc))
    code = st.text_input('One-time email code', max_chars=8, key='beta_code')
    if st.button('Verify code and enter'):
        try:
            st.session_state['beta_access_token'] = verify_code(email, code)
            st.session_state.pop('beta_code_requested', None)
            st.rerun()
        except BetaError as exc:
            st.error(str(exc))
    st.caption('Need access? Contact the Sanskritam AI administrator to request an invitation.')
    st.stop()  # Nothing below, including the OpenAI call, runs for visitors.


def new_request_id():
    return str(uuid.uuid4())
