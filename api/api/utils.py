import json
import os
import re
from datetime import datetime
from decimal import Decimal
from typing import Any

import boto3
from botocore.exceptions import ClientError

from errors import ProgrammingError

camel_pattern = re.compile(r'(?<!^)(?=[A-Z])')

s3 = boto3.client('s3')
sns = boto3.client('sns')

monitoring_topic = os.environ['MONITORING_TOPIC']


def camel_to_snake(s: str) -> str:
    return re.sub(camel_pattern, '_', s).lower()


def snake_to_camel(s: str) -> str:
    components = s.split('_')
    # Capitalize the first letter of each component except the first one
    return components[0] + ''.join(x.capitalize() for x in components[1:])


def dash_to_snake(s: str) -> str:
    return s.replace('-', '_')


def custom_serializer(obj):
    match obj:
        case datetime():
            return obj.isoformat()
        case Decimal():
            return int(obj)
        case _:
            raise TypeError("Type not serializable")


def get_presigned_upload_link(
        bucket: str,
        key: str,
        expiration=300,
        fields: dict = None,
        conditions: list = None,
) -> dict:
    """
    Generates a presigned URL S3 POST request to upload a file
    As per
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/generate_presigned_post.html

    :param fields:
    :param conditions:
    :param bucket: AWS bucket to upload to
    :param key: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Dictionary with the following keys:
        url: URL to post to
        fields: Dictionary of form fields and values to submit with the POST
    """

    try:
        return s3.generate_presigned_post(
            bucket,
            key,
            ExpiresIn=expiration,
            Conditions=conditions,
            Fields=fields,

        )
    except ClientError as e:
        raise ProgrammingError(f'{e}')


def delete_from_bucket(bucket: str, key: str) -> dict:
    return s3.delete_object(Bucket=bucket, Key=key)


def send_notification(topic: str, message: Any) -> dict:
    return sns.publish(
        TargetArn=topic,
        Message=json.dumps({'default': json.dumps(message)}),
        MessageStructure='json',
    )


def send_monitoring_notification(message: Any) -> dict:
    return send_notification(monitoring_topic, message)
