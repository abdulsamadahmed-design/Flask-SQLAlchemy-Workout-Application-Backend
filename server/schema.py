from marshmallow import Schema, fields, validate, validates_schema, ValidationError

def not_blank(value):
    if not value.strip():
        raise ValidationError("Must not be blank.")


class ExerciseSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=[validate.Length(min=1, max=100), not_blank])
    category = fields.Str(required=True, validate=[validate.Length(min=1, max=60), not_blank])
    equipment_needed = fields.Bool(load_default=False)
    workouts = fields.Method("get_workouts", dump_only=True)

    def get_workouts(self, obj):
        return [{"id": workout.id, "date": workout.date.isoformat()}
                for workout in obj.workouts]


class WorkoutExerciseSchema(Schema):
    id = fields.Int(dump_only=True)
    workout_id = fields.Int(dump_only=True)
    exercise_id = fields.Int(dump_only=True)
    reps = fields.Int(allow_none=True, load_default=None, validate=validate.Range(min=1))
    sets = fields.Int(allow_none=True, load_default=None, validate=validate.Range(min=1))
    duration_seconds = fields.Int(allow_none=True, load_default=None,
                                  validate=validate.Range(min=1))
    exercise = fields.Nested(ExerciseSchema(only=("id", "name", "category")), dump_only=True)


class WorkoutSchema(Schema):
    id = fields.Int(dump_only=True)
    date = fields.Date(required=False)
    duration_minutes = fields.Int(required=True, validate=validate.Range(min=1))
    notes = fields.Str(allow_none=True, load_default=None)
    workout_exercises = fields.Nested(WorkoutExerciseSchema(many=True), dump_only=True)
    exercises = fields.Method("get_exercises", dump_only=True)

    def get_exercises(self, obj):
        return [{
            "id": link.exercise.id,
            "name": link.exercise.name,
            "category": link.exercise.category,
            "equipment_needed": link.exercise.equipment_needed,
            "reps": link.reps,
            "sets": link.sets,
            "duration_seconds": link.duration_seconds,
        } for link in obj.workout_exercises]


class WorkoutExerciseCreateSchema(Schema):
    reps = fields.Int(allow_none=True, load_default=None, validate=validate.Range(min=1))
    sets = fields.Int(allow_none=True, load_default=None, validate=validate.Range(min=1))
    duration_seconds = fields.Int(allow_none=True, load_default=None,
                                  validate=validate.Range(min=1))

    @validates_schema
    def require_training_measure(self, data, **kwargs):
        if not any(data.get(key) is not None for key in
                   ("reps", "sets", "duration_seconds")):
            raise ValidationError(
                "Provide at least one of reps, sets, or duration_seconds."
            )
        