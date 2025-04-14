import requests


def test_create_user():
    # Define the URL for the user creation endpoint
    url = "http://localhost:5556/user/"

    # Define the data payload for the POST request
    payload = {
        "username": "johndoe",
        "email": "o@example.com",
        "role": "tester",
        "addresses": [
            {
                "street": "123 Elm St",
                "city": "Metropolis",
                "country": "Utopia",
                "phone_numbers": [
                    {"type": "home", "number": "555-1234"},
                    {"type": "work", "number": "555-5678"},
                ],
            }
        ]
    }

    # Send a POST request with the JSON payload
    response = requests.post(url, json=payload)

    # Validate the response status code
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
