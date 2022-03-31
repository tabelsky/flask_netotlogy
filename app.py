import atexit
import os
import re
import uuid
from typing import Union

import pydantic
from flask import Flask, jsonify, request
from flask.views import MethodView
from flask_bcrypt import Bcrypt
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

app = Flask("app")
bcrypt = Bcrypt(app)
engine = create_engine(os.getenv("PG_DSN"))
Base = declarative_base()
Session = sessionmaker(bind=engine)


atexit.register(lambda: engine.dispose())

password_regex = re.compile(
    "^(?=.*[a-z_])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&_])[A-Za-z\d@$!#%*?&_]{8,200}$"
)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    user_name = Column(String(100), nullable=False, unique=True)
    password = Column(String(200), nullable=False)
    registration_time = Column(DateTime, server_default=func.now())

    @classmethod
    def register(cls, session: Session, user_name: str, password: str):
        new_user = User(
            user_name=user_name,
            password=bcrypt.generate_password_hash(password.encode()).decode(),
        )
        session.add(new_user)
        try:
            session.commit()
            return new_user
        except IntegrityError:
            session.rollback()

    def check_password(self, password: str):
        return bcrypt.check_password_hash(self.password.encode(), password.encode())

    def to_dict(self):
        return {
            "user_name": self.user_name,
            "registration_time": int(self.registration_time.timestamp()),
            "id": self.id,
        }


class Token(Base):
    __tablename__ = "tokens"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    creation_time = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship(User, lazy="joined")


Base.metadata.create_all(engine)


class HTTPError(Exception):
    def __init__(self, status_code: int, message: Union[str, list, dict]):
        self.status_code = status_code
        self.message = message


@app.errorhandler(HTTPError)
def handle_invalid_usage(error):
    response = jsonify({"message": error.message})
    response.status_code = error.status_code
    return response


def check_token(session):
    token = (
        session.query(Token)
        .join(User)
        .filter(
            User.user_name == request.headers.get("user_name"),
            Token.id == request.headers.get("token"),
        )
        .first()
    )
    if token is None:
        raise HTTPError(401, "invalid token")
    return token


class CreateUserModel(pydantic.BaseModel):
    user_name: str
    password: str

    @pydantic.validator("password")
    def strong_password(cls, value: str):
        if not re.search(password_regex, value):
            raise ValueError("password to easy")

        return value


def validate(unvalidated_data: dict, validation_model):
    try:
        return validation_model(**unvalidated_data).dict()
    except pydantic.ValidationError as er:
        raise HTTPError(400, er.errors())


class UserView(MethodView):
    def get(self, user_id: int):
        with Session() as session:
            token = check_token(session)
            if token.user.id != user_id:
                raise HTTPError(403, "auth error")
            return jsonify(token.user.to_dict())

    def post(self):
        with Session() as session:
            register_data = validate(request.json, CreateUserModel)
            return User.register(session, **register_data).to_dict()


@app.route("/login/", methods=["POST"])
def login():
    login_data = request.json
    with Session() as session:
        user = (
            session.query(User)
            .filter(User.user_name == login_data["user_name"])
            .first()
        )
        if user is None or not user.check_password(login_data["password"]):
            raise HTTPError(401, "incorrect user or password")
        token = Token(user_id=user.id)
        session.add(token)
        session.commit()
        return jsonify({"token": token.id})


app.add_url_rule(
    "/user/<int:user_id>/", view_func=UserView.as_view("get_user"), methods=["GET"]
)
app.add_url_rule(
    "/user/", view_func=UserView.as_view("register_user"), methods=["POST"]
)
