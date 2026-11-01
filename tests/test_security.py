import sys
import types
import unittest
from unittest.mock import patch

# Lightweight Streamlit stub so tests run without Streamlit installed.
if 'streamlit' not in sys.modules:
    stub = types.ModuleType('streamlit')
    stub.session_state = {}
    stub.secrets = {}
    sys.modules['streamlit'] = stub

import private_beta


class SessionSecurityTests(unittest.TestCase):
    def setUp(self):
        private_beta.st.session_state.clear()

    def test_clears_all_user_and_widget_state(self):
        private_beta.st.session_state.update({'beta_access_token': 'secret', 'result': {'text': 'private'}, 'audio_transcript': 'private', 'widget': 1})
        private_beta.clear_account_session()
        self.assertEqual(dict(private_beta.st.session_state), {})

    def test_logout_uses_current_token(self):
        with patch.object(private_beta, '_request', return_value={}) as req:
            private_beta.sign_out('access-token')
            req.assert_called_once_with('POST', '/auth/v1/logout', token='access-token')

    def test_logout_failure_does_not_block_local_cleanup(self):
        with patch.object(private_beta, '_request', side_effect=private_beta.BetaError('offline')):
            private_beta.sign_out('expired-token')
        private_beta.st.session_state['result'] = 'private'
        private_beta.clear_account_session()
        self.assertFalse(private_beta.st.session_state)


if __name__ == '__main__':
    unittest.main()
