from datetime import datetime, timedelta, UTC
import json
import os

import boto3
import botocore.exceptions
from dynamo import db

from errors import Forbidden, EmptyResponse
from models import User
from utils import get_presigned_upload_link, delete_from_bucket

scheduler = boto3.client('scheduler')

account_deletion_offset = int(os.environ.get('ACCOUNT_DELETION_OFFSET', 30))
background_function = os.environ['BACKGROUND_FUNCTION']
background_role = os.environ['BACKGROUND_ROLE']
schedule_group = os.environ['SCHEDULE_GROUP']
upload_bucket = os.environ['UPLOAD_BUCKET']
media_bucket = os.environ['MEDIA_BUCKET']
table = os.environ['WORKOUTS_TABLE']
destination_tag = f'<Tagging><TagSet><Tag><Key>destination</Key><Value>{media_bucket}</Value></Tag></TagSet></Tagging>'

min_content_length: int = 128
max_content_length: int = 31_457_280  # 30 MB max


def delete_account(*, user: User, account_id: str) -> None:
    """
    Deletes a user account by scheduling it for deletion. Ensures that the account
    is associated with the provided user ID and avoids unnecessary rescheduling
    if the account has already been scheduled for deletion.

    :param user: The User object for the account owner.
    :param account_id: The unique identifier of the user account to be deleted.
    :return: None

    :raises Forbidden: If the provided user ID does not match the account ID.
    :raises EmptyResponse: If the account is already scheduled for deletion or
                           after scheduling is confirmed as successful.
    :raises botocore.exceptions.ClientError: If AWS Scheduler fails or other
            service errors occur during account deletion scheduling.
    """
    when = datetime.now(UTC) + timedelta(days=account_deletion_offset)
    schedule_name = f'delete-account-{user.id}'

    response = _get_account(user.id)

    item = response.get('Item')
    if not item:
        raise Forbidden("No such account")

    match item:
        case {
            'scheduledForDeletionAt': {'S': delete_at},
            'deletionSchedule': {'S': schedule},
        } if delete_at and schedule:
            raise EmptyResponse
        case _:

            def update():
                db().update_item(
                    TableName=table,
                    Key={
                        'PK': {'S': f'USER#{account_id}'},
                        'SK': {'S': 'ACCOUNT'}
                    },
                    UpdateExpression="SET scheduledForDeletionAt = :when, deletionSchedule = :arn",
                    ExpressionAttributeValues={
                        ':when': {'S': when.isoformat()},
                        ':arn': {'S': arn}
                    }
                )

            try:
                message = {
                    'Event': 'AccountDeletion',
                    'Payload': {'user_id': user.id},
                }

                arn = scheduler.create_schedule(
                    ActionAfterCompletion='DELETE',
                    Name=schedule_name,
                    GroupName=schedule_group,
                    ScheduleExpression=f'at({when.strftime("%Y-%m-%dT%H:%M:%S")})',
                    Target={
                        'Arn': background_function,
                        'RoleArn': background_role,
                        'Input': json.dumps(message),
                    },
                    FlexibleTimeWindow={'Mode': 'OFF'},
                    State='ENABLED',
                )['ScheduleArn']

                update()

            except botocore.exceptions.ClientError as error:
                # if schedule exists, ok
                if error.response['Error']['Code'] != 'ConflictException':
                    raise error

    raise EmptyResponse


def edit_account(*, user: User, account_id: str, action: str, _: dict = None) -> dict | None:  # noqa
    match action:
        case 'undoAccountDeletion':
            return _undo_account_deletion(user.id)
        case 'removeAvatar':
            return _remove_avatar(account_id)
    return None


def _undo_account_deletion(user_id: str) -> None:
    """
    Deletes the account deletion schedule for a given user.

    This function retrieves the user document associated with the given user ID
    and checks if an account deletion schedule exists. If an account deletion
    schedule is found, it attempts to delete the schedule from the scheduler.
    Once the schedule is deleted, the corresponding fields in the user item are
    updated to remove any trace of a pending deletion.

    :param user_id: User's Firebase ID
    :return: None
    """
    item = _get_account(user_id).get('Item')

    if not item:
        raise Forbidden('No such account found')

    match item:
        case {
            'scheduledForDeletionAt': {'S': delete_at},
            'deletionSchedule': {'S': schedule},
        } if delete_at and schedule:
            match f'{schedule}'.split('/'):
                case [_, _, name]:
                    try:
                        scheduler.delete_schedule(
                            GroupName=schedule_group,
                            Name=name,
                        )
                    except botocore.exceptions.ClientError as error:
                        # if it does not exist, ok
                        if error.response['Error']['Code'] != 'ResourceNotFoundException':
                            raise error

            db().update_item(
                TableName=table,
                Key={
                    'PK': {'S': f'USER#{user_id}'},
                    'SK': {'S': 'ACCOUNT'}
                },
                UpdateExpression="REMOVE scheduledForDeletionAt, deletionSchedule"
            )


def _remove_avatar(account_id: str) -> dict:
    return delete_from_bucket(bucket=media_bucket, key=f'avatars/{account_id}')


def account_info(*, user: User, account_id: str, action: str, mime_type: str = None) -> dict | None:  # noqa
    match action:
        case 'uploadAvatar':
            default_type = 'image/png'
            tag = {'tagging': destination_tag}
            return get_presigned_upload_link(
                bucket=upload_bucket,
                key=f'avatars/{user.id}',
                fields={
                    # this will be returned by CloudFront with no changes
                    'Content-Type': mime_type or default_type,
                    # this will point at destination bucket, processing lambda will save there
                    **tag,
                },
                conditions=[
                    ['content-length-range', min_content_length, max_content_length],
                    {'Content-Type': mime_type or default_type},
                    tag,
                ],
            )
    raise Forbidden(f'Action {action} not allowed')


def _get_account(account_id: str) -> dict:
    """
    Fetches account item from Dynamo
    :param account_id: user's Firebase id
    :return: DynamoDB get_item response
    """
    return db().get_item(
        TableName=table,
        Key={
            'PK': {'S': f'USER#{account_id}'},
            'SK': {'S': 'ACCOUNT'}
        }
    )
