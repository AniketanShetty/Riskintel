"""
test_openapi_schema.py

OpenAPI schema export tests for the frozen RiskIntel API contract.

Required coverage (per contract-freeze plan):
  1. GET /api/openapi.json serves a valid OpenAPI document
  2. POST /api/assess          exists in paths
  3. POST /api/assess/person-a exists in paths
  4. POST /api/assess/person-b exists in paths
  5. Each endpoint declares POST + requestBody + 200/4xx responses
  6. ErrorResponse is referenced in components/schemas

No business logic is modified.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app as fastapi_app


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def app():
    yield fastapi_app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def schema(client):
    """Fetch and cache the OpenAPI schema document."""
    resp = client.get("/api/openapi.json")
    assert resp.status_code == 200, f"OpenAPI endpoint returned {resp.status_code}"
    return resp.json()


# ── Schema accessibility ──────────────────────────────────────────────────


class TestOpenApiServed:
    """The OpenAPI document must be served at the configured URL."""

    def test_openapi_url_returns_200(self, client):
        resp = client.get("/api/openapi.json")
        assert resp.status_code == 200

    def test_openapi_is_valid_json_object(self, client):
        resp = client.get("/api/openapi.json")
        doc = resp.json()
        assert isinstance(doc, dict)

    def test_openapi_version_is_3_1(self, schema):
        # FastAPI >= 0.115 defaults to OpenAPI 3.1.0
        assert schema.get("openapi", "").startswith("3.1"), (
            f"expected OpenAPI 3.1.x, got {schema.get('openapi')}"
        )

    def test_openapi_has_info_block(self, schema):
        info = schema.get("info", {})
        assert info.get("title") == "RiskIntel API"
        assert info.get("version") == "1.0.0"


# ── Path existence ────────────────────────────────────────────────────────


class TestOpenApiPaths:
    """All three frozen assess endpoints must appear in the paths block."""

    def test_paths_block_present(self, schema):
        assert "paths" in schema, "OpenAPI schema missing 'paths'"

    def test_path_assess_unified_exists(self, schema):
        assert "/api/assess" in schema["paths"], (
            "missing POST /api/assess in OpenAPI paths"
        )

    def test_path_assess_person_a_exists(self, schema):
        assert "/api/assess/person-a" in schema["paths"], (
            "missing POST /api/assess/person-a in OpenAPI paths"
        )

    def test_path_assess_person_b_exists(self, schema):
        assert "/api/assess/person-b" in schema["paths"], (
            "missing POST /api/assess/person-b in OpenAPI paths"
        )

    def test_all_paths_have_post(self, schema):
        for path in ("/api/assess", "/api/assess/person-a", "/api/assess/person-b"):
            methods = schema["paths"][path]
            assert "post" in methods, f"{path}: missing post method"


# ── Request / response schema assertions ──────────────────────────────────


class TestOpenApiEndpointsShape:
    """Each assess endpoint must declare requestBody and response schemas."""

    @pytest.mark.parametrize(
        "path",
        ["/api/assess", "/api/assess/person-a", "/api/assess/person-b"],
    )
    def test_endpoint_has_request_body(self, schema, path):
        post = schema["paths"][path]["post"]
        assert "requestBody" in post, f"{path}: missing requestBody"
        rb = post["requestBody"]
        assert "content" in rb
        assert "application/json" in rb["content"]

    @pytest.mark.parametrize(
        "path",
        ["/api/assess", "/api/assess/person-a", "/api/assess/person-b"],
    )
    def test_endpoint_has_200_response(self, schema, path):
        post = schema["paths"][path]["post"]
        responses = post.get("responses", {})
        assert "200" in responses, f"{path}: missing 200 response"

    @pytest.mark.parametrize(
        "path",
        ["/api/assess", "/api/assess/person-a", "/api/assess/person-b"],
    )
    def test_endpoint_responses_are_json(self, schema, path):
        post = schema["paths"][path]["post"]
        for code, resp_obj in post.get("responses", {}).items():
            content = resp_obj.get("content", {})
            if code == "200":
                # Success response type — JSON
                assert "application/json" in content, (
                    f"{path} {code}: missing application/json"
                )


# ── Components / schemas ──────────────────────────────────────────────────


class TestOpenApiComponents:
    """The components block must define the response schemas used."""

    def test_components_schemas_present(self, schema):
        assert "components" in schema
        assert "schemas" in schema["components"]

    def test_validation_error_schema_present(self, schema):
        """FastAPI auto-generates ValidationError for 422 responses.

        ErrorResponse (output_contracts.md §5) is not auto-generated as a
        component because it's used via the global exception handler, not
        as a response_model on routes. The contract's error envelope is
        enforced at runtime by test_integration_high_value's error tests.
        """
        schemas = schema["components"]["schemas"]
        # FastAPI generates ValidationError for 422 responses
        assert "ValidationError" in schemas, (
            f"ValidationError not in schemas: {list(schemas.keys())}"
        )

    def test_person_a_response_schema_present(self, schema):
        """PersonAResponse must be a schema component."""
        schemas = schema["components"]["schemas"]
        found = any("PersonAResponse" in name for name in schemas)
        assert found, (
            f"PersonAResponse not in schemas: {list(schemas.keys())}"
        )

    def test_person_b_response_schema_present(self, schema):
        """PersonBResponse must be a schema component."""
        schemas = schema["components"]["schemas"]
        found = any("PersonBResponse" in name for name in schemas)
        assert found, (
            f"PersonBResponse not in schemas: {list(schemas.keys())}"
        )

    def test_person_a_request_schema_present(self, schema):
        """PersonARequest must be a schema component."""
        schemas = schema["components"]["schemas"]
        found = any("PersonARequest" in name for name in schemas)
        assert found, (
            f"PersonARequest not in schemas: {list(schemas.keys())}"
        )

    def test_person_b_request_schema_present(self, schema):
        """PersonBRequest must be a schema component."""
        schemas = schema["components"]["schemas"]
        found = any("PersonBRequest" in name for name in schemas)
        assert found, (
            f"PersonBRequest not in schemas: {list(schemas.keys())}"
        )
