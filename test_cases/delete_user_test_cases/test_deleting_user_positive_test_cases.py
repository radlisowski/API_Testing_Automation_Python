import json

import requests

from api_config import get_url


def test_delete_user_with_valid_id(create_user, get_user_db_collection):
    user_id = create_user.user_id

    delete_response = requests.delete(get_url("user") + str(user_id))

    assert delete_response.status_code == 200
    parsed_response = json.loads(delete_response.text)
    assert parsed_response["message"] == f"User {user_id} deleted successfully"

    database_record = get_user_db_collection.find_one({"user_id": user_id})
    assert database_record is None
