import datetime
import os

import boto3
import botocore.exceptions
import firebase_admin
from firebase_admin import credentials

from errors import Forbidden
from models import User
from utils import only_self, get_presigned_upload_link

cred = credentials.Certificate('firebase.json')
firebase_admin.initialize_app(cred)

_scheduler = boto3.client('scheduler')

account_deletion_offset = os.environ.get('ACCOUNT_DELETION_OFFSET') or 30
# background_function = os.environ['BACKGROUND_FUNCTION']
background_role = os.environ['BACKGROUND_ROLE']
schedule_group = os.environ['SCHEDULE_GROUP']
upload_bucket = os.environ['UPLOAD_BUCKET']
media_bucket = os.environ['MEDIA_BUCKET']
destination_tag = f"<Tagging><TagSet><Tag><Key>destination</Key><Value>{media_bucket}</Value></Tag></TagSet></Tagging>"

min_content_length: int = 128
max_content_length: int = 31_457_280  # 30 MB max


@only_self
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
    when = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=30)

    schedule_name = f'delete-account-{user.id}'

    # match doc:
    #     case {'scheduledForDeletionAt': when, 'deletionSchedule': schedule} if when and schedule:
    #         # account is already scheduled
    #         raise EmptyResponse
    #     case _:
    #
    #         try:
    #             message = {
    #                 'Event': 'AccountDeletion',
    #                 'Payload': {'user_id': user.id},
    #             }
    #
    #             arn = _scheduler.create_schedule(
    #                 ActionAfterCompletion='DELETE',
    #                 Name=schedule_name,
    #                 GroupName=schedule_group,
    #                 ScheduleExpression=f'at({when.strftime('%Y-%m-%dT%H:%M:%S')})',
    #                 Target={
    #                     'Arn': background_function,
    #                     'RoleArn': background_role,
    #                     'Input': json.dumps(message),
    #                 },
    #                 FlexibleTimeWindow={'Mode': 'OFF'},
    #                 State='ENABLED',
    #             )['ScheduleArn']
    #
    #
    #         except botocore.exceptions.ClientError as error:
    #             # if schedule exists, ok
    #             if error.response['Error']['Code'] != 'ConflictException':
    #                 raise error
    #
    #         raise EmptyResponse


@only_self
def edit_account(*, user: User, account_id: str, action: str, _: dict = None) -> None:  # noqa
    match action:
        case 'undoAccountDeletion':
            return _undo_account_deletion(user.id)


def _undo_account_deletion(user_id: str) -> None:
    """
    Deletes the account deletion schedule for a given user.

    This function retrieves the user document associated with the given user ID
    and checks if an account deletion schedule exists. If an account deletion
    schedule is found, it attempts to delete the schedule from the scheduler.
    Once the schedule is deleted, the corresponding fields in the user document are
    updated to remove any trace of a pending deletion.

    :param user_id: User's Firebase ID
    :return: None
    """
    doc = {}

    match doc:
        case {'scheduledForDeletionAt': _, 'deletionSchedule': schedule} if schedule:
            match f'{schedule}'.split('/'):
                case [_, _, name]:
                    try:
                        _scheduler.delete_schedule(
                            GroupName=schedule_group,
                            Name=name,
                        )
                    except botocore.exceptions.ClientError as error:
                        # if it does not exist, ok
                        if error.response['Error']['Code'] != 'ResourceNotFoundException':
                            raise error


@only_self
def account_info(*, user: User, account_id: str, action: str, mime_type: str = None) -> dict | None:  # noqa
    match action:
        case 'uploadAvatar':
            default_type = 'image/png'
            tag = {"tagging": destination_tag}
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
                    ["content-length-range", min_content_length, max_content_length],
                    {'Content-Type': mime_type or default_type},
                    tag,
                ],
            )
    raise Forbidden(f'Action {action} not allowed')
