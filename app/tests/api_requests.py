import json
from typing import Literal
from urllib.parse import urljoin

import requests
from errors import ApiError
from tests.config import API_URL

session = requests.Session()


def base_request(http_method: Literal["get", "post", "delete", "patch"], path: "str", *args, **kwargs) -> dict:
    method = getattr(session, http_method)
    response = method(urljoin(API_URL, path), *args, **kwargs)
    if response.status_code >= 400:
        try:
            message = response.json()
        except json.JSONDecodeError:
            message = response.text
        raise ApiError(response.status_code, message)
    return response.json()


def register(email: str, password: str) -> int:
    return base_request("post", "register", json={"email": email, "password": password})["id"]


def login(email: str, password: str) -> str:
    return base_request("post", "login", json={"email": email, "password": password})["token"]


def get_user(user_id: int) -> dict:
    return base_request("get", f"users/{user_id}")


def patch_user(user_id: int, email: str, password: str = None, token: str = None) -> dict:
    params = {key: value for key, value in (("email", email), ("password", password)) if value is not None}
    return base_request("patch", f"users/{user_id}", json=params, headers={"token": token})


def delete_user(user_id: int, token: str) -> bool:
    return base_request("delete", f"users/{user_id}", headers={"token": token})["deleted"]
