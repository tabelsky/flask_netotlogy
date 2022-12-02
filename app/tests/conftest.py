import datetime
import secrets
import time

import pytest
from auth import hash_password
from models import Base, Token, User, get_engine, get_session_maker
from tests.config import ROOT_USER_EMAIL, ROOT_USER_PASSWORD


def get_random_password():
    password = secrets.token_hex()
    return f"{password[:10]}{password[10:20].upper()}"


@pytest.fixture(scope="session", autouse=True)
def init_database():
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


def create_user(email: str = None, password: str = None):
    email = email or f"user{time.time()}@email.te"
    password = password or get_random_password()
    Session = get_session_maker()
    with Session() as session:
        new_user = User(email=email, password=hash_password(password))
        session.add(new_user)
        session.commit()
        return {
            "id": new_user.id,
            "email": new_user.email,
            "password": password,
            "registration_time": new_user.registration_time,
        }


@pytest.fixture(scope="session")
def root_user():
    return create_user(ROOT_USER_EMAIL, ROOT_USER_PASSWORD)


@pytest.fixture()
def new_user():
    return create_user()


@pytest.fixture()
def expired_token():
    Session = get_session_maker()

    with Session() as session:
        user = create_user()
        token = Token(user_id=user["id"], creation_time=datetime.datetime.utcnow() - datetime.timedelta(days=1000))
        session.add(token)
        session.commit()
        return str(token.id)
