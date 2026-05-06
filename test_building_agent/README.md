# Test Building Agent

This folder contains a local helper agent for auditing API test coverage.

The goal is to build toward an API-agnostic test generation tool. For now, the agent does not create tests automatically. It discovers endpoints, scans existing tests, compares them against a generic API testing stencil, and reports what test coverage is missing.

## Current Flow

1. Discover FastAPI endpoints from `app.py`.
2. Scan existing pytest files under `test_cases/`.
3. Detect `requests.get`, `requests.post`, `requests.delete`, `requests.put`, and `requests.patch` calls.
4. Match those requests back to discovered endpoints.
5. Compare each endpoint against a generic API test stencil.
6. Report missing test types.

## Files

`agent.py`

The main command-line agent.

`templates/api_test_stencil.json`

The endpoint-agnostic checklist of test types each API endpoint should be considered against.

`templates/learned_patterns.json`

A generated file that summarizes patterns found in the current repo's tests. This is useful context for later template generation, but the main source of truth for required coverage is the stencil.

## Commands

List discovered endpoints:

```bash
python3 test_building_agent/agent.py --list
```

Example output:

```text
POST         /user/               create_user
DELETE       /user/{user_id}      delete_user
GET          /user/{user_id}      get_user
```

Audit simple endpoint coverage:

```bash
python3 test_building_agent/agent.py --audit
```

This checks whether each endpoint has any matching tests, plus whether those tests look positive or negative.

Audit against the generic API stencil:

```bash
python3 test_building_agent/agent.py --stencil-audit
```

This is the most important command right now. It reports which stencil test cases are missing for each endpoint.

Learn patterns from existing tests:

```bash
python3 test_building_agent/agent.py --learn-templates
```

This rewrites `templates/learned_patterns.json` based on the current tests.

Run the agent unit tests:

```bash
python3 -m unittest test_building_agent.tests.test_agent -v
```

These tests use Python's standard library only. They do not need FastAPI, MongoDB, Docker, or pytest.
They include fixture-repo checks that create temporary mini API projects and verify the stencil audit can both find gaps and recognize complete coverage.

## Current Stencil

The generic stencil currently includes:

- `success_happy_path`
- `not_found_unknown_resource`
- `invalid_path_parameter_type`
- `missing_payload`
- `missing_required_field`
- `invalid_payload_data_type`
- `malformed_json`

The stencil is intentionally endpoint-agnostic. For example, `missing_payload` applies to `POST`, `PUT`, and `PATCH` endpoints that accept request bodies, while `not_found_unknown_resource` applies to path-based `GET`, `PUT`, `PATCH`, and `DELETE` endpoints.

## Current Gaps Found

At the time this README was created, the stencil audit reports:

```text
POST /user/ -> create_user
  - [negative] missing_payload
  - [negative] invalid_payload_data_type
  - [negative] malformed_json

DELETE /user/{user_id} -> delete_user
  - [negative] invalid_path_parameter_type

GET /user/{user_id} -> get_user
  - [negative] not_found_unknown_resource
  - [negative] invalid_path_parameter_type
```

## Intended Next Steps

1. Tune `api_test_stencil.json` until it represents the testing standard we want.
2. Add any missing tests manually or have the agent generate draft tests.
3. Teach the agent to use the stencil plus existing project style to create new pytest files.
4. When a new endpoint appears, have the agent detect the endpoint and propose or generate the missing tests automatically.
