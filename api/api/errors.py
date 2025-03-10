from dataclasses import dataclass


class EmptyResponse(Exception):
    pass


class Unauthorized(Exception):
    pass


class Forbidden(Exception):
    pass


@dataclass
class NotFound(Exception):
    path: str
