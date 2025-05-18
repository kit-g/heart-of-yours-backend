import json
import os
from datetime import datetime, timezone

import boto3
from dynamo import db

table = os.environ['WORKOUTS_TABLE']
avatar_bucket = os.environ['MEDIA_BUCKET']
auth_function = os.environ['AUTH_FUNCTION']

s3 = boto3.client('s3')
lambda_ = boto3.client('lambda')


def delete_account(user_id: str):
    delete_avatar(user_id)
    print(f'Deleted avatar from {avatar_bucket}')

    delete_from_table(user_id)
    print(f'Deleted account from {table}')


def delete_from_table(account_id: str) -> dict:
    db().delete_item(
        TableName=table,
        Key={
            'PK': {'S': f'USER#{account_id}'},
            'SK': {'S': 'ACCOUNT'}
        },
    )

    return db().update_item(
        TableName=table,
        Key={
            'PK': {'S': f'USER#{account_id}'},
            'SK': {'S': 'ACCOUNT'}
        },
        UpdateExpression='SET #ts = :deletedAt',
        ExpressionAttributeNames={
            '#ts': 'deletedAt',
        },
        ExpressionAttributeValues={
            ':deletedAt': {'S': datetime.now(timezone.utc).isoformat()},
        },
    )


def delete_avatar(account_id: str) -> dict:
    return s3.delete_object(
        Bucket=avatar_bucket,
        Key=f'avatars/{account_id}',
    )


def call_lambda(function_name: str, event: dict) -> dict | None:
    try:
        body = json.dumps(event).encode('utf-8')
        response = lambda_.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=body,
        )

        payload = response['Payload'].read()
        return json.loads(payload.decode('utf-8'))
    except json.JSONDecodeError as error:
        if error.pos == 0:
            return {}
        raise
    except Exception:
        raise


def handler(event: dict, context) -> dict:
    print(event)

    match event:
        case {
            'Event': 'AccountDeletion',
            'Payload': {'user_id': user_id},
        }:
            delete_account(user_id)
            r = call_lambda(auth_function, event)
            print(f'On deleting {user_id} from Firebase Auth: {r}')
    try:
        return {'statusCode': 200}
    except Exception as e:
        print(f'{context.function_name}: {type(e)} - {e}')
        raise e
