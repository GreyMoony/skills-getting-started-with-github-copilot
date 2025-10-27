import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client():
    with TestClient(app_module.app) as c:
        yield c


@pytest.fixture(autouse=True)
def restore_activities():
    # Make a deep copy of the activities dict before each test and restore after.
    orig = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(orig)


def test_get_activities(client):
    res = client.get("/activities")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, dict)
    # Expect at least one known activity from the seeded data
    assert "Chess Club" in data


def test_signup_and_unregister_flow(client):
    activity = "Chess Club"
    email = "testuser@example.com"

    # Ensure email not present initially
    data = client.get("/activities").json()
    assert email not in data[activity]["participants"]

    # Sign up
    res = client.post(f"/activities/{activity}/signup?email={email}")
    assert res.status_code == 200
    assert "Signed up" in res.json().get("message", "")

    # Now the participant should be present
    data = client.get("/activities").json()
    assert email in data[activity]["participants"]

    # Duplicate signup should fail with 400
    res = client.post(f"/activities/{activity}/signup?email={email}")
    assert res.status_code == 400

    # Unregister
    res = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert res.status_code == 200
    assert "Unregistered" in res.json().get("message", "")

    # Now the participant should be gone
    data = client.get("/activities").json()
    assert email not in data[activity]["participants"]

    # Unregistering again should return 404
    res = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert res.status_code == 404


def test_invalid_activity_handling(client):
    res = client.post("/activities/NoSuchActivity/signup?email=a@b.com")
    assert res.status_code == 404

    res = client.delete("/activities/NoSuchActivity/unregister?email=a@b.com")
    assert res.status_code == 404
