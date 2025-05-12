import json
import random
import constants
import requests
from api_config import get_url
from models.api_models import User, UserErrorResponse


"""
    "This test validates the API's response behavior when a request is made to create a new user with an "
    "empty username field. It checks if the service correctly identifies the error and returns an "
    "appropriate HTTP status code and error message."
"""


def test_post_user_with_empty_username_error_handling(get_user_db_collection):
    user = User(
        # An empty username is provided to simulate an input error.
        username="",
        # Generates a valid random email to maintain other field integrity.
        email=f"test_{random.randint(1000000, 9999999)}@example.com",
        role="tester",
        addresses=[]
    )

    # Send a POST request to the user creation endpoint using the user data above
    post_response = requests.post(get_url('user'), json=user.dict())
    # Validate that the API correctly responds with a 400 Bad Request status code
    assert post_response.status_code == 400
    # Parse the response to extract error details using the UserErrorResponse response model located in conftest.py
    parsed_response = UserErrorResponse(**json.loads(post_response.text))
    # Check whether the error message matches the expected constant for an empty username
    assert (parsed_response.detail == constants.CREATE_USER_EMPTY_USERNAME)


"""
    "This test validates the API's response behavior when a request is made to create a new user with an "
    "empty email field. It checks if the service correctly identifies the error and returns an "
    "appropriate HTTP status code and error message."
"""


def test_post_user_with_empty_email_error_handling(get_user_db_collection):
    user = User(
        # Generates a valid random username (located in constants.py) to maintain other field integrity.
        username=f"User {random.randint(1000000, 9999999)}",
        # An empty email is provided to simulate an input error.
        email="",
        role="tester",
        addresses=[]
    )

    post_response = requests.post(get_url('user'), json=user.dict())
    assert post_response.status_code == 400
    parsed_response = UserErrorResponse(**json.loads(post_response.text))
    assert (parsed_response.detail == constants.CREATE_USER_EMPTY_EMAIL)
