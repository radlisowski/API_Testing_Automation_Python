import random
import requests
import constants
from api_config import get_url
from models.api_models import User, Address, PhoneNumber


def test_post_user_endpoint_with_valid_payload():
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

    # Validate the response status code
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"

    # TODO
    # add validation of the response vs payload
    # add validation for payload vis database records
