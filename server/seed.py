from datetime import date, timedelta
from .app import app
from .models import db, Workout, Exercise, WorkoutExercise


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

        strength = Exercise(name="Push-ups", category="Strength", equipment_needed=False)
        cardio = Exercise(name="Running", category="Cardio", equipment_needed=False)
        weights = Exercise(name="Dumbbell Row", category="Strength", equipment_needed=True)

        workout1 = Workout(
            date=date.today(), duration_minutes=35, notes="Full-body session"
        )
        workout2 = Workout(
            date=date.today() - timedelta(days=1),
            duration_minutes=25, notes="Easy cardio day"
        )
        db.session.add_all([strength, cardio, weights, workout1, workout2])
        db.session.flush()

        db.session.add_all([
            WorkoutExercise(workout=workout1, exercise=strength, reps=12, sets=3),
            WorkoutExercise(workout=workout1, exercise=weights, reps=10, sets=3),
            WorkoutExercise(workout=workout2, exercise=cardio, duration_seconds=1200),
        ])
        db.session.commit()
        print("Database seeded successfully.")


if __name__ == "__main__":
    seed()