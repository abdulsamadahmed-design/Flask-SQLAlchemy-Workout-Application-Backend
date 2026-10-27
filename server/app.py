import os
import sqlite3
from datetime import date

from flask import Flask, jsonify, request
from flask_migrate import Migrate
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from models import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

migrate = Migrate(app, db)

db.init_app(app)


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def error(message, status):
    return jsonify({"error": message}), status


def get_json_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def exercise_to_dict(exercise):
    return {
        "id": exercise.id,
        "name": exercise.name,
        "category": exercise.category,
        "equipment_needed": exercise.equipment_needed,
    }


def workout_to_dict(workout):
    return {
        "id": workout.id,
        "date": workout.date.isoformat(),
        "duration_minutes": workout.duration_minutes,
        "notes": workout.notes,
    }


def link_to_dict(link):
    return {
        "id": link.id,
        "workout_id": link.workout_id,
        "exercise_id": link.exercise_id,
        "reps": link.reps,
        "sets": link.sets,
        "duration_seconds": link.duration_seconds,
    }


@app.get("/workouts")
def get_workouts():
    workouts = Workout.query.order_by(Workout.id).all()
    return jsonify([workout_to_dict(w) for w in workouts]), 200


@app.get("/workouts/<int:workout_id>")
def get_workout(workout_id):
    workout = db.session.get(Workout, workout_id)
    if workout is None:
        return error("Workout not found", 404)
    result = workout_to_dict(workout)
    result["exercises"] = [
        {**exercise_to_dict(link.exercise),
         "reps": link.reps, "sets": link.sets,
         "duration_seconds": link.duration_seconds}
        for link in workout.workout_exercises
    ]
    return jsonify(result), 200


@app.post("/workouts")
def create_workout():
    data = get_json_body()
    if data is None:
        return error("Request body must be a JSON object", 400)
    if "duration_minutes" not in data:
        return error("duration_minutes is required", 400)
    try:
        workout_date = date.fromisoformat(data["date"]) if "date" in data else date.today()
        workout = Workout(
            date=workout_date,
            duration_minutes=data["duration_minutes"],
            notes=data.get("notes"),
        )
        db.session.add(workout)
        db.session.commit()
    except (ValueError, TypeError) as exc:
        db.session.rollback()
        return error(str(exc), 400)
    return jsonify(workout_to_dict(workout)), 201


@app.delete("/workouts/<int:workout_id>")
def delete_workout(workout_id):
    workout = db.session.get(Workout, workout_id)
    if workout is None:
        return error("Workout not found", 404)
    db.session.delete(workout)
    db.session.commit()
    return "", 204


@app.get("/exercises")
def get_exercises():
    exercises = Exercise.query.order_by(Exercise.id).all()
    return jsonify([exercise_to_dict(e) for e in exercises]), 200


@app.get("/exercises/<int:exercise_id>")
def get_exercise(exercise_id):
    exercise = db.session.get(Exercise, exercise_id)
    if exercise is None:
        return error("Exercise not found", 404)
    result = exercise_to_dict(exercise)
    result["workouts"] = [workout_to_dict(w) for w in exercise.workouts]
    return jsonify(result), 200


@app.post("/exercises")
def create_exercise():
    data = get_json_body()
    if data is None:
        return error("Request body must be a JSON object", 400)
    try:
        exercise = Exercise(
            name=data.get("name"),
            category=data.get("category"),
            equipment_needed=data.get("equipment_needed", False),
        )
        db.session.add(exercise)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("An exercise with that name already exists", 409)
    except (ValueError, TypeError) as exc:
        db.session.rollback()
        return error(str(exc), 400)
    return jsonify(exercise_to_dict(exercise)), 201


@app.delete("/exercises/<int:exercise_id>")
def delete_exercise(exercise_id):
    exercise = db.session.get(Exercise, exercise_id)
    if exercise is None:
        return error("Exercise not found", 404)
    db.session.delete(exercise)
    db.session.commit()
    return "", 204


@app.post("/workouts/<int:workout_id>/exercises/<int:exercise_id>/workout_exercises")
def add_exercise_to_workout(workout_id, exercise_id):
    workout = db.session.get(Workout, workout_id)
    if workout is None:
        return error("Workout not found", 404)
    exercise = db.session.get(Exercise, exercise_id)
    if exercise is None:
        return error("Exercise not found", 404)
    data = get_json_body()
    if data is None:
        return error("Request body must be a JSON object", 400)
    try:
        link = WorkoutExercise(
            workout=workout,
            exercise=exercise,
            reps=data.get("reps"),
            sets=data.get("sets"),
            duration_seconds=data.get("duration_seconds"),
        )
        db.session.add(link)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("That exercise is already in this workout", 409)
    except (ValueError, TypeError) as exc:
        db.session.rollback()
        return error(str(exc), 400)
    return jsonify(link_to_dict(link)), 201


if __name__ == '__main__':
    app.run(port=5555, debug=True)
