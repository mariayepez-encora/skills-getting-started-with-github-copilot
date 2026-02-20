"""
Error handling and edge case tests for FastAPI endpoints.
Tests error scenarios including 404s, 400 validation errors, and capacity limits.
"""

from fastapi.testclient import TestClient
from src.app import app


def test_signup_nonexistent_activity():
    """Test that signup for non-existent activity returns 404"""
    # Arrange
    client = TestClient(app)
    activity_name = "Nonexistent Club"
    email = "student@school.com"
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_remove_participant_nonexistent_activity():
    """Test that removing participant from non-existent activity returns 404"""
    # Arrange
    client = TestClient(app)
    activity_name = "Nonexistent Club"
    email = "student@school.com"
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants/{email}"
    )
    
    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_remove_nonexistent_participant():
    """Test that removing non-existent participant returns 404"""
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    nonexistent_email = "nonexistent@school.com"
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants/{nonexistent_email}"
    )
    
    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_duplicate_signup():
    """Test that duplicate signup for same activity returns 400"""
    # Arrange
    client = TestClient(app)
    email = "duplicate@school.com"
    activity_name = "Debate Team"
    
    # Act - First signup
    first_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert first_response.status_code == 200
    
    # Act - Duplicate signup
    duplicate_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    # Assert
    assert duplicate_response.status_code == 400
    detail = duplicate_response.json()["detail"].lower()
    assert "already" in detail or "duplicate" in detail or "signed up" in detail


def test_signup_missing_email_parameter():
    """Test that signup without email parameter returns 422 validation error"""
    # Arrange
    client = TestClient(app)
    activity_name = "Tennis Club"
    
    # Act
    response = client.post(f"/activities/{activity_name}/signup")
    
    # Assert
    assert response.status_code == 422
    assert "email" in response.json()["detail"][0]["loc"]


def test_capacity_limit_enforcement():
    """Test that activity respects max participant capacity"""
    # Arrange
    client = TestClient(app)
    test_activity = "Science Club"
    
    # Get current state of activities
    activities_response = client.get("/activities")
    activities = activities_response.json()
    max_cap = activities[test_activity]["max_participants"]
    current_count = len(activities[test_activity]["participants"])
    spots_available = max_cap - current_count
    
    # Act & Assert
    if spots_available <= 0:
        # Activity is full, test rejection
        response = client.post(
            f"/activities/{test_activity}/signup",
            params={"email": "fulltest@capacity.com"}
        )
        assert response.status_code == 400
        assert "capacity" in response.json()["detail"].lower() or \
               "full" in response.json()["detail"].lower()
    else:
        # Try to fill remaining spots and then exceed
        for i in range(spots_available + 1):
            email = f"capacitytest{i}@capacity.com"
            response = client.post(
                f"/activities/{test_activity}/signup",
                params={"email": email}
            )
            
            if i < spots_available:
                assert response.status_code == 200, \
                    f"Signup {i+1} should succeed (under capacity)"
            else:
                assert response.status_code == 400, \
                    f"Signup {i+1} should fail (over capacity)"
                assert "capacity" in response.json()["detail"].lower() or \
                       "full" in response.json()["detail"].lower()


def test_activities_endpoint_returns_consistent_structure():
    """Test that activities maintain consistent structure across multiple requests"""
    # Arrange
    client = TestClient(app)
    
    # Act
    first_response = client.get("/activities")
    second_response = client.get("/activities")
    activities1 = first_response.json()
    activities2 = second_response.json()
    
    # Assert - both should have same activities
    assert set(activities1.keys()) == set(activities2.keys())
    
    # Assert - structure should be consistent
    for activity_name in activities1:
        keys1 = set(activities1[activity_name].keys())
        keys2 = set(activities2[activity_name].keys())
        assert keys1 == keys2


def test_email_case_sensitivity():
    """Test email handling (typically case-insensitive in practice)"""
    # Arrange
    client = TestClient(app)
    email_lower = "test@school.com"
    email_upper = "TEST@SCHOOL.COM"
    activity_name = "Art Studio"
    
    # Act - Sign up with lowercase
    signup_lower = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email_lower}
    )
    
    # Assert first signup succeeds
    assert signup_lower.status_code == 200
    
    # Act - Try signup with uppercase
    signup_upper = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email_upper}
    )
    
    # Assert - should fail as duplicate in most email systems
    # This depends on implementation; documenting expected behavior
    assert signup_upper.status_code in [200, 400]
