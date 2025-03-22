from common import get_raw, exercises


def port():
    for row in get_raw('import.csv'):
        name = row['name']
        r = exercises.document(name).set(row)
        print(f'On {name}: {r}')


if __name__ == '__main__':
    port()
