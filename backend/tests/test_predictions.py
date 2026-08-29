from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_severity_prediction():
    response = client.post(
        "/api/v1/predictions/severity",
        json={
            "category": "POTHOLE",
            "ward_code": "W001",
            "repeat_count": 0,
            "description_length": 50,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "predicted_severity" in data
    assert data["predicted_severity"] in {
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW",
    }


def test_resolution_time_prediction():
    response = client.post(
        "/api/v1/predictions/resolution-time",
        json={
            "category": "POTHOLE",
            "department": "ROADS",
            "severity": "HIGH",
            "ward_code": "W001",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "predicted_resolution_days" in data
    assert isinstance(data["predicted_resolution_days"], (int, float))
    assert data["predicted_resolution_days"] > 0


def test_severity_invalid_repeat_count():
    response = client.post(
        "/api/v1/predictions/severity",
        json={
            "category": "POTHOLE",
            "ward_code": "W001",
            "repeat_count": -1,
            "description_length": 50,
        },
    )

    assert response.status_code == 422


def test_resolution_invalid_severity():
    response = client.post(
        "/api/v1/predictions/resolution-time",
        json={
            "category": "POTHOLE",
            "department": "ROADS",
            "severity": "URGENT",
            "ward_code": "W001",
        },
    )

    assert response.status_code == 422