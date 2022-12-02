import psycopg2
from errors import ApiError
from models import ORM_MODEL, ORM_MODEL_CLS
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def get_item(session: Session, model_cls: ORM_MODEL_CLS, item_id: int | str) -> ORM_MODEL:
    item = session.query(model_cls).get(item_id)
    if item is None:
        raise ApiError(404, f"{model_cls.__name__.lower()} not found")
    return item


def create_item(session: Session, model_cls: ORM_MODEL_CLS, commit: bool = True, **params) -> ORM_MODEL:
    new_item = model_cls(**params)
    session.add(new_item)
    if commit:
        try:
            session.commit()
        except IntegrityError as er:
            if isinstance(er.orig, psycopg2.errors.UniqueViolation):
                raise ApiError(409, f"such {model_cls.__name__.lower()} already exists")
    return new_item


def patch_item(session: Session, item: ORM_MODEL, commit: bool = True, **params) -> ORM_MODEL:
    for field, value in params.items():
        setattr(item, field, value)
    session.add(item)
    if commit:
        try:
            session.commit()
        except IntegrityError as er:
            if isinstance(er.orig, psycopg2.errors.UniqueViolation):
                raise ApiError(409, f"attr already exists")
    return item


def delete_item(session: Session, item: ORM_MODEL, commit: bool = True):
    session.delete(item)
    if commit:
        session.commit()
