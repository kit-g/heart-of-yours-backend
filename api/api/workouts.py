import os

from models import User, Workout

_table = os.environ['WORKOUTS_TABLE']


def save_workout(*, user: User, **body) -> tuple[dict | None, int]:
    workout = Workout.from_dict(body, user_id=user.id)
    workout.save_as_non_null_item(table=_table)
    return None, 201
