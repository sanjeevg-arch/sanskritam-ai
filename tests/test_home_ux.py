import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_home_module_defines_expected_functions():
    tree = ast.parse((ROOT / 'home_ux.py').read_text(encoding='utf-8'))
    names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert {'render_home', 'next_beginner_lesson'} <= names


def test_main_app_has_all_four_routes():
    source = (ROOT / 'app.py').read_text(encoding='utf-8')
    for label in ['🏠 Home', '📚 Learn', '🌐 Translate', '🧠 Practice']:
        assert label in source
    assert 'render_admin_cost_dashboard(beta_user)' in source
