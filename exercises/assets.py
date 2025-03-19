import os
from typing import Callable, Any
from urllib.parse import quote_plus

import boto3
import mimetypes
from PIL import Image
import io

from firebase_admin import credentials, initialize_app, firestore

_bucket = "583168578067-exercise-assets"
_assets = "assets"

_s3 = boto3.client("s3")

cred = credentials.Certificate('../api/background/firebase.json')
initialize_app(cred)
db = firestore.client()

distribution = os.environ['DISTRIBUTION']


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


def link(exercise: str, file: str) -> str:
    return f'https://{distribution}/exercises/{quote_plus(exercise)}/{file}'


@logs
def upload(*, file_path: str, file_name: str, content_type: str) -> None:
    return _s3.upload_file(
        file_path,
        _bucket,
        f'exercises/{file_name}',
        ExtraArgs={"ContentType": content_type}
    )


@logs
def extract_thumbnail(file_path: str, thumbnail_size=(200, 200)):
    """
    Extract the first frame of a GIF as a thumbnail
    Returns the thumbnail as a file object
    """
    # open the gif file
    with Image.open(file_path) as img:
        # get first frame
        img.seek(0)
        # convert to rgb (in case of transparency)
        rgb_img = img.convert('RGB')
        # resize for thumbnail
        rgb_img.thumbnail(thumbnail_size)

        # create a temp file-like object in memory
        thumbnail_io = io.BytesIO()
        # save as jpeg with good quality
        rgb_img.save(thumbnail_io, 'JPEG', quality=85)
        thumbnail_io.seek(0)
        return thumbnail_io


@logs
def update(exercise: str):
    doc = {
        'thumbnail': link(exercise, 'thumbnail.jpg'),
        'asset': link(exercise, 'asset.gif'),
    }
    return db.collection('exercises').document(exercise).update(doc)


def upload_files():
    for file_name in os.listdir(_assets):
        file_path = os.path.join(_assets, file_name)

        if not os.path.isfile(file_path):
            continue

        content_type, _ = mimetypes.guess_type(file_path)

        if content_type != 'image/gif':
            print(f"Skipping {file_name} - not a GIF file")
            continue

        exercise = os.path.splitext(file_name)[0]

        asset_path = f"{exercise}/asset.gif"
        thumbnail_path = f"{exercise}/thumbnail.jpg"

        upload(
            file_path=file_path,
            file_name=asset_path,
            content_type='image/gif',
        )
        print(f"Uploaded {file_name} to {asset_path}")

        if thumbnail := extract_thumbnail(file_path):
            temp = os.path.join(_assets, f"temp_thumbnail_{exercise}.jpg")
            with open(temp, 'wb') as f:
                f.write(thumbnail.getvalue())

            upload(
                file_path=temp,
                file_name=thumbnail_path,
                content_type='image/jpeg'
            )
            print(f"Uploaded thumbnail to {thumbnail_path}")

            os.remove(temp)

        update(exercise)


if __name__ == "__main__":
    upload_files()
