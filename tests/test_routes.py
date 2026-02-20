"""
Happy path tests for FastAPI endpoints.
Tests successful operations for activities list, signup, deletion, and redirect.
"""

from fastapi.testclient import TestClient
from src.app import app


def test_redirect_root_to_static():
    """Test that GET / redirects to the static index.html"""
    # Arrange
    client = TestClient(app)
    
    # Act
    response = client.get("/", follow_redirects=False)
    
    # Assert
    assert response.status_code == 307
    assert "index.html" in response.headers["location"]


def test_get_all_activities():
    """Test that GET /activities returns all activities with correct structure"""
    # Arrange
    client = TestClient(app)
    expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
    
    # Act
    response = client.get("/activities")
    activities = response.json()
    
    # Assert
    assert response.status_code == 200
    assert isinstance(activities, dict)
    assert len(activities) > 0
    
    # Verify structure of each activity
    for activity_name, activity_data in activities.items():
        assert "description" in activity_data
        assert "schedule" in activity_data
        assert "max_participants" in activity_data
        assert "participants" in activity_data
        assert isinstance(activity_data["participants"], list)
        assert isinstance(activity_data["max_participants"], int)
    
    # Verify some expected activities exist
    for activity in expected_activities:
        assert activity in activities


def test_signup_for_activity():
    """Test successful signup for an activity"""
    # Arrange
    client = TestClient(app)
    email = "student@school.com"
    activity_name = "Art Studio"
    
    # Get initial participant count
    initial_response = client.get("/activities")
    initial_count = len(initial_response.json()[activity_name]["participants"])
    
    # Act
    signup_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    # Assert - check signup response
    assert signup_response.status_code == 200
    result = signup_response.json()
    assert "message" in result
    assert email in result["message"] or "signed up" in result["message"].lower()
    
    # Assert - verify participant was added
    updated_response = client.get("/activities")
    updated_participants = updated_response.json()[activity_name]["participants"]
    assert len(updated_participants) == initial_count + 1
    assert email in updated_participants


def test_remove_participant_from_activity():
    """Test successful removal of participant from activity"""
    # Arrange
    client = TestClient(app)
    email = "student2@school.com"
    activity_name = "Drama Club"
    
    # Setup: sign up first
    client.post(f"/activities/{activity_name}/signup", params={"email": email})
    verify_response = client.get("/activities")
    assert email in verify_response.json()[activity_name]["participants"]
    
    # Act
    delete_response = client.delete(
        f"/activities/{activity_name}/participants/{email}"
    )
    
    # Assert - check delete response
    assert delete_response.status_code == 200
    result = delete_response.json()
    assert "message" in result
    
    # Assert - verify participant was removed
    final_response = client.get("/activities")
    assert email not in final_response.json()[activity_name]["participants"]


def test_multiple_signups_to_same_activity():
    """Test that multiple different students can sign up for the same activity"""
    # Arrange
    client = TestClient(app)
    emails = ["user1@school.com", "user2@school.com", "user3@school.com"]
    activity_name = "Basketball Team"
    
    # Act
    for email in emails:
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        # Assert each signup succeeds
        assert response.status_code == 200
    
    # Assert - verify all are in the activity
    final_response = client.get("/activities")
    participants = final_response.json()[activity_name]["participants"]
    for email in emails:
        assert email in participants
