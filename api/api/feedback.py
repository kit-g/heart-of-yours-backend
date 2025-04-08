import datetime
import os

from models import User
from utils import get_presigned_upload_link, send_monitoring_notification

media_bucket = os.environ['MEDIA_BUCKET']

min_content_length: int = 128
max_content_length: int = 31_457_280  # 30 MB max


def leave_feedback(*, user: User, message: str) -> dict:
    """
    Builds a pre-signed URL for screenshot upload,
    notifies the monitoring SNS topic
    and returns the URL

    :param user: request user
    :param message: feedback user message
    :return: pre-signed URL
    """
    mime_type = 'image/png'
    key = f'feedback/{user.id}/{datetime.datetime.now().isoformat()}'
    link = get_presigned_upload_link(
        bucket=media_bucket,
        key=key,
        fields={
            'Content-Type': mime_type,
        },
        conditions=[
            ["content-length-range", min_content_length, max_content_length],
            {'Content-Type': mime_type},
        ]
    )
    screenshot_url = f'{link["url"]}/{key}'
    body = {
        'user_id': user.id,
        'email': user.email,
        'username': user.name,
        'message': message,
        'screenshot': screenshot_url,
    }

    send_monitoring_notification(body)
    return link
