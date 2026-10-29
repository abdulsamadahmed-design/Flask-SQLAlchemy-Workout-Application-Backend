import os
import sqlite3
from datetime import date

from flask import Flask, jsonify, request
from flask_migrate import Migrate
from marshmallow import ValidationError
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from models import *
from schema import (
    ExerciseSchema, WorkoutSchema, WorkoutExerciseSchema, WorkoutExerciseCreateSchema
)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

migrate = Migrate(app, db)
db.init_app(app)

workout_schema = WorkoutSchema(exclude=("workout_exercises",))
workouts_schema = WorkoutSchema(many=True, only=("id", "date", "duration_minutes", "notes"))
exercise_schema = ExerciseSchema()
exercises_schema = ExerciseSchema(many=True, exclude=("workouts",))
link_schema = WorkoutExerciseSchema()
link_create_schema = WorkoutExerciseCreateSchema()


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    # SQLite ignores foreign keys (and ON DELETE CASCADE) unless this is switched on
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@app.errorhandler(ValidationError)
def handle_validation_error(err):
    return jsonify({"errors": err.messages}), 400


def error(message, status):
    return jsonify({"error": message}), status


def get_json_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


@app.get("/workouts")
def get_workouts():
    workouts = Workout.query.order_by(Workout.id).all()
    return jsonify(workouts_schema.dump(workouts)), 200


@app.get("/workouts/<int:workout_id>")
def get_workout(workout_id):
    workout = db.session.get(Workout, workout_id)
    if workout is None:
        return error("Workout not found", 404)
    return jsonify(workout_schema.dump(workout)), 200


@app.post("/workouts")
def create_workout():
    data = get_json_body()
    if data is None:
        return error("Request body must be a JSON object", 400)
    clean = workout_schema.load(data)
    try:
        workout = Workout(
            date=clean.get("date", date.today()),
            duration_minutes=clean["duration_minutes"],
            notes=clean.get("notes"),
        )
        db.session.add(workout)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return error(str(exc), 400)
    return jsonify(workout_schema.dump(workout)), 201


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
    return jsonify(exercises_schema.dump(exercises)), 200


@app.get("/exercises/<int:exercise_id>")
def get_exercise(exercise_id):
    exercise = db.session.get(Exercise, exercise_id)
    if exercise is None:
        return error("Exercise not found", 404)
    return jsonify(exercise_schema.dump(exercise)), 200


@app.post("/exercises")
def create_exercise():
    data = get_json_body()
    if data is None:
        return error("Request body must be a JSON object", 400)
    clean = exercise_schema.load(data)
    try:
        exercise = Exercise(**clean)
        db.session.add(exercise)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("An exercise with that name already exists", 409)
    except ValueError as exc:
        db.session.rollback()
        return error(str(exc), 400)
    return jsonify(exercise_schema.dump(exercise)), 201


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
    clean = link_create_schema.load(data)
    try:
        link = WorkoutExercise(workout=workout, exercise=exercise, **clean)
        db.session.add(link)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("That exercise is already in this workout", 409)
    except ValueError as exc:
        db.session.rollback()
        return error(str(exc), 400)
    return jsonify(link_schema.dump(link)), 201


if __name__ == '__main__':
    app.run(port=5555, debug=True)
    