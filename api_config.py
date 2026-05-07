import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ApiSettings:
    active_environment: str
    base_url: str
    mongo_uri: str
    db_name: str
    db_collection_name: str
    counters_collection_name: str
    ca_cert_file_path: str


def load_settings() -> ApiSettings:
    active_env = os.getenv("ACTIVE_ENVIRONMENT", "DEV")

    return ApiSettings(
        active_environment=active_env,
        base_url=os.getenv("BASE_URL", "http://localhost:5556"),
        mongo_uri=os.getenv("MONGO_URI", "mongodb://localhost:27017/"),
        db_name=os.getenv("MONGO_DB_NAME", "UserDatabase"),
        db_collection_name=os.getenv("MONGO_COLLECTION_NAME", "UserCollection"),
        counters_collection_name=os.getenv("MONGO_COUNTERS_COLLECTION_NAME", "Counters"),
        ca_cert_file_path=os.getenv("CA_CERT_FILE_PATH", ".pem"),
    )


settings = load_settings()

endpoints = {
    "user": "/user/",
}

# Backward-compatible names used by the existing pytest fixtures.
active_environment = settings.active_environment
base_url = settings.base_url
db_name = settings.db_name
db_collection_name = settings.db_collection_name
ca_cert_file_path = settings.ca_cert_file_path


def get_url(endpoint: str) -> str:
    """Create the full URL by combining the base URL with the endpoint path."""
    return settings.base_url + endpoints[endpoint]


def get_database_uri() -> str:
    return settings.mongo_uri
