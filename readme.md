# AUTO-TESTING-API

This repo contains a small FastAPI user service plus an early-stage API test-building agent.

The bigger goal is to build an agent that can be dropped into an API repository, discover endpoints, inspect existing tests, compare coverage against an API-agnostic testing stencil, report gaps, and eventually generate missing pytest API tests in the style of the repo.

## What Is Included

- FastAPI app with user `POST`, `GET`, and `DELETE` endpoints
- MongoDB-backed storage
- Docker and Docker Compose local environment
- Existing pytest API tests
- A local test-building agent under `test_building_agent/`
- Unit tests for the agent itself

## Project Structure

```text
.
├── app.py
├── docker-compose.yml
├── Dockerfile
├── models/
├── test_cases/
├── test_building_agent/
│   ├── README.md
│   ├── agent.py
│   ├── templates/
│   └── tests/
├── requirements.txt
└── pytest.ini
```

## Run Locally With Docker

Build and start the API plus MongoDB:

```bash
docker compose up -d --build
```

Open the FastAPI docs:

```text
http://localhost:5556/docs
```

Stop the services:

```bash
docker compose down
```

## API Examples

Create a user:

```bash
curl -X POST "http://localhost:5556/user/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "role": "tester",
    "email": "testuser@example.com",
    "addresses": [
      {
        "street": "Main Street",
        "city": "Dublin",
        "country": "Ireland",
        "phone_numbers": [
          {
            "type": "mobile",
            "number": "123456789"
          }
        ]
      }
    ]
  }'
```

Fetch a user:

```bash
curl "http://localhost:5556/user/1"
```

Delete a user:

```bash
curl -X DELETE "http://localhost:5556/user/1"
```

## Run API Tests

With the Docker services running:

```bash
docker compose exec -T api pytest test_cases -q
```

Run only the delete endpoint tests:

```bash
docker compose exec -T api pytest test_cases/delete_user_test_cases -q
```

## Test-Building Agent

The agent lives in:

```text
test_building_agent/
```

List discovered endpoints:

```bash
python3 test_building_agent/agent.py --list
```

Audit endpoint coverage:

```bash
python3 test_building_agent/agent.py --audit
```

Compare endpoints and existing tests against the generic API stencil:

```bash
python3 test_building_agent/agent.py --stencil-audit
```

Learn current repo testing patterns:

```bash
python3 test_building_agent/agent.py --learn-templates
```

Run the agent unit tests:

```bash
python3 -m unittest test_building_agent.tests.test_agent -v
```

These tests include temporary fixture repos, so the agent is checked against controlled API/test layouts as well as this project.

Run linting and formatting checks:

```bash
ruff check .
black --check .
```

Run agent unit tests with coverage:

```bash
pytest test_building_agent/tests --cov=test_building_agent --cov-report=term-missing
```

## Current Agent Capability

The agent currently:

- Discovers FastAPI endpoints from `app.py`
- Scans pytest files under `test_cases/`
- Matches `requests.get/post/delete/put/patch` calls to endpoints
- Compares existing tests against `test_building_agent/templates/api_test_stencil.json`
- Reports existing and missing test types
- Stores learned repo-specific patterns in `learned_patterns.json`

It does not generate tests yet. That is the next planned step.

## Current Generic Stencil

The stencil currently checks for:

- `success_happy_path`
- `not_found_unknown_resource`
- `invalid_path_parameter_type`
- `missing_payload`
- `missing_required_field`
- `invalid_payload_data_type`
- `malformed_json`

## Local Python Setup

If you want to run without Docker, create a virtual environment and install dependencies:

```bash
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Then run the app:

```bash
python3 app.py
```

MongoDB must be running locally on:

```text
mongodb://localhost:27017/
```
