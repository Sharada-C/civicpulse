from fastapi.testclient import TestClient

from app.main import app
from app.api.complaints import get_current_user
from app.models.complaint import User

client = TestClient(app)


def test_protected_endpoint_requires_authentication():
    response = client.patch(
        "/api/v1/complaints/1",
        json={"status": "RESOLVED"},
    )

    assert response.status_code == 401


def test_citizen_cannot_update_complaint():
    citizen = User(
        user_id=999,
        email="citizen@test.com",
        role="CITIZEN",
    )

    app.dependency_overrides[get_current_user] = lambda: citizen

    try:
        response = client.patch(
            "/api/v1/complaints/1",
            json={"status": "RESOLVED"},
        )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()