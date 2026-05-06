import json
import requests
from api_config import get_url
from models.api_models import UserErrorResponse


def test_delete_user_with_unknown_id_returns_404():
    missing_user_id = 999999999

    delete_response = requests.delete(get_url('user') + str(missing_user_id))

    assert delete_response.status_code == 404
    parsed_response = UserErrorResponse(**json.loads(delete_response.text))
    assert parsed_response.detail == "User not found"
