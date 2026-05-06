import ast
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
