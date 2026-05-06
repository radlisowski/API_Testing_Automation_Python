import ast
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from test_building_agent import agent


class AgentEndpointDiscoveryTests(unittest.TestCase):
    def test_load_fastapi_endpoints_finds_current_user_routes(self):
        endpoints = agent.load_fastapi_endpoints()
        endpoint_keys = {(endpoint.method, endpoint.path) for endpoint in endpoints}

        self.assertIn(("POST", "/user/"), endpoint_keys)
        self.assertIn(("GET", "/user/{user_id}"), endpoint_keys)
        self.assertIn(("DELETE", "/user/{user_id}"), endpoint_keys)

    def test_load_endpoint_aliases_reads_api_config(self):
        aliases = agent.load_endpoint_aliases()

        self.assertEqual(aliases["user"], "/user/")


class AgentRequestParsingTests(unittest.TestCase):
    def test_resolve_request_path_handles_get_url_plus_path_param(self):
        call = _first_call("requests.get(get_url('user') + str(user_id))")

        path = agent.resolve_request_path(call, {"user": "/user/"})

        self.assertEqual(path, "/user/{user_id}")

    def test_paths_match_treats_dynamic_segments_as_compatible(self):
        self.assertTrue(agent.paths_match("/user/{user_id}", "/user/{missing_user_id}"))
        self.assertTrue(agent.paths_match("/user/{user_id}", "/user/{value}"))
        self.assertFalse(agent.paths_match("/user/{user_id}", "/orders/{order_id}"))

    def test_classify_test_uses_file_and_test_name_hints(self):
        self.assertEqual(
            agent.classify_test(
                Path("test_cases/create_user_test_cases/test_creating_user_positive_test_cases.py"),
                "test_post_user_endpoint_with_valid_payload",
            ),
            "positive",
        )
        self.assertEqual(
            agent.classify_test(
                Path("test_cases/create_user_test_cases/test_creating_user_negative_test_cases.py"),
                "test_post_user_with_empty_email_error_handling",
            ),
            "negative",
        )

    def test_find_expected_status_codes_reads_response_assertions(self):
        test_node = _first_function(
            """
def test_example():
    response = requests.post('/user/')
    assert response.status_code == 201
"""
        )

        self.assertEqual(agent.find_expected_status_codes(test_node), [201])


class AgentStencilTests(unittest.TestCase):
    def test_stencil_case_applies_only_to_matching_endpoint_shape(self):
        missing_payload_case = agent.StencilCase(
            id="missing_payload",
            category="negative",
            applies_to_methods=("POST", "PUT", "PATCH"),
            requires_path_params=False,
            requires_request_body=True,
            description="",
        )
        invalid_path_case = agent.StencilCase(
            id="invalid_path_parameter_type",
            category="negative",
            applies_to_methods=("GET", "PUT", "PATCH", "DELETE"),
            requires_path_params=True,
            requires_request_body=False,
            description="",
        )

        self.assertTrue(
            agent.stencil_case_applies_to_endpoint(
                missing_payload_case,
                agent.Endpoint(method="POST", path="/user/", function_name="create_user"),
            )
        )
        self.assertFalse(
            agent.stencil_case_applies_to_endpoint(
                missing_payload_case,
                agent.Endpoint(method="GET", path="/user/{user_id}", function_name="get_user"),
            )
        )
        self.assertTrue(
            agent.stencil_case_applies_to_endpoint(
                invalid_path_case,
                agent.Endpoint(method="GET", path="/user/{user_id}", function_name="get_user"),
            )
        )

    def test_test_matches_stencil_case_identifies_success_and_not_found(self):
        success_case = agent.StencilCase(
            id="success_happy_path",
            category="positive",
            applies_to_methods=("GET",),
            requires_path_params=False,
            requires_request_body=False,
            description="",
        )
        not_found_case = agent.StencilCase(
            id="not_found_unknown_resource",
            category="negative",
            applies_to_methods=("GET",),
            requires_path_params=True,
            requires_request_body=False,
            description="",
        )

        success_test = _test_request("GET", "/user/{user_id}", "test_get_user_with_valid_id", (200,))
        missing_test = _test_request("GET", "/user/{missing_user_id}", "test_get_user_with_unknown_id_returns_404", (404,))

        self.assertTrue(agent.test_matches_stencil_case(success_test, success_case))
        self.assertTrue(agent.test_matches_stencil_case(missing_test, not_found_case))
        self.assertFalse(agent.test_matches_stencil_case(success_test, not_found_case))

    def test_current_stencil_audit_reports_known_missing_get_cases(self):
        results = agent.audit_against_stencil()
        by_endpoint = {(result.endpoint.method, result.endpoint.path): result for result in results}

        get_result = by_endpoint[("GET", "/user/{user_id}")]
        missing_case_ids = {case.id for case in get_result.missing_cases}

        self.assertIn("not_found_unknown_resource", missing_case_ids)
        self.assertIn("invalid_path_parameter_type", missing_case_ids)


class AgentFixtureRepoTests(unittest.TestCase):
    def test_fixture_repo_audit_finds_missing_stencil_cases(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            _write_fixture_repo(
                repo_root,
                app_source="""
app = object()


@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    pass


@app.post("/orders/")
async def create_order(order: dict):
    pass
""",
                test_source="""
import requests
from api_config import get_url


def test_get_order_with_valid_id():
    order_id = "1"
    response = requests.get(get_url('orders') + order_id)
    assert response.status_code == 200


def test_post_order_with_valid_payload():
    response = requests.post(get_url('orders'), json={"name": "Coffee"})
    assert response.status_code == 201
""",
            )

            with _patched_agent_paths(repo_root):
                results = agent.audit_against_stencil()

        by_endpoint = {(result.endpoint.method, result.endpoint.path): result for result in results}
        get_missing = {case.id for case in by_endpoint[("GET", "/orders/{order_id}")].missing_cases}
        post_missing = {case.id for case in by_endpoint[("POST", "/orders/")].missing_cases}

        self.assertEqual(
            get_missing,
            {"not_found_unknown_resource", "invalid_path_parameter_type"},
        )
        self.assertEqual(
            post_missing,
            {
                "missing_payload",
                "missing_required_field",
                "invalid_payload_data_type",
                "malformed_json",
            },
        )

    def test_fixture_repo_audit_passes_when_all_stencil_cases_exist(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            _write_fixture_repo(
                repo_root,
                app_source="""
app = object()


@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    pass


@app.post("/orders/")
async def create_order(order: dict):
    pass
""",
                test_source="""
import requests
from api_config import get_url


def test_get_order_with_valid_id():
    order_id = "1"
    response = requests.get(get_url('orders') + order_id)
    assert response.status_code == 200


def test_get_order_with_unknown_id_returns_404():
    missing_order_id = "999999"
    response = requests.get(get_url('orders') + missing_order_id)
    assert response.status_code == 404


def test_get_order_with_invalid_id_type_returns_validation_error():
    response = requests.get(get_url('orders') + "abc")
    assert response.status_code == 422


def test_post_order_with_valid_payload():
    response = requests.post(get_url('orders'), json={"name": "Coffee"})
    assert response.status_code == 201


def test_post_order_with_missing_payload_returns_validation_error():
    response = requests.post(get_url('orders'))
    assert response.status_code == 422


def test_post_order_with_missing_required_field_returns_validation_error():
    response = requests.post(get_url('orders'), json={})
    assert response.status_code == 422


def test_post_order_with_invalid_payload_data_type_returns_validation_error():
    response = requests.post(get_url('orders'), json={"name": 123})
    assert response.status_code == 422


def test_post_order_with_malformed_json_returns_validation_error():
    response = requests.post(get_url('orders'), data="{bad json")
    assert response.status_code == 422
""",
            )

            with _patched_agent_paths(repo_root):
                output = io.StringIO()
                with redirect_stdout(output):
                    agent.print_stencil_audit_report()
                results = agent.audit_against_stencil()

        self.assertTrue(all(not result.missing_cases for result in results))
        self.assertIn("No stencil gaps found.", output.getvalue())


def _first_call(source: str) -> ast.Call:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            return node
    raise AssertionError("No call found in source")


def _first_function(source: str) -> ast.FunctionDef:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            return node
    raise AssertionError("No function found in source")


def _test_request(method: str, path_hint: str, test_name: str, status_codes: tuple[int, ...]) -> agent.TestRequest:
    return agent.TestRequest(
        method=method,
        path_hint=path_hint,
        file_path=Path("test_cases/example_test.py"),
        test_name=test_name,
        line_number=1,
        classification="positive",
        expected_status_codes=status_codes,
        scenario=test_name.removeprefix("test_"),
        payload_style="no_payload",
        response_validation=(),
        database_validation=False,
    )


def _write_fixture_repo(repo_root: Path, app_source: str, test_source: str) -> None:
    test_cases_dir = repo_root / "test_cases"
    test_cases_dir.mkdir()
    (repo_root / "app.py").write_text(app_source, encoding="utf-8")
    (repo_root / "api_config.py").write_text(
        """
endpoints = {
    'orders': '/orders/'
}
""",
        encoding="utf-8",
    )
    (test_cases_dir / "test_orders.py").write_text(test_source, encoding="utf-8")


def _patched_agent_paths(repo_root: Path):
    return patch.multiple(
        agent,
        PROJECT_ROOT=repo_root,
        APP_FILE=repo_root / "app.py",
        API_CONFIG_FILE=repo_root / "api_config.py",
        TEST_CASES_DIR=repo_root / "test_cases",
    )


if __name__ == "__main__":
    unittest.main()
