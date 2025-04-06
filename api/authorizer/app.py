import json
import os
from dataclasses import dataclass, asdict
from typing import Literal

import firebase_admin
from firebase_admin import auth, credentials

cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)

Effect = Literal['Allow', 'Deny']
region = os.environ['AWS_REGION']


@dataclass
class User:
    id: str
    name: str
    email: str
    verified: bool

    @classmethod
    def from_dict(cls, d: dict) -> 'User':
        return cls(
            id=d['uid'],
            name=d['name'],
            email=d['email'],
            verified=d['email_verified'],
        )

    def to_dict(self):
        return asdict(self)  # noqa


def generate_policy(effect: Effect, resource: str, user: User = None) -> dict:
    policy = {
        "principalId": user.id if user else 'user',
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": resource
                },
            ]
        },
    }

    if user:
        policy['context'] = {
            'user': json.dumps(user.to_dict()),
        }
    return policy


def handler(event, _):
    print(event)

    match event:
        case {
            'headers': {'Authorization': header},
            'requestContext': {
                'stage': stage,
                'accountId': account,
                'apiId': api_id,
            },
            'pathParameters': path_params,
        }:
            resource = f"arn:aws:execute-api:{region}:{account}:{api_id}/{stage}/*"

            match header.split(' '):
                case ['Bearer', token]:
                    try:
                        decoded = auth.verify_id_token(token)
                        user = User.from_dict(decoded)

                        match path_params:
                            # this will be the general convention:
                            # if the path contains {accountId},
                            # the endpoint will only allow the action to that user
                            case {'accountId': account_id}:
                                if account_id == user.id:
                                    return generate_policy("Allow", resource, user=user)
                                return generate_policy("Deny", resource)
                            case _:
                                return generate_policy("Allow", resource, user=user)
                    except Exception as e:
                        print(f"Token verification failed: {e}")
                        return generate_policy("Deny", resource)
