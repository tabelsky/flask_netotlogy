import pytest

from tests.api_client import ApiException


class TestEndpoints:
    def test_incorrect_uri(self, api_client):
        with pytest.raises(ApiException) as er:
            api_client._call("GET", "nonexistent")
            assert er.value.status == 404

    def test_login_incorrect(self, api_client):
        with pytest.raises(ApiException) as er:
            api_client.login("abracadabra", "123_araa443dffFFd")
            assert er.value.status == 401

    def test_login_correct(self, api_client, admin_user):
        token = api_client.login(
            user_name=admin_user["user_name"], password=admin_user["password"]
        )
        assert "token" in token
        assert isinstance(token["token"], str)
        print(token)

    def test_get_user(self, admin_login, admin_user):
        user = admin_login.get_user(admin_user["id"])
        assert user["user_name"] == admin_user["user_name"]
