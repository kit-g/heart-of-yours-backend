from common import get_raw
from api.api.models import Exercise


def port():
    for row in get_raw('import.csv'):
        exercise = Exercise(
            name=row['name'],
            target=row['target'],
            category=row['category'],
        )
        r = exercise.save_as_non_null_item(table='workouts')
        print(f'On {row['name']}: {r}')


if __name__ == '__main__':
    port()
