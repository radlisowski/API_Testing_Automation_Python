"""Set the active environment"""
active_environment = 'DEV'
# Change this to 'SIT', 'UAT' or other environments as needed

# Define shared endpoints for all environments
endpoints = {
    'user': '/user/'
    # Add more endpoints as needed, which are common across environments
}

# Define configurations for different environments
environments = {
    'DEV': {
        'base_url': 'http://localhost:5556',
        'db_name': 'UserDatabase',
        'db_collection': 'UserCollection'
    },
    'SIT': {
        'base_url': 'http://sit.dummy_page.com',
        'db_name': '',
        'db_collection': ''
    }
}

ca_cert_file_path = 'rds-ca-2019-root.pem'

# Select the current environment configuration
current_config = environments[active_environment]

# Directly access the base_url from the current environment
base_url = current_config['base_url']

db_name = current_config['db_name']
db_collection = current_config['db_collection']


# Function to create full URL for a given endpoint
def get_url(endpoint):
    """Create the full URL by combining the base URL with the endpoint."""
    return base_url + endpoints[endpoint]


@staticmethod
def get_database_uri():
    if active_environment == "DEV":
        return "mongodb://localhost:27017/",
    if active_environment == "SIT":
        return "mongodb://%s:%s@%s:%s/%s"
