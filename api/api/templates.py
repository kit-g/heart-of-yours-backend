import os

from models import User, Template

_table = os.environ['WORKOUTS_TABLE']


def save_template(*, user: User, **body) -> tuple[dict | None, int]:
    template = Template.from_dict(body, user_id=user.id)
    template.save_as_non_null_item(table=_table)
    return None, 201
