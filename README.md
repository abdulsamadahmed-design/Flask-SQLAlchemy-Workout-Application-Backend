# Workout Application Backend

A Flask REST API for personal trainers to track workouts and the exercises in them. Built with Flask, Flask-SQLAlchemy, Flask-Migrate and Marshmallow.

## Description

Workouts and exercises are stored in a SQLite database. An exercise can be reused in many workouts, and each workout-exercise link records reps, sets and/or duration. The API validates data at three levels: database constraints, model validations and Marshmallow schemas.

## Installation

Requires Python 3.12 (the pinned Werkzeug 2.2.2 does not run on Python 3.14).

```
pipenv install --dev
pipenv shell
cd server
flask db upgrade head
python seed.py
```

## Running the app

```
cd server
flask run
```

The API is at http://127.0.0.1:5000. Run the tests from the project root with `pytest -v`.

## Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | /workouts | List all workouts |
| GET | /workouts/<id> | One workout, with its exercises and their reps/sets/duration |
| POST | /workouts | Create a workout (`duration_minutes` required, `date` and `notes` optional) |
| DELETE | /workouts/<id> | Delete a workout and its links |
| GET | /exercises | List all exercises |
| GET | /exercises/<id> | One exercise, with its workouts |
| POST | /exercises | Create an exercise (`name` and `category` required) |
| DELETE | /exercises/<id> | Delete an exercise and its links |
| POST | /workouts/<workout_id>/exercises/<exercise_id>/workout_exercises | Add an exercise to a workout (at least one of `reps`, `sets`, `duration_seconds`) |

## Validations

- **Table constraints:** unique exercise names, positive durations, reps and sets, and one link per workout/exercise pair.
- **Model validations:** non-blank names and categories, positive numbers.
- **Schema validations:** length limits, blank-name checks, minimum values, and "at least one of reps, sets or duration".