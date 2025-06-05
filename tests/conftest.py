import pytest
from app import app as flask_app
# from flask_wtf.csrf import validate_csrf # モックのためにインポート - 削除

@pytest.fixture
def app():
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['TESTING'] = True
    yield flask_app

# @pytest.fixture(autouse=True) # 削除
# def mock_csrf_validation(monkeypatch): # 削除
#     """テスト中にvalidate_csrf関数を何もしないようにモックします。""" # 削除
#     def mock_validate_csrf(token): # 削除
#         pass # 何もしないことで、検証を実質的にバイパスします。 # 削除
#     
#     monkeypatch.setattr('flask_wtf.csrf.validate_csrf', mock_validate_csrf) # 削除 