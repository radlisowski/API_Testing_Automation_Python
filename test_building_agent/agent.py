import argparse
import ast
import json
from dataclasses import dataclass, field
from pathlib import Path

AGENT_ROOT = Path(__file__).parent
PROJECT_ROOT = AGENT_ROOT.parent
APP_FILE = PROJECT_ROOT / "app.py"
API_CONFIG_FILE = PROJECT_ROOT / "api_config.py"
TEST_CASES_DIR = PROJECT_ROOT / "test_cases"
TEMPLATE_DIR = AGENT_ROOT / "templates"
LEARNED_PATTERNS_FILE = TEMPLATE_DIR / "learned_patterns.json"
API_TEST_STENCIL_FILE = TEMPLATE_DIR / "api_test_stencil.json"
SUPPORTED_HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


@dataclass(frozen=True)
class Endpoint:
    method: str
    path: str
    function_name: str


@dataclass(frozen=True)
class TestRequest:
    method: str
    path_hint: str
    file_path: Path
    test_name: str
    line_number: int
    classification: str
    expected_status_codes: tuple[int, ...]
    scenario: str
    payload_style: str
    response_validation: tuple[str, ...]
    database_validation: bool


@dataclass
class CoverageResult:
    endpoint: Endpoint
    matching_tests: list[TestRequest] = field(default_factory=list)

    @property
    def has_coverage(self) -> bool:
        return bool(self.matching_tests)

    @property
    def positive_tests(self) -> list[TestRequest]:
        return [
            test for test in self.matching_tests if "positive" in test.file_path.as_posix() or "valid" in test.test_name
        ]

    @property
    def negative_tests(self) -> list[TestRequest]:
        return [
            test
            for test in self.matching_tests
            if (
                "negative" in test.file_path.as_posix()
                or "invalid" in test.test_name
                or "unknown" in test.test_name
                or "error" in test.test_name
            )
        ]


@dataclass(frozen=True)
class StencilCase:
    id: str
    category: str
    applies_to_methods: tuple[str, ...]
    requires_path_params: bool
    requires_request_body: bool
    description: str


@dataclass(frozen=True)
class TestStandard:
    id: str
    category: str
    description: str


@dataclass(frozen=True)
class StencilAuditResult:
    endpoint: Endpoint
    required_cases: tuple[StencilCase, ...]
    covered_case_ids: tuple[str, ...]

    @property
    def missing_cases(self) -> list[StencilCase]:
        return [case for case in self.required_cases if case.id not in self.covered_case_ids]

    @property
    def has_missing_cases(self) -> bool:
        return bool(self.missing_cases)


@dataclass(frozen=True)
class StandardsAuditResult:
    standard: TestStandard
    covered: bool
    evidence: tuple[str, ...]


def load_fastapi_endpoints() -> list[Endpoint]:
    """Return endpoints defined with decorators such as @app.get('/user/{user_id}')."""
    endpoints = []

    for file_path in iter_python_files_for_endpoint_scan():
        endpoints.extend(load_fastapi_endpoints_from_file(file_path))

    return sorted(endpoints, key=lambda endpoint: (endpoint.path, endpoint.method))


def iter_python_files_for_endpoint_scan() -> list[Path]:
    excluded_dirs = {".git", "__pycache__", "test_cases", "test_building_agent"}
    return [
        file_path
        for file_path in sorted(PROJECT_ROOT.rglob("*.py"))
        if not any(part in excluded_dirs for part in file_path.relative_to(PROJECT_ROOT).parts)
    ]


def load_fastapi_endpoints_from_file(file_path: Path) -> list[Endpoint]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    endpoints = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if not isinstance(decorator.func, ast.Attribute):
                continue
            if not isinstance(decorator.func.value, ast.Name):
                continue
            if decorator.func.value.id not in {"app", "router"}:
                continue
            if decorator.func.attr not in SUPPORTED_HTTP_METHODS:
                continue
            if not decorator.args or not isinstance(decorator.args[0], ast.Constant):
                continue

            endpoints.append(
                Endpoint(
                    method=decorator.func.attr.upper(),
                    path=decorator.args[0].value,
                    function_name=node.name,
                )
            )

    return endpoints


def load_stencil_data() -> dict:
    return json.loads(API_TEST_STENCIL_FILE.read_text(encoding="utf-8"))


def load_api_test_stencil() -> list[StencilCase]:
    data = load_stencil_data()
    cases = []

    for case_data in data["test_cases"]:
        cases.append(
            StencilCase(
                id=case_data["id"],
                category=case_data["category"],
                applies_to_methods=tuple(case_data["applies_to_methods"]),
                requires_path_params=case_data["requires_path_params"],
                requires_request_body=case_data["requires_request_body"],
                description=case_data["description"],
            )
        )

    return cases


def load_test_standards() -> list[TestStandard]:
    data = load_stencil_data()
    standards = []

    for standard_data in data.get("test_standards", []):
        standards.append(
            TestStandard(
                id=standard_data["id"],
                category=standard_data["category"],
                description=standard_data["description"],
            )
        )

    return standards


def load_endpoint_aliases() -> dict[str, str]:
    """Read api_config.endpoints so get_url('user') can be resolved to /user/."""
    tree = ast.parse(API_CONFIG_FILE.read_text(encoding="utf-8"))

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "endpoints" for target in node.targets):
            continue
        if not isinstance(node.value, ast.Dict):
            continue

        aliases = {}
        for key, value in zip(node.value.keys, node.value.values):
            if isinstance(key, ast.Constant) and isinstance(value, ast.Constant):
                aliases[str(key.value)] = str(value.value)
        return aliases

    return {}


def load_test_requests(endpoint_aliases: dict[str, str]) -> list[TestRequest]:
    """Find requests.<method>(...) calls in pytest test files."""
    requests_found = []

    for file_path in sorted(TEST_CASES_DIR.rglob("test_*.py")):
        tree = ast.parse(file_path.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
                continue
            for child in ast.walk(node):
                if not is_requests_call(child):
                    continue

                path_hint = resolve_request_path(child, endpoint_aliases)
                requests_found.append(
                    TestRequest(
                        method=child.func.attr.upper(),
                        path_hint=path_hint,
                        file_path=file_path,
                        test_name=node.name,
                        line_number=child.lineno,
                        classification=classify_test(file_path, node.name),
                        expected_status_codes=tuple(find_expected_status_codes(node)),
                        scenario=describe_scenario(node.name),
                        payload_style=describe_payload_style(node, child),
                        response_validation=tuple(describe_response_validation(node)),
                        database_validation=has_database_validation(node),
                    )
                )

    return requests_found


def is_requests_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    if not isinstance(node.func, ast.Attribute):
        return False
    if not isinstance(node.func.value, ast.Name):
        return False
    if node.func.value.id != "requests":
        return False
    return node.func.attr in SUPPORTED_HTTP_METHODS


def classify_test(file_path: Path, test_name: str) -> str:
    searchable_text = f"{file_path.as_posix()} {test_name}"
    if any(word in searchable_text for word in ("negative", "invalid", "unknown", "error", "empty", "missing")):
        return "negative"
    if any(word in searchable_text for word in ("positive", "valid", "mandatory")):
        return "positive"
    return "unknown"


def find_expected_status_codes(test_node: ast.FunctionDef) -> list[int]:
    status_codes = []

    for node in ast.walk(test_node):
        if not isinstance(node, ast.Compare):
            continue
        if not isinstance(node.left, ast.Attribute) or node.left.attr != "status_code":
            continue
        if not node.comparators or not isinstance(node.comparators[0], ast.Constant):
            continue
        status_code = node.comparators[0].value
        if isinstance(status_code, int):
            status_codes.append(status_code)

    return status_codes


def describe_scenario(test_name: str) -> str:
    scenario = test_name
    for prefix in ("test_",):
        if scenario.startswith(prefix):
            scenario = scenario[len(prefix) :]
    return scenario


def describe_payload_style(test_node: ast.FunctionDef, request_call: ast.Call) -> str:
    json_payload = None
    for keyword in request_call.keywords:
        if keyword.arg == "json":
            json_payload = keyword.value
            break

    if json_payload is None:
        return "no_payload"

    calls = [node for node in ast.walk(test_node) if isinstance(node, ast.Call)]
    call_names = {get_call_name(call) for call in calls}

    if "User" in call_names and "Address" in call_names and "PhoneNumber" in call_names:
        return "full_user_model_payload"
    if "User" in call_names:
        return "user_model_payload"
    if isinstance(json_payload, ast.Dict):
        return "dict_payload"
    return "dynamic_payload"


def get_call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def describe_response_validation(test_node: ast.FunctionDef) -> list[str]:
    validations = []
    call_names = {get_call_name(node) for node in ast.walk(test_node) if isinstance(node, ast.Call)}

    if "json.loads" in ast.unparse(test_node):
        validations.append("parse_json_response")
    if response_model_is_used(test_node, "User"):
        validations.append("validate_user_response_model")
    if response_model_is_used(test_node, "UserErrorResponse"):
        validations.append("validate_error_response_model")
    if "assert_user_attributes" in call_names:
        validations.append("assert_user_attributes")
    if "assert_user_addresses" in call_names:
        validations.append("assert_user_addresses")
    if any(isinstance(node, ast.Subscript) for node in ast.walk(test_node)):
        validations.append("assert_response_field")

    return validations


def response_model_is_used(test_node: ast.FunctionDef, model_name: str) -> bool:
    for node in ast.walk(test_node):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        if get_call_name(node.value) != model_name:
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and "response" in target.id:
                return True
    return False


def has_database_validation(test_node: ast.FunctionDef) -> bool:
    searchable_text = ast.unparse(test_node)
    return "get_user_db_collection" in searchable_text or "database_record" in searchable_text


def resolve_request_path(node: ast.Call, endpoint_aliases: dict[str, str]) -> str:
    if not node.args:
        return "<unknown>"
    return resolve_expression_path(node.args[0], endpoint_aliases)


def resolve_expression_path(node: ast.AST, endpoint_aliases: dict[str, str]) -> str:
    if isinstance(node, ast.Call):
        return resolve_call_path(node, endpoint_aliases)

    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = resolve_expression_path(node.left, endpoint_aliases)
        right = resolve_expression_path(node.right, endpoint_aliases)
        return left + right

    if isinstance(node, ast.Constant):
        return str(node.value)

    if isinstance(node, ast.JoinedStr):
        return "".join(resolve_expression_path(value, endpoint_aliases) for value in node.values)

    if isinstance(node, ast.FormattedValue):
        return "{value}"

    if isinstance(node, ast.Name):
        return "{" + node.id + "}"

    return "{dynamic}"


def resolve_call_path(node: ast.Call, endpoint_aliases: dict[str, str]) -> str:
    if isinstance(node.func, ast.Name) and node.func.id == "get_url":
        if node.args and isinstance(node.args[0], ast.Constant):
            return endpoint_aliases.get(str(node.args[0].value), f"<unknown endpoint {node.args[0].value}>")
        return "<unknown get_url>"

    if isinstance(node.func, ast.Name) and node.func.id == "str":
        if node.args and isinstance(node.args[0], ast.Name):
            return "{" + node.args[0].id + "}"
        return "{value}"

    return "{dynamic}"


def paths_match(endpoint_path: str, request_path: str) -> bool:
    endpoint_parts = split_path(endpoint_path)
    request_parts = split_path(request_path)

    if len(endpoint_parts) != len(request_parts):
        return False

    for endpoint_part, request_part in zip(endpoint_parts, request_parts):
        if is_path_parameter(endpoint_part):
            continue
        if is_path_parameter(request_part):
            continue
        if endpoint_part != request_part:
            return False

    return True


def split_path(path: str) -> list[str]:
    return [part for part in path.strip("/").split("/") if part]


def is_path_parameter(path_part: str) -> bool:
    return path_part.startswith("{") and path_part.endswith("}")


def audit_coverage() -> list[CoverageResult]:
    endpoints = load_fastapi_endpoints()
    endpoint_aliases = load_endpoint_aliases()
    test_requests = load_test_requests(endpoint_aliases)
    results = []

    for endpoint in endpoints:
        matching_tests = [
            test_request
            for test_request in test_requests
            if test_request.method == endpoint.method and paths_match(endpoint.path, test_request.path_hint)
        ]
        results.append(CoverageResult(endpoint=endpoint, matching_tests=matching_tests))

    return results


def audit_against_stencil() -> list[StencilAuditResult]:
    coverage_results = audit_coverage()
    stencil_cases = load_api_test_stencil()
    audit_results = []

    for result in coverage_results:
        required_cases = tuple(
            case for case in stencil_cases if stencil_case_applies_to_endpoint(case, result.endpoint)
        )
        covered_case_ids = tuple(
            case.id
            for case in required_cases
            if any(test_matches_stencil_case(test, case) for test in result.matching_tests)
        )
        audit_results.append(
            StencilAuditResult(
                endpoint=result.endpoint,
                required_cases=required_cases,
                covered_case_ids=covered_case_ids,
            )
        )

    return audit_results


def audit_test_standards() -> list[StandardsAuditResult]:
    endpoint_aliases = load_endpoint_aliases()
    test_requests = load_test_requests(endpoint_aliases)
    test_files = list_test_files() + list_test_support_files()
    source_by_file = {file_path: file_path.read_text(encoding="utf-8") for file_path in test_files}
    all_test_source = "\n".join(source_by_file.values())
    results = []

    for standard in load_test_standards():
        covered, evidence = standard_is_covered(standard, test_requests, source_by_file, all_test_source)
        results.append(StandardsAuditResult(standard=standard, covered=covered, evidence=tuple(evidence)))

    return results


def list_test_files() -> list[Path]:
    return sorted(TEST_CASES_DIR.rglob("test_*.py"))


def list_test_support_files() -> list[Path]:
    return sorted(TEST_CASES_DIR.rglob("conftest.py"))


def standard_is_covered(
    standard: TestStandard,
    test_requests: list[TestRequest],
    source_by_file: dict[Path, str],
    all_test_source: str,
) -> tuple[bool, list[str]]:
    if standard.id == "api_integration_tests":
        if test_requests:
            return True, [f"Found {len(test_requests)} HTTP request-based test(s)."]
        return False, ["No requests.get/post/delete/put/patch calls found in test files."]

    if standard.id == "service_unit_tests":
        service_tests = [file_path for file_path in source_by_file if "service" in file_path.as_posix().lower()]
        service_tests.extend(find_files_with_service_test_functions(source_by_file))
        if service_tests:
            return True, [f"Found service-oriented test file/source: {path}" for path in service_tests]
        return False, ["No service/business-logic unit tests detected."]

    if standard.id == "fixture_data_factories":
        if "@pytest.fixture" in all_test_source or "factory" in all_test_source.lower():
            return True, ["Found pytest fixtures or factory-style helpers in test source."]
        return False, ["No pytest fixtures or factory-style test data helpers detected."]

    if standard.id == "per_test_database_cleanup":
        if has_per_test_database_cleanup(source_by_file):
            return True, ["Detected function-scoped/autouse database cleanup or per-test delete_many usage."]
        return False, ["Database cleanup does not appear to run automatically for every test."]

    if standard.id == "parametrized_negative_tests":
        if "@pytest.mark.parametrize" in all_test_source and "negative" in all_test_source.lower():
            return True, ["Found pytest parametrization in negative-test source."]
        return False, ["No parametrized negative tests detected."]

    if standard.id == "validation_error_tests":
        return validation_error_standard_result(test_requests)

    if standard.id == "coverage_report":
        project_config = read_project_quality_config()
        if "pytest-cov" in project_config or "--cov" in project_config:
            return True, ["Detected pytest-cov dependency or --cov command/config."]
        return False, ["No pytest-cov dependency or coverage command/config detected."]

    return False, [f"No detector implemented for standard '{standard.id}'."]


def find_files_with_service_test_functions(source_by_file: dict[Path, str]) -> list[Path]:
    matching_files = []
    for file_path, source in source_by_file.items():
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_") and "service" in node.name:
                matching_files.append(file_path)
                break
    return matching_files


def has_per_test_database_cleanup(source_by_file: dict[Path, str]) -> bool:
    for source in source_by_file.values():
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            function_source = ast.unparse(node).replace(" ", "").lower()
            if "delete_many(" not in function_source:
                continue
            if "@pytest.fixture" in function_source and (
                "scope='function'" in function_source
                or 'scope="function"' in function_source
                or "autouse=true" in function_source
            ):
                return True
    return False


def validation_error_standard_result(test_requests: list[TestRequest]) -> tuple[bool, list[str]]:
    status_codes = {status_code for test in test_requests for status_code in test.expected_status_codes}
    scenarios = " ".join(test.scenario for test in test_requests).lower()
    missing = []

    for status_code in (400, 404, 422):
        if status_code not in status_codes:
            missing.append(str(status_code))
    if "duplicate" not in scenarios and "already_exists" not in scenarios:
        missing.append("duplicate data")
    if "malformed_json" not in scenarios and "invalid_json" not in scenarios:
        missing.append("malformed JSON")

    if not missing:
        return True, ["Detected 400, 404, 422, duplicate-data, and malformed-JSON test coverage."]

    return False, [f"Missing validation/error coverage for: {', '.join(missing)}."]


def read_project_quality_config() -> str:
    candidate_files = [PROJECT_ROOT / "requirements.txt", PROJECT_ROOT / "pyproject.toml", PROJECT_ROOT / "readme.md"]
    return "\n".join(file_path.read_text(encoding="utf-8") for file_path in candidate_files if file_path.exists())


def stencil_case_applies_to_endpoint(case: StencilCase, endpoint: Endpoint) -> bool:
    if endpoint.method not in case.applies_to_methods:
        return False
    if case.requires_path_params and not endpoint_has_path_params(endpoint):
        return False
    if case.requires_request_body and not endpoint_accepts_request_body(endpoint):
        return False
    return True


def endpoint_has_path_params(endpoint: Endpoint) -> bool:
    return any(is_path_parameter(part) for part in split_path(endpoint.path))


def endpoint_accepts_request_body(endpoint: Endpoint) -> bool:
    return endpoint.method in {"POST", "PUT", "PATCH"}


def test_matches_stencil_case(test: TestRequest, case: StencilCase) -> bool:
    searchable_text = f"{test.test_name} {test.scenario} {test.file_path.as_posix()}".lower()
    status_codes = set(test.expected_status_codes)

    if case.id == "success_happy_path":
        return any(200 <= status_code < 300 for status_code in status_codes)

    if case.id == "not_found_unknown_resource":
        return 404 in status_codes or any(word in searchable_text for word in ("not_found", "unknown", "missing_id"))

    if case.id == "invalid_path_parameter_type":
        return any(
            word in searchable_text
            for word in ("invalid_id", "invalid_path", "wrong_id", "incorrect_id", "data_type", "type")
        )

    if case.id == "missing_payload":
        return any(
            word in searchable_text for word in ("missing_payload", "empty_payload", "no_payload", "without_payload")
        )

    if case.id == "missing_required_field":
        return any(
            word in searchable_text for word in ("missing_required", "required", "empty_", "blank_", "missing_field")
        )

    if case.id == "invalid_payload_data_type":
        return any(word in searchable_text for word in ("invalid_type", "wrong_type", "incorrect_type", "data_type"))

    if case.id == "malformed_json":
        return any(word in searchable_text for word in ("malformed_json", "invalid_json", "bad_json"))

    return False


def learn_patterns() -> dict:
    """Create a reviewable pattern library from existing tests."""
    results = audit_coverage()
    patterns = {
        "version": 1,
        "source": {
            "app_file": str(APP_FILE.relative_to(PROJECT_ROOT)),
            "test_cases_dir": str(TEST_CASES_DIR.relative_to(PROJECT_ROOT)),
        },
        "method_patterns": {},
        "gaps": [],
    }

    for result in results:
        method_key = result.endpoint.method
        method_patterns = patterns["method_patterns"].setdefault(
            method_key,
            {
                "positive": [],
                "negative": [],
                "unknown": [],
            },
        )

        if not result.positive_tests:
            patterns["gaps"].append(
                {
                    "method": result.endpoint.method,
                    "path": result.endpoint.path,
                    "missing": "positive",
                }
            )
        if not result.negative_tests:
            patterns["gaps"].append(
                {
                    "method": result.endpoint.method,
                    "path": result.endpoint.path,
                    "missing": "negative",
                }
            )

        for test in result.matching_tests:
            classification = test.classification
            if classification not in method_patterns:
                classification = "unknown"
            method_patterns[classification].append(
                {
                    "endpoint_path": result.endpoint.path,
                    "endpoint_function": result.endpoint.function_name,
                    "test_file": str(test.file_path.relative_to(PROJECT_ROOT)),
                    "test_name": test.test_name,
                    "line_number": test.line_number,
                    "scenario": test.scenario,
                    "path_hint": test.path_hint,
                    "expected_status_codes": list(test.expected_status_codes),
                    "payload_style": test.payload_style,
                    "response_validation": list(test.response_validation),
                    "database_validation": test.database_validation,
                }
            )

    return patterns


def save_learned_patterns() -> None:
    patterns = learn_patterns()
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    LEARNED_PATTERNS_FILE.write_text(
        json.dumps(patterns, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {LEARNED_PATTERNS_FILE.relative_to(PROJECT_ROOT)}")
    print_pattern_summary(patterns)


def print_pattern_summary(patterns: dict) -> None:
    print("\nLearned Pattern Summary")
    print("=======================")
    for method, method_patterns in sorted(patterns["method_patterns"].items()):
        positive_count = len(method_patterns["positive"])
        negative_count = len(method_patterns["negative"])
        unknown_count = len(method_patterns["unknown"])
        print(f"{method:8} positive={positive_count} negative={negative_count} unknown={unknown_count}")

    if patterns["gaps"]:
        print("\nTemplate gaps:")
        for gap in patterns["gaps"]:
            print(f"- {gap['method']} {gap['path']} missing {gap['missing']} pattern")


def print_endpoint_list() -> None:
    for endpoint in load_fastapi_endpoints():
        print(f"{endpoint.method:12} {endpoint.path:20} {endpoint.function_name}")


def print_audit_report() -> None:
    results = audit_coverage()

    print("Endpoint Coverage Audit")
    print("=======================")

    for result in results:
        status = "COVERED" if result.has_coverage else "MISSING"
        endpoint = result.endpoint
        print(f"\n[{status}] {endpoint.method} {endpoint.path} -> {endpoint.function_name}")

        if not result.has_coverage:
            continue

        print(f"  tests found: {len(result.matching_tests)}")
        print(f"  positive-looking tests: {len(result.positive_tests)}")
        print(f"  negative-looking tests: {len(result.negative_tests)}")

        if not result.positive_tests:
            print("  missing test type: positive")
        if not result.negative_tests:
            print("  missing test type: negative")

        for test in result.matching_tests:
            relative_path = test.file_path.relative_to(PROJECT_ROOT)
            print(f"  - {relative_path}:{test.line_number}::{test.test_name}")

    missing_count = sum(1 for result in results if not result.has_coverage)
    missing_test_type_count = sum(1 for result in results if not result.positive_tests or not result.negative_tests)
    template_ready_count = len(results) - missing_test_type_count
    print(f"\nSummary: {len(results) - missing_count}/{len(results)} endpoints have at least one matching test.")
    print(
        f"Template readiness: {template_ready_count}/{len(results)} endpoints have both positive and "
        "negative-looking tests."
    )

    if missing_count:
        print("Missing endpoints:")
        for result in results:
            if not result.has_coverage:
                print(f"  - {result.endpoint.method} {result.endpoint.path}")

    if missing_test_type_count:
        print("Endpoints missing a test type:")
        for result in results:
            missing_types = []
            if not result.positive_tests:
                missing_types.append("positive")
            if not result.negative_tests:
                missing_types.append("negative")
            if missing_types:
                print(f"  - {result.endpoint.method} {result.endpoint.path}: {', '.join(missing_types)}")


def print_stencil_audit_report() -> None:
    results = audit_against_stencil()

    print("API Stencil Coverage Report")
    print("===========================")

    missing_result_count = 0
    missing_case_count = 0

    for result in results:
        endpoint = result.endpoint
        print(f"\n{endpoint.method} {endpoint.path} -> {endpoint.function_name}")

        covered_cases = [case for case in result.required_cases if case.id in result.covered_case_ids]
        if covered_cases:
            print("  Existing tests:")
            for covered_case in covered_cases:
                print(f"    - [{covered_case.category}] {covered_case.id}")
        else:
            print("  Existing tests: none matched to the stencil")

        if not result.has_missing_cases:
            print("  Missing tests: none")
            continue

        missing_result_count += 1
        missing_case_count += len(result.missing_cases)
        print("  Missing tests:")
        for missing_case in result.missing_cases:
            print(f"    - [{missing_case.category}] {missing_case.id}")
            print(f"      {missing_case.description}")

    if missing_case_count == 0:
        print("\nNo stencil gaps found.")
        return

    print(f"\nSummary: {missing_case_count} missing stencil test(s) across {missing_result_count} endpoint(s).")


def print_standards_audit_report() -> None:
    results = audit_test_standards()

    print("API Testing Standards Report")
    print("============================")

    missing_count = 0
    for result in results:
        status = "COVERED" if result.covered else "MISSING"
        standard = result.standard
        print(f"\n[{status}] {standard.id}")
        print(f"  category: {standard.category}")
        print(f"  standard: {standard.description}")
        for evidence in result.evidence:
            print(f"  evidence: {evidence}")

        if not result.covered:
            missing_count += 1

    if missing_count == 0:
        print("\nAll testing standards are covered.")
        return

    print(f"\nSummary: {missing_count} missing testing standard(s).")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit FastAPI endpoints against existing pytest request coverage.")
    parser.add_argument(
        "--list",
        action="store_true",
        help="List endpoints exposed by app.py.",
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Audit endpoint coverage in test_cases.",
    )
    parser.add_argument(
        "--learn-templates",
        action="store_true",
        help="Learn and store test patterns from existing test_cases.",
    )
    parser.add_argument(
        "--stencil-audit",
        action="store_true",
        help="Compare endpoints and tests against the generic API test stencil.",
    )
    parser.add_argument(
        "--standards-audit",
        action="store_true",
        help="Compare the repo against generic API testing standards.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.list:
        print_endpoint_list()

    if args.audit:
        print_audit_report()

    if args.learn_templates:
        save_learned_patterns()

    if args.stencil_audit:
        print_stencil_audit_report()

    if args.standards_audit:
        print_standards_audit_report()

    no_command_selected = not (
        args.list or args.audit or args.learn_templates or args.stencil_audit or args.standards_audit
    )
    if no_command_selected:
        print_audit_report()


if __name__ == "__main__":
    main()
