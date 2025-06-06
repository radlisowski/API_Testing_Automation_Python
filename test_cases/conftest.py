import json
import random
import pytest
import requests
import constants
from api_config import active_environment, get_database_uri, ca_cert_file_path, db_name, db_collection_name, get_url
from pymongo import MongoClient
from models.api_models import User, Address, PhoneNumber


def get_doc_db_client():
    connection_options = {}

    # Only use TLS options if not connecting to a local DB
    if active_environment != 'DEV':
        connection_options['tls'] = True
        connection_options['tlsCAFile'] = ca_cert_file_path
        connection_options['retryWrites'] = False

    # Initialize MongoClient with dynamic option handling
    client = MongoClient(
        get_database_uri(),
        **connection_options
    )
    return client


@pytest.fixture(scope="session", autouse=False)
def get_user_db_collection():
    """ Connects to collection on the database client.
    Use this in tests to directly interact with stored data, enabling checks
    on data creation, updates, and retrieval during testing. """
    client = get_doc_db_client()  # Establish connection to the database client
    db = client[db_name]      # Access the specific database
    collection = db[db_collection_name] # Access the specific collection
    return collection               # Make the collection available to tests


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # Check if the test is marked with the specific marker
    # Execute test and get outcome
    # Wait with the finishing the test till below is executed
    outcome = yield
    report = outcome.get_result()

    # Check if the test marked with 'clean_database' has completed
    if 'clean_database' in item.keywords and report.when == "call":
        if report.outcome == 'passed' or report.outcome == 'failed':
            print(f"Cleaning database after test: {item.name}")
            client = get_doc_db_client()
            db = client[db_name]  # Access the specific database
            database_collection = db[db_collection_name]
            database_collection.delete_many({})  # Remove all documents

            print("Database cleanup completed.")


@pytest.fixture(scope="session")
def create_user(get_user_db_collection):
    """
    This fixture creates a new user object to prepare data for tests that require a pre-existing user.
    It generates a user with randomized details like username and phone numbers, ensuring broad test coverage.
    The user data is sent to the server and validated, providing useful test conditions for user creation and storage.
    Refer to the README file for more information on how fixtures work in this context.
    """
    payload = User(
        username=f"User {random.randint(1000000, 9999999)}",
        email=f"coffee_number_{random.randint(1000000, 9999999)}@conftest.com",
        role="tester",
        addresses=[
            Address(
                street=f"{random.randint(100, 999)} Elm Street",
                city=constants.CITY,
                country=constants.COUNTRY,
                phone_numbers=[
                    PhoneNumber(type="home", number=str(random.randint(10000000, 99999999)), ),
                    PhoneNumber(type="work", number=str(random.randint(10000000, 99999999)), ),
                ]
            )
        ]
    )

    post_response = requests.post(get_url('user'), json=payload.dict())
    assert post_response.status_code == 201
    parsed_response = User(**json.loads(post_response.text))
    # the below returns the created user to the test
    return parsed_response
