import os
from urllib.parse import quote_plus

import boto3
import mimetypes
from PIL import Image
import io

from common import logs

_assets = "assets"

_s3 = boto3.client("s3")
_dynamo = boto3.client("dynamodb")

distribution = os.environ['DISTRIBUTION']
_bucket = os.environ['BUCKET']
table = os.environ['WORKOUTS_TABLE']


def link(exercise: str, file: str) -> str:
    return f'https://{distribution}/exercises/{quote_plus(exercise)}/{file}'


@logs
def dimensions(file_path: str) -> tuple[int, int]:
    with Image.open(file_path) as img:
        return img.size


@logs
def upload(*, file_path: str, file_name: str, content_type: str) -> None:
    return _s3.upload_file(
        file_path,
        _bucket,
        f'exercises/{file_name}',
        ExtraArgs={
            "ContentType": content_type,
            'CacheControl': 'public, max-age=31536000, immutable',
        }
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
def update(exercise: str, doc: dict):
    """Generated"""
    update_expr = "SET "
    expr_attr_values = {}
    expr_attr_names = {}
    sets = []

    for key, value in doc.items():
        placeholder = f"#{key}"
        value_placeholder = f":{key}"
        sets.append(f"{placeholder} = {value_placeholder}")
        expr_attr_names[placeholder] = key
        expr_attr_values[value_placeholder] = {
            'M': {
                'link': {'S': value['link']},
                'width': {'N': str(value['width'])},
                'height': {'N': str(value['height'])},
            }
        }

    update_expr += ", ".join(sets)

    return _dynamo.update_item(
        TableName=table,
        Key={
            'PK': {'S': 'EXERCISE'},
            'SK': {'S': exercise},
        },
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_attr_names,
        ExpressionAttributeValues=expr_attr_values,
    )


def upload_files():
    for file_name in os.listdir(_assets):
        file_path = os.path.join(_assets, file_name)

        if not os.path.isfile(file_path):
            continue

        content_type, _ = mimetypes.guess_type(file_path)

        if not content_type or not content_type.startswith('image/'):
            print(f"Skipping {file_name} - not an image file")
            continue

        exercise, extension = os.path.splitext(file_name)

        asset_path = f"{exercise}/asset.gif"
        thumbnail_path = f"{exercise}/thumbnail.jpg"

        width, height = dimensions(file_path)

        upload(
            file_path=file_path,
            file_name=asset_path,
            content_type=content_type,
        )
        print(f"Uploaded {file_name} to {asset_path}")

        doc = {
            'asset': {
                'link': link(exercise, 'asset.gif'),
                'width': width,
                'height': height,
            },
        }

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

            t_width, t_height = dimensions(temp)

            doc['thumbnail'] = {
                'link': link(exercise, 'thumbnail.jpg'),
                'width': t_width,
                'height': t_height,
            }
            os.remove(temp)

        update(exercise, doc)


if __name__ == "__main__":
    upload_files()
