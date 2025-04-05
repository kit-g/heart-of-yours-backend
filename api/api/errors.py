from dataclasses import dataclass


class EmptyResponse(Exception):
    pass


class Unauthorized(Exception):
    pass


@dataclass
class Forbidden(Exception):
    message: str = None


@dataclass
class NotFound(Exception):
    path: str


@dataclass
class ProgrammingError(Exception):
    message: str
