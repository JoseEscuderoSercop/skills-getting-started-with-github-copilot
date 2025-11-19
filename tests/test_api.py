"""
Tests for the Mergington High School API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_root_redirect(client):
    """Test that root redirects to static/index.html."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities."""
    response = client.get("/activities")
    assert response.status_code == 200
    
    activities = response.json()
    assert isinstance(activities, dict)
    assert len(activities) == 9
    assert "Chess Club" in activities
    assert "Programming Class" in activities
    
    # Verify structure of an activity
    chess_club = activities["Chess Club"]
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    assert chess_club["max_participants"] == 12
    assert "michael@mergington.edu" in chess_club["participants"]


def test_signup_for_activity_success(client):
    """Test successful signup for an activity."""
    email = "newstudent@mergington.edu"
    activity = "Chess Club"
    
    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 200
    
    result = response.json()
    assert result["message"] == f"Signed up {email} for {activity}"
    
    # Verify the participant was added
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email in activities[activity]["participants"]


def test_signup_duplicate_participant(client):
    """Test that duplicate signup is rejected."""
    email = "michael@mergington.edu"  # Already registered
    activity = "Chess Club"
    
    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_signup_nonexistent_activity(client):
    """Test signup for non-existent activity."""
    email = "student@mergington.edu"
    activity = "Nonexistent Activity"
    
    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_unregister_participant_success(client):
    """Test successful unregistration of a participant."""
    email = "michael@mergington.edu"
    activity = "Chess Club"
    
    # Verify participant is registered initially
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email in activities[activity]["participants"]
    
    # Unregister the participant
    response = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert response.status_code == 200
    
    result = response.json()
    assert result["message"] == f"Unregistered {email} from {activity}"
    
    # Verify the participant was removed
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email not in activities[activity]["participants"]


def test_unregister_not_registered_participant(client):
    """Test unregistering a participant who is not registered."""
    email = "notregistered@mergington.edu"
    activity = "Chess Club"
    
    response = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert response.status_code == 400
    assert "not registered" in response.json()["detail"]


def test_unregister_from_nonexistent_activity(client):
    """Test unregistering from non-existent activity."""
    email = "student@mergington.edu"
    activity = "Nonexistent Activity"
    
    response = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_signup_and_unregister_flow(client):
    """Test complete flow of signing up and unregistering."""
    email = "testuser@mergington.edu"
    activity = "Swimming Club"
    
    # Get initial participant count
    activities_response = client.get("/activities")
    initial_count = len(activities_response.json()[activity]["participants"])
    
    # Sign up
    signup_response = client.post(f"/activities/{activity}/signup?email={email}")
    assert signup_response.status_code == 200
    
    # Verify participant was added
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email in activities[activity]["participants"]
    assert len(activities[activity]["participants"]) == initial_count + 1
    
    # Unregister
    unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert unregister_response.status_code == 200
    
    # Verify participant was removed
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email not in activities[activity]["participants"]
    assert len(activities[activity]["participants"]) == initial_count


def test_multiple_participants_signup(client):
    """Test multiple participants signing up for the same activity."""
    activity = "Drama Club"
    emails = [
        "student1@mergington.edu",
        "student2@mergington.edu",
        "student3@mergington.edu"
    ]
    
    for email in emails:
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
    
    # Verify all were added
    activities_response = client.get("/activities")
    activities = activities_response.json()
    for email in emails:
        assert email in activities[activity]["participants"]


def test_activity_capacity_tracking(client):
    """Test that participant count is correctly tracked."""
    activity = "Art Studio"
    
    activities_response = client.get("/activities")
    activities = activities_response.json()
    
    initial_count = len(activities[activity]["participants"])
    max_participants = activities[activity]["max_participants"]
    
    assert initial_count <= max_participants
    assert initial_count == 2  # emily and mia initially


def test_url_encoded_activity_names(client):
    """Test that activity names with spaces are properly handled."""
    email = "test@mergington.edu"
    activity = "Chess Club"
    
    # URL encode the activity name
    import urllib.parse
    encoded_activity = urllib.parse.quote(activity)
    
    response = client.post(f"/activities/{encoded_activity}/signup?email={email}")
    assert response.status_code == 200


def test_url_encoded_email(client):
    """Test that emails with special characters are properly handled."""
    email = "test+tag@mergington.edu"
    activity = "Gym Class"
    
    import urllib.parse
    encoded_email = urllib.parse.quote(email)
    
    response = client.post(f"/activities/{activity}/signup?email={encoded_email}")
    assert response.status_code == 200
    
    # Verify with proper encoding
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email in activities[activity]["participants"]
