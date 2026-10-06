from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
	monkeypatch.setattr(app_module, "activities", deepcopy(app_module.activities))
	return TestClient(app_module.app, follow_redirects=False)


def test_root_redirects_to_static_index(client):
	# Arrange
	expected_location = "/static/index.html"

	# Act
	response = client.get("/")

	# Assert
	assert response.status_code == 307
	assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(client):
	# Arrange
	expected_activities = app_module.activities

	# Act
	response = client.get("/activities")

	# Assert
	assert response.status_code == 200
	assert response.json() == expected_activities


def test_signup_adds_student_to_activity(client):
	# Arrange
	activity_name = "Soccer Club"
	email = "student@example.com"

	# Act
	response = client.post(
		f"/activities/{activity_name}/signup", params={"email": email}
	)

	# Assert
	assert response.status_code == 200
	assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
	assert email in app_module.activities[activity_name]["participants"]


def test_signup_returns_404_for_unknown_activity(client):
	# Arrange
	activity_name = "Unknown Club"

	# Act
	response = client.post(
		f"/activities/{activity_name}/signup",
		params={"email": "student@example.com"},
	)

	# Assert
	assert response.status_code == 404
	assert response.json() == {"detail": "Activity not found"}


def test_signup_returns_400_for_existing_participant(client):
	# Arrange
	activity_name = "Chess Club"
	email = app_module.activities[activity_name]["participants"][0]

	# Act
	response = client.post(
		f"/activities/{activity_name}/signup", params={"email": email}
	)

	# Assert
	assert response.status_code == 400
	assert response.json() == {
		"detail": "Student already signed up for this activity"
	}


def test_signup_returns_400_for_full_activity(client):
	# Arrange
	activity_name = "Chess Club"
	activity = app_module.activities[activity_name]
	activity["participants"] = [
		f"student{index}@example.com" for index in range(activity["max_participants"])
	]

	# Act
	response = client.post(
		f"/activities/{activity_name}/signup",
		params={"email": "new-student@example.com"},
	)

	# Assert
	assert response.status_code == 400
	assert response.json() == {"detail": "Activity is full"}


def test_unregister_removes_student_from_activity(client):
	# Arrange
	activity_name = "Chess Club"
	email = app_module.activities[activity_name]["participants"][0]

	# Act
	response = client.delete(
		f"/activities/{activity_name}/signup", params={"email": email}
	)

	# Assert
	assert response.status_code == 200
	assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
	assert email not in app_module.activities[activity_name]["participants"]


def test_unregister_returns_404_for_unknown_activity(client):
	# Arrange
	activity_name = "Unknown Club"

	# Act
	response = client.delete(
		f"/activities/{activity_name}/signup",
		params={"email": "student@example.com"},
	)

	# Assert
	assert response.status_code == 404
	assert response.json() == {"detail": "Activity not found"}


def test_unregister_returns_404_for_unregistered_student(client):
	# Arrange
	activity_name = "Chess Club"
	email = "student@example.com"

	# Act
	response = client.delete(
		f"/activities/{activity_name}/signup", params={"email": email}
	)

	# Assert
	assert response.status_code == 404
	assert response.json() == {"detail": "Student is not signed up for this activity"}
