import json
import re

from utils import camel_to_snake
from errors import Unauthorized

_cors = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Credentials": True,
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "*",
}


def response(status: int = 200, serializer=None, body=None) -> dict:
    match body:
        case d, code if isinstance(code, int) and isinstance(d, dict):
            status = code
            body = d
    payload = {'body': json.dumps(body, default=serializer)} if body else {}
    return {
        'statusCode': status,
        'headers': _cors,
        **payload,
    }


def request(event: dict) -> dict | None:
    """
    Merges all params in the HTTP request
    into a single dictionary.
    Names in that dictionary will be in snake case.

    :param event: API Gateway event
    :return: path, body and query params merged into a single dict
    """
    match event:
        case {
            'pathParameters': path,
            'body': body,
            'queryStringParameters': query_params,
            'requestContext': context,
        }:
            body = json.loads(body) if body else {}
            # user_id = user_of(context)
            return {
                camel_to_snake(k): v
                for k, v in {
                    # **{'user_id': user_id},
                    **(path or {}),
                    **(query_params or {}),
                    **body,
                }.items()
            }


def user_of(context: dict) -> str:
    try:
        match context:
            case {'authorizer': {'user': raw}}:
                return json.loads(raw)['id']
            case _:
                raise Unauthorized
    except:
        raise Unauthorized


def argument_error(error: TypeError) -> dict | None:
    match error.args:
        case (arg, ) if 'unexpected keyword' in arg:
            match re.search(r"unexpected keyword argument '(\w+)'", arg):
                case re.Match(group=group):
                    return response(
                        status=400,
                        body={
                            'error': True,
                            'message': f'Unexpected argument "{group(1)}"'
                        }
                    )
        case (arg, ) if "missing 1 required keyword-only argument" in arg:
            match re.search(r"missing 1 required keyword-only argument: '(\w+)'", arg):
                case re.Match(group=group):
                    return response(
                        status=400,
                        body={
                            'error': True,
                            'message': f"Missing required argument: '{group(1)}'"
                        }
                    )
        case (arg, ) if "required keyword-only arguments" in arg:
            pattern = r": (.+)"
            match re.search(pattern, arg):
                case re.Match(group=group):
                    return response(
                        status=400,
                        body={
                            'error': True,
                            'message': f'Missing required arguments: {group(1)}'
                        }
                    )
