import json
import pytest as pytest
import requests
from api_config import get_url
from models.api_models import User
"""
    "This test verifies getting of user by id and validating all fields in a response body"
"""


@pytest.mark.clean_database
def test_get_user_with_valid_id(create_user):
    """Parameter create_user: This parameter is injected by a pytest fixture, create_user, which
    sets up and creates a user in the database before the test runs.
    The fixture returns an object representing the created user, including a user_id."""
    user_id=str(create_user.user_id)
    """Extracts the User ID: Converts the user_id attribute of the create_user object to a string, 
    ensuring it's in the correct format for including in the URL below."""
    get_request = requests.get(get_url('user') + user_id)
    assert get_request.status_code == 200
    parsed_get_response = User(**json.loads(get_request.text))

    """asserting email and username received from get response with respect to post response"""
    assert parsed_get_response.email == create_user.email
    assert parsed_get_response.username == create_user.username

    """asserting Nested list of addresses received from get response with respect to post response"""
    for actual_address in parsed_get_response.addresses:
        for expected_address in create_user.addresses:
            assert expected_address.city == actual_address.city
            assert expected_address.street == actual_address.street
            assert expected_address.country == actual_address.country

