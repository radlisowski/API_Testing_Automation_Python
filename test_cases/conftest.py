import pytest
from api_config import active_environment, get_database_uri, ca_cert_file_path, db_name, \
    db_collection
from pymongo import MongoClient


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
    """ Connects to 'myCollection' inside 'myDatabase' on the database client.
    Use this in tests to directly interact with stored data, enabling checks
    on data creation, updates, and retrieval during testing. """
    client = get_doc_db_client()  # Establish connection to the database client
    db = client[db_name]      # Access the specific database
    collection = db[db_collection] # Access the specific collection
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
            database_collection = db[db_collection]
            database_collection.delete_many({})  # Remove all documents
            print("Database cleanup completed.")

