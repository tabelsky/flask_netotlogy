import uuid

import pytest
from tests.api_requests import ApiError, delete_user, get_user, login, patch_user, register
from tests.config import DEFAULT_PASSWORD


def test_register():
    user_id = register("user_1@email.te", DEFAULT_PASSWORD)

    assert isinstance(user_id, int)


def test_register_simple_password():
    with pytest.raises(ApiError) as error:
        register("user_1@email.te", "1234")

    assert error.value.status_code == 400
    assert error.value.message == {
        "status": "error",
        "description": [{"loc": ["password"], "msg": "password is to easy", "type": "value_error"}],
    }


def test_invalid_email():
    with pytest.raises(ApiError) as error:
        register("invalid_email", DEFAULT_PASSWORD)

    assert error.value.status_code == 400
    assert error.value.message == {
        "status": "error",
        "description": [{"loc": ["email"], "msg": "value is not a valid email address", "type": "value_error.email"}],
    }


def test_register_existed(new_user):
    with pytest.raises(ApiError) as error:
        register(new_user["email"], DEFAULT_PASSWORD)
    assert error.value.status_code == 409
    assert error.value.message == {"status": "error", "description": f"such user already exists"}


def test_login(new_user):
    token = login(new_user["email"], new_user["password"])
    assert isinstance(token, str)


def test_login_incorrect(new_user):
    with pytest.raises(ApiError) as error:
        login(new_user["email"], new_user["password"] + "a")
    assert error.value.status_code == 401


def test_get_user(new_user):
    user = get_user(new_user["id"])
    assert user == {
        "id": new_user["id"],
        "email": new_user["email"],
        "registration_time": new_user["registration_time"].isoformat(),
    }


def test_get_unexisting_user():
    with pytest.raises(ApiError) as er:
        get_user(9999999)
    assert er.value.status_code == 404
    assert er.value.message == {"status": "error", "description": "user not found"}


def test_delete_user(new_user):
    new_user_token = login(new_user["email"], new_user["password"])
    result = delete_user(new_user["id"], new_user_token)
    assert result is True


def test_delete_foreign_user(root_user, new_user):

    root_user_token = login(root_user["email"], root_user["password"])
    with pytest.raises(ApiError) as er:
        delete_user(new_user["id"], root_user_token)
    assert er.value.status_code == 403
    assert er.value.message == {"status": "error", "description": "user has no access"}


@pytest.mark.parametrize("token", ["bad_token", str(uuid.uuid4()), None])
def test_delete_user_bad_token(token, new_user):
    with pytest.raises(ApiError) as er:
        delete_user(new_user["id"], token)
    assert er.value.status_code == 403
    assert er.value.message == {"status": "error", "description": "incorrect token"}


def test_patch_user(new_user):
    new_user_token = login(new_user["email"], new_user["password"])
    pathed = patch_user(new_user["id"], email="new@email.nw", token=new_user_token)
    assert pathed == {
        "id": new_user["id"],
        "email": "new@email.nw",
        "registration_time": new_user["registration_time"].isoformat(),
    }
    user = get_user(new_user["id"])

    assert user == {
        "id": new_user["id"],
        "email": "new@email.nw",
        "registration_time": new_user["registration_time"].isoformat(),
    }


def test_patch_foreign_user(root_user, new_user):

    root_user_token = login(root_user["email"], root_user["password"])
    with pytest.raises(ApiError) as er:
        patch_user(new_user["id"], email="new@email.nw", token=root_user_token)
    assert er.value.status_code == 403
    assert er.value.message == {"status": "error", "description": "user has no access"}
