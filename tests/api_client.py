from typing import Union

from requests import Response, Session

from tests.config import API_URL


class ApiException(Exception):
    def __init__(self, message: str, status: int):
        self.message = message
        self.status = status

    def __str__(self):
        return f"api request failed with code {self.status}.\n\n response from server:\n {self.message}"


class TestApi:

    """Клиент для тестирвоания эндпоинтов"""

    _instance = None

    @classmethod
    def get_instance(cls, api_url: str):
        if cls._instance is None:
            cls._instance = cls(api_url)
        return cls._instance

    def __init__(self, api_url: str):
        self.api_url = api_url
        self.session = Session()

    def _call(
        self,
        http_method: str,
        api_method: str,
        response_attribute: str = None,
        *args,
        **kwargs,
    ) -> Union[Response, dict, str]:
        response = self.session.request(
            http_method, f"{self.api_url}/{api_method}/", *args, **kwargs
        )
        if response.status_code >= 400:
            raise ApiException(response.text, response.status_code)

        response = (
            getattr(response, response_attribute)
            if response_attribute is not None
            else response
        )
        response = response() if callable(response) else response
        #  если передали response_attribute получаем его и вызываем, в случае если это метод, например json()

        return response

    def register(self, user_name: str, password: str):
        return self._call(
            "POST", "user", "json", json={"user_name": user_name, "password": password}
        )

    def login(self, user_name: str, password: str):
        token = self._call(
            "POST", "login", "json", json={"user_name": user_name, "password": password}
        )
        self.session.headers.update({"token": token["token"], "user_name": user_name})
        return token

    def get_user(self, user_id):
        return self._call("GET", f"user/{user_id}", "json")


def get_client(api_url: str = API_URL) -> TestApi:
    return TestApi.get_instance(api_url)
