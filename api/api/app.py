from errors import EmptyResponse, Unauthorized, NotFound, Forbidden
from framework import response, request, argument_error
from utils import custom_serializer, dash_to_snake

import accounts


def router(event: dict) -> dict:
    """
    operation parsing relies on API Gateway's
    OperationName in the AWS::ApiGateway::Method resource.
    Those names are by convention in dash-case, so
    we'll convert them to snake_case
    and endpoint handlers are expected to be named the same as
    the endpoints themselves, hence this syntax:

    >>> getattr(accounts, function_name)(**request(event))

    :param event:
    :return:
    """
    match event:
        case {
            'path': path,
            'requestContext': {'operationName': operation},
        } if path.startswith('/accounts'):
            function_name = dash_to_snake(operation)
            return getattr(accounts, function_name)(**request(event))
        case {'path': path}:
            raise NotFound(path)
    raise ValueError(event)


def handler(event: dict, _):
    print(event)

    try:
        return response(
            body=router(event),
            serializer=custom_serializer,
        )
    except EmptyResponse:
        return response(status=204)
    except TypeError as e:
        return argument_error(e)
    except Forbidden as e:
        return response(
            status=403,
            body={'error': f'{e.__class__.__name__}'},
        )
    except Unauthorized as e:
        return response(
            status=401,
            body={'error': str(e)},
        )
    except NotFound as e:
        return response(
            status=404,
            body={'error': f'{e.path} not found'},
        )
    except Exception as e:
        return response(
            status=500,
            body={'error': str(e)},
        )
