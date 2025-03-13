import datetime
import json
import os

import boto3
import botocore.exceptions
from google.cloud.firestore_v1 import DocumentReference
from google.cloud.firestore_v1.transforms import DELETE_FIELD

from models import User
from errors import EmptyResponse, Forbidden

import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('firebase.json')
firebase_admin.initialize_app(cred)

_db = firestore.client()

_scheduler = boto3.client('scheduler')

account_deletion_offset = os.environ.get('ACCOUNT_DELETION_OFFSET') or 30
background_function = os.environ['BACKGROUND_FUNCTION']
background_role = os.environ['BACKGROUND_ROLE']
schedule_group = os.environ['SCHEDULE_GROUP']


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
                                             service errors occur during account
                                             deletion scheduling.
    """
    if user.id != account_id:
        raise Forbidden

    when = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=30)

    schedule_name = f'delete-account-{user.id}'

    doc = _user_doc(user.id)

    match doc:
        case {'scheduledForDeletionAt': when, 'deletionSchedule': schedule} if when and schedule:
            # account is already scheduled
            raise EmptyResponse
        case _:

            try:
                message = {
                    'Event': 'AccountDeletion',
                    'Payload': {'user_id': user.id},
                }

                arn = _scheduler.create_schedule(
                    ActionAfterCompletion='DELETE',
                    Name=schedule_name,
                    GroupName=schedule_group,
                    ScheduleExpression=f'at({when.strftime('%Y-%m-%dT%H:%M:%S')})',
                    Target={
                        'Arn': background_function,
                        'RoleArn': background_role,
                        'Input': json.dumps(message),
                    },
                    FlexibleTimeWindow={'Mode': 'OFF'},
                    State='ENABLED',
                )['ScheduleArn']

                update = {
                    'scheduledForDeletionAt': when.isoformat(),
                    'deletionSchedule': arn,
                }

                _user_ref(user.id).update(update)

            except botocore.exceptions.ClientError as error:
                # if schedule exists, ok
                if error.response['Error']['Code'] != 'ConflictException':
                    raise error

            raise EmptyResponse


def edit_account(*, user: User, account_id: str, action: str, _: dict = None) -> None:
    if user.id != account_id:
        raise Forbidden

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
    doc = _user_doc(user_id)

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

                    doc = {
                        "scheduledForDeletionAt": DELETE_FIELD,
                        "deletionSchedule": DELETE_FIELD,
                    }
                    _user_ref(user_id).update(doc)


def _user_ref(user_id: str) -> DocumentReference:
    return _db.collection('users').document(user_id)


def _user_doc(user_id: str) -> dict:
    return _user_ref(user_id).get().to_dict()
