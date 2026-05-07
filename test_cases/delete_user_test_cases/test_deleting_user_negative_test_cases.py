import json

import requests

from api_config import get_url
from models.api_models import UserErrorResponse


def test_delete_user_with_unknown_id_returns_404():
    missing_user_id = 999999999

    delete_response = requests.delete(get_url("user") + str(missing_user_id))

    assert delete_response.status_code == 404
    parsed_response = UserErrorResponse(**json.loads(delete_response.text))
    assert parsed_response.detail == "User not found"


def test_delete_user_with_invalid_id_type_returns_validation_error():
    delete_response = requests.delete(get_url("user") + "not-an-integer")

    assert delete_response.status_code == 422
    parsed_response = UserErrorResponse(**json.loads(delete_response.text))
    assert parsed_response.detail[0]["loc"] == ["path", "user_id"]
