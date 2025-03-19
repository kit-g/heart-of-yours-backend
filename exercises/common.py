import csv
import json
from typing import Generator, Callable, Any

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate('firebase.json')

app = firebase_admin.initialize_app(cred)

db = firestore.client()
exercises = db.collection('exercises')
templates = db.collection('templates')


def get_raw(filepath: str) -> Generator[dict, None, None]:
    with open(filepath) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            yield row


def get_json(filepath: str) -> dict:
    with open(filepath) as source:
        return json.load(source)


def logs(func: Callable) -> Any:
    """
    Decorator to wrap a function in try-except for error handling and logging exceptions.

    :param func: The target function to decorate.
    :return: A wrapped function that handles exceptions and logs errors.
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error in {func.__name__}: {type(e)} - {e}, args: {args}, kwargs {kwargs}")
            return None

    return wrapper
