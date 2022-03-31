import pytest

import app
from tests.api_client import get_client

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "StrongPassword_!#123"


@pytest.fixture(scope="session", autouse=True)
def clean_up_database():
    print("v" * 100)
    app.Base.metadata.drop_all(app.engine)
    app.Base.metadata.create_all(app.engine)
    yield
    app.Base.metadata.drop_all(app.engine)
    app.Base.metadata.create_all(app.engine)


@pytest.fixture(scope="session", autouse=True)
def api_client():
    return get_client()


@pytest.fixture(scope="session", autouse=True)
def admin_user(clean_up_database, api_client):
    user = api_client.register(ADMIN_USERNAME, ADMIN_PASSWORD)
    return {"user_name": ADMIN_USERNAME, "password": ADMIN_PASSWORD, "id": user["id"]}


@pytest.fixture()
def admin_login(api_client, admin_user):
    api_client.login(admin_user["user_name"], admin_user["password"])
    return api_client
