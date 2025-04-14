"""Set the active environment"""
active_environment = 'DEV'  # Change this to 'SIT', 'UAT' or other environments as needed


# Define shared endpoints for all environments
endpoints = {
    'user': '/user/'
    # Add more endpoints as needed, which are common across environments
}

# Define configurations for different environments
environments = {
    'DEV': {
        'base_url': 'http://localhost:5556'
    },
    'SIT': {
        'base_url': 'http://sit.dummy_page.com'
    }
}

# Select the current environment configuration
current_config = environments[active_environment]

# Directly access the base_url from the current environment
base_url = current_config['base_url']


# Function to create full URL for a given endpoint
def get_url(endpoint):
    """Create the full URL by combining the base URL with the endpoint."""
    return base_url + endpoints[endpoint]
