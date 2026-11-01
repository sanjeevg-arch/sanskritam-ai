import sys
import types
import unittest
from unittest.mock import patch

if 'streamlit' not in sys.modules:
    stub = types.ModuleType('streamlit')
    stub.session_state = {}
    stub.secrets = {}
    sys.modules['streamlit'] = stub

from private_beta import BetaError
from admin_cost_dashboard import fetch_usage

class AdminGuardTests(unittest.TestCase):
    def test_anonymous_rejected(self):
        with self.assertRaises(BetaError):
            fetch_usage(30)

    def test_non_admin_rejected_without_db_call(self):
        with patch('admin_cost_dashboard._request') as req, patch('admin_cost_dashboard.is_admin', return_value=False):
            with self.assertRaises(BetaError):
                fetch_usage(30, user={'email': 'student@example.com'})
            req.assert_not_called()

    def test_invalid_window_rejected(self):
        with patch('admin_cost_dashboard.is_admin', return_value=True):
            with self.assertRaises(BetaError):
                fetch_usage(999, user={'email': 'admin@example.com'})
