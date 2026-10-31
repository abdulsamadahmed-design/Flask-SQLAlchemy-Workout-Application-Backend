import pytest
from app import app
from models import db


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.app_context():
        assert "test.db" in str(db.engine.url), "Refusing to wipe a non-test database"
        db.drop_all()
        db.create_all()
    with app.test_client() as test_client:
        yield test_client
    with app.app_context():
        db.session.remove()
        db.drop_all()

def test_create_and_list_exercise(client):
    response = client.post("/exercises", json={
        "name": "Squats", "category": "Strength", "equipment_needed": False
    })
    assert response.status_code == 201
    assert response.json["name"] == "Squats"
    listing = client.get("/exercises")
    assert listing.status_code == 200
    assert len(listing.json) == 1


def test_schema_rejects_invalid_workout_duration(client):
    response = client.post("/workouts", json={"duration_minutes": 0})
    assert response.status_code == 400


def test_not_found_workout(client):
    response = client.get("/workouts/999")
    assert response.status_code == 404

def test_blank_exercise_name_rejected(client):
    response = client.post("/exercises", json={"name": "   ", "category": "Core"})
    assert response.status_code == 400


def test_link_requires_a_measure(client):
    client.post("/workouts", json={"duration_minutes": 30})
    client.post("/exercises", json={"name": "Squats", "category": "Strength"})
    response = client.post("/workouts/1/exercises/1/workout_exercises", json={})
    assert response.status_code == 400


def test_delete_workout_removes_its_links(client):
    client.post("/workouts", json={"duration_minutes": 30})
    client.post("/exercises", json={"name": "Squats", "category": "Strength"})
    client.post("/workouts/1/exercises/1/workout_exercises", json={"reps": 10})
    assert client.delete("/workouts/1").status_code == 204
    assert client.get("/exercises/1").json["workouts"] == []
    