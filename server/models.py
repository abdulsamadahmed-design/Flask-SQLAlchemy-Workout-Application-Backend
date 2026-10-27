from datetime import date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.orm import validates

db = SQLAlchemy()


class Workout(db.Model):
    __tablename__ = "workouts"
    __table_args__ = (
        CheckConstraint("duration_minutes > 0", name="ck_workout_duration_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    duration_minutes = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    workout_exercises = db.relationship(
        "WorkoutExercise", back_populates="workout",
        cascade="all, delete-orphan", passive_deletes=True
    )
    exercises = db.relationship(
        "Exercise", secondary="workout_exercises", viewonly=True
    )

    @validates("duration_minutes")
    def validate_duration(self, key, value):
        if not isinstance(value, int) or value <= 0:
            raise ValueError("duration_minutes must be a positive integer.")
        return value


class Exercise(db.Model):
    __tablename__ = "exercises"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    category = db.Column(db.String(60), nullable=False)
    equipment_needed = db.Column(db.Boolean, nullable=False, default=False)

    workout_exercises = db.relationship(
        "WorkoutExercise", back_populates="exercise",
        cascade="all, delete-orphan", passive_deletes=True
    )
    workouts = db.relationship(
        "Workout", secondary="workout_exercises", viewonly=True
    )

    @validates("name", "category")
    def validate_required_text(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a non-empty string.")
        return value.strip()


class WorkoutExercise(db.Model):
    __tablename__ = "workout_exercises"
    __table_args__ = (
        UniqueConstraint("workout_id", "exercise_id", name="uq_workout_exercise_pair"),
        CheckConstraint("reps IS NULL OR reps > 0", name="ck_workout_exercise_reps_positive"),
        CheckConstraint("sets IS NULL OR sets > 0", name="ck_workout_exercise_sets_positive"),
        CheckConstraint("duration_seconds IS NULL OR duration_seconds > 0",
                        name="ck_workout_exercise_duration_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(
        db.Integer, db.ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False
    )
    exercise_id = db.Column(
        db.Integer, db.ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False
    )
    reps = db.Column(db.Integer, nullable=True)
    sets = db.Column(db.Integer, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)

    workout = db.relationship("Workout", back_populates="workout_exercises")
    exercise = db.relationship("Exercise", back_populates="workout_exercises")

    @validates("reps", "sets", "duration_seconds")
    def validate_positive_optional_numbers(self, key, value):
        if value is not None and (not isinstance(value, int) or value <= 0):
            raise ValueError(f"{key} must be a positive integer when provided.")
        return value
    