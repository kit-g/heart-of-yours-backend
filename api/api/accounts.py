import datetime
import json
import os

import boto3
import botocore.exceptions

from models import User
from errors import EmptyResponse, Forbidden

import firebase_admin
from firebase_admin import credentials

from firebase_admin import firestore

cred = credentials.Certificate('firebase.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

scheduler = boto3.client('scheduler')

account_deletion_offset = os.environ.get('ACCOUNT_DELETION_OFFSET') or 30
background_function = os.environ['BACKGROUND_FUNCTION']
background_role = os.environ['BACKGROUND_ROLE']
schedule_group = os.environ['SCHEDULE_GROUP']


def delete_account(*, user: User, account_id: str, password) -> None:
    if user.id != account_id:
        raise Forbidden

    when = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=30)

    schedule_name = f'delete-account-{user.id}'

    snapshot = db.collection('users').document(user.id).get()

    match snapshot.to_dict():
        case {'scheduledForDeletionAt': _, 'deletionSchedule': _}:  # account is already scheduled
            raise EmptyResponse
        case _:

            arn = None

            try:
                message = {
                    'Event': 'AccountDeletion',
                    'Payload': {'user_id': user.id},
                }

                arn = scheduler.create_schedule(
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

            except botocore.exceptions.ClientError as error:
                # if schedule exists, ok
                if error.response['Error']['Code'] != 'ConflictException':
                    raise error

                update = {
                    'scheduledForDeletionAt': when.isoformat(),
                    'deletionSchedule': arn
                }

                db.collection('users').document(user.id).update(update)
            raise EmptyResponse
