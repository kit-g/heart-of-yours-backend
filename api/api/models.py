from dataclasses import dataclass


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
