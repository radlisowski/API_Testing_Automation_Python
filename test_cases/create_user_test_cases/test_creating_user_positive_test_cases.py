import json
import random
import pytest
import requests
import constants
from api_assersions import assert_user_attributes, assert_user_addresses
from api_config import get_url
from models.api_models import User, Address, PhoneNumber


# @pytest.mark.clean_database
def test_post_user_endpoint_with_valid_payload(get_user_db_collection):
    payload = User(
        username=f"User {random.randint(1000000, 9999999)}",
        email=f"test_{random.randint(1000000, 9999999)}@dummy_page.com",
        role="tester",
        addresses=[
            Address(
                street=f"{random.randint(10, 99)} Main Street",
                city=constants.CITY,
                country=constants.COUNTRY,
                phone_numbers=[
                    PhoneNumber(type="home", number=str(random.randint(10000000, 99999999)), ),
                    PhoneNumber(type="work", number=str(random.randint(10000000, 99999999)), ),
                ]
            )
        ]
    )

    # Send a POST request with the JSON payload
    response = requests.post(get_url('user'), json=payload.dict())

    '''RESPONSE VALIDATION'''

    # We are verifying the HTTP response code from the server, specifically looking for a 201 status code.
    assert response.status_code == 201

    """Converting the server's JSON response into a Python object.
    This transformation makes it easier to access and verify each attribute of the newly created user.
    By handling the response as a Python object, you can use its fields directly
    to ensure all the user data matches the expected values."""

    parsed_response = User(**json.loads(response.text))
    assert_user_attributes(payload, parsed_response)
    assert_user_addresses(payload, parsed_response)

    '''DATABASE VALIDATION'''

    # Retrieve the collection from the MongoDB database
    database_collection = get_user_db_collection
    # Retrieve the user data from the MongoDB collection matching the username
    database_record = database_collection.find_one({'username': payload.username})

    # Convert the database record into a Pydantic User object for comparison (as above with the response)
    db_user = User(**database_record)

    """ Use helper functions to verify that the user attributes, 
    such as username and email and role, match between the original user object from the payload 
    and the database entry."""
    assert_user_attributes(payload, db_user)

    """ Ensure that the user's addresses and associated phone numbers 
    are identical between the original user object and the database entry."""
    assert_user_addresses(payload, db_user)


def test_post_user_with_mandatory_only_payload(get_user_db_collection):
    payload = User(
        username=f"User {random.randint(1000000, 9999999)}",
        email=f"test_{random.randint(1000000, 9999999)}@dummy_page.com",
        role="tester",
        addresses=[]
    )

    post_response = requests.post(get_url('user'), json=payload.dict())

    '''RESPONSE VALIDATION'''

    assert post_response.status_code == 201
    parsed_response = User(**json.loads(post_response.text))
    assert_user_attributes(payload, parsed_response)
    assert_user_addresses(payload, parsed_response)

    '''DATABASE VALIDATION'''

    database_record = get_user_db_collection.find_one({'username': payload.username})
    db_user = User(**database_record)
    assert_user_attributes(payload, db_user)
    assert_user_addresses(payload, db_user)
