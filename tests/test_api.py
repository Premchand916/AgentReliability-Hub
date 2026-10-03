from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    with TestClient(create_app(database_url)) as test_client:
        yield test_client


@pytest.fixture
def project(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/projects",
        json={"name": "  Support Agent  ", "description": "Evaluation workspace"},
    )
    assert response.status_code == 201
    return response.json()


def valid_case_payload() -> dict[str, object]:
    return {
        "slug": "refund-policy",
        "name": "Refund within 30 days",
        "input": "How long do I have to request a refund?",
        "expectation": {
            "expected_answer": "Refunds are available within 30 days.",
            "expected_tools": ["lookup_policy"],
            "prohibited_text": ["secret-123"],
            "max_latency_ms": 1_000,
            "max_total_tokens": 200,
        },
        "mock_scenario": "pass",
    }


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_describes_phase_two_routes(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()

    assert schema["info"]["title"] == "AgentReliability Hub"
    assert "/api/health" in schema["paths"]
    assert "/api/projects" in schema["paths"]
    assert "/api/projects/{project_id}/cases" in schema["paths"]


def test_create_list_and_read_project(client: TestClient, project: dict[str, object]) -> None:
    project_id = project["id"]

    assert project["name"] == "Support Agent"
    assert client.get(f"/api/projects/{project_id}").json() == project
    assert client.get("/api/projects").json() == {"items": [project]}


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "   "},
        {"name": "valid", "unknown": True},
        {"name": "x" * 101},
    ],
)
def test_reject_invalid_project(client: TestClient, payload: dict[str, object]) -> None:
    response = client.post("/api/projects", json=payload)

    assert response.status_code == 422


def test_unknown_project_uses_stable_error(client: TestClient) -> None:
    response = client.get("/api/projects/missing")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "project_not_found", "message": "Project not found"}
    }


def test_create_and_list_case(
    client: TestClient,
    project: dict[str, object],
) -> None:
    project_id = project["id"]
    response = client.post(
        f"/api/projects/{project_id}/cases",
        json=valid_case_payload(),
    )

    assert response.status_code == 201
    case = response.json()
    assert case["project_id"] == project_id
    assert case["slug"] == "refund-policy"
    assert client.get(f"/api/projects/{project_id}/cases").json() == {"items": [case]}


def test_case_slug_is_unique_within_project(
    client: TestClient,
    project: dict[str, object],
) -> None:
    project_id = project["id"]
    first = client.post(f"/api/projects/{project_id}/cases", json=valid_case_payload())
    duplicate = client.post(f"/api/projects/{project_id}/cases", json=valid_case_payload())

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "duplicate_case_slug"


def test_same_case_slug_is_allowed_in_different_projects(client: TestClient) -> None:
    first_project = client.post("/api/projects", json={"name": "First"}).json()
    second_project = client.post("/api/projects", json={"name": "Second"}).json()

    first = client.post(
        f"/api/projects/{first_project['id']}/cases",
        json=valid_case_payload(),
    )
    second = client.post(
        f"/api/projects/{second_project['id']}/cases",
        json=valid_case_payload(),
    )

    assert first.status_code == 201
    assert second.status_code == 201


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("max_latency_ms", -1),
        ("max_latency_ms", True),
        ("max_total_tokens", -1),
        ("max_total_tokens", True),
    ],
)
def test_reject_invalid_limits(
    client: TestClient,
    project: dict[str, object],
    field: str,
    value: object,
) -> None:
    payload = valid_case_payload()
    expectation = payload["expectation"]
    assert isinstance(expectation, dict)
    expectation[field] = value

    response = client.post(f"/api/projects/{project['id']}/cases", json=payload)

    assert response.status_code == 422


def test_reject_scenario_without_required_expectation(
    client: TestClient,
    project: dict[str, object],
) -> None:
    payload = valid_case_payload()
    payload["mock_scenario"] = "slow"
    expectation = payload["expectation"]
    assert isinstance(expectation, dict)
    expectation["max_latency_ms"] = None

    response = client.post(f"/api/projects/{project['id']}/cases", json=payload)

    assert response.status_code == 422


def test_reject_case_with_missing_required_field(
    client: TestClient,
    project: dict[str, object],
) -> None:
    payload = valid_case_payload()
    del payload["input"]

    response = client.post(f"/api/projects/{project['id']}/cases", json=payload)

    assert response.status_code == 422


def test_project_survives_application_restart(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'restart.db'}"
    with TestClient(create_app(database_url)) as first_client:
        created = first_client.post("/api/projects", json={"name": "Persistent"}).json()

    with TestClient(create_app(database_url)) as restarted_client:
        response = restarted_client.get(f"/api/projects/{created['id']}")

    assert response.status_code == 200
    assert response.json()["name"] == "Persistent"


def test_duplicate_case_rollback_leaves_session_usable(
    client: TestClient,
    project: dict[str, object],
) -> None:
    project_id = project["id"]
    client.post(f"/api/projects/{project_id}/cases", json=valid_case_payload())
    duplicate = client.post(f"/api/projects/{project_id}/cases", json=valid_case_payload())
    second_payload = valid_case_payload()
    second_payload["slug"] = "shipping-policy"
    created_after_rollback = client.post(
        f"/api/projects/{project_id}/cases", json=second_payload
    )

    assert duplicate.status_code == 409
    assert created_after_rollback.status_code == 201
    assert len(client.get(f"/api/projects/{project_id}/cases").json()["items"]) == 2
