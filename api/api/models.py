from dataclasses import dataclass, field
from typing import Any, Self

from dynamo import TypedModelWithSortableKey, DynamoModel

_exercise_type = 'EXERCISE'
_user_type = 'USER'
_workout_type = 'WORKOUT'


@dataclass
class User:
    id: str
    name: str
    email: str
    verified: bool

    @classmethod
    def from_dict(cls, d: dict) -> Self:
        return cls(
            id=d['uid'],
            name=d['name'],
            email=d['email'],
            verified=d['email_verified'],
        )


@dataclass
class Exercise(TypedModelWithSortableKey):
    name: str
    category: str
    target: str
    asset: str = None
    thumbnail: str = None
    instructions: str = None

    def _to_item(self) -> dict[str, Any]:
        asset = {'asset': self.asset} if self.asset else {}
        thumbnail = {'asset': self.thumbnail} if self.thumbnail else {}
        instructions = {'asset': self.instructions} if self.instructions else {}
        return {
            'PK': self.type,
            'SK': self.name,
            'category': self.category,
            'target': self.target,
            **asset,
            **thumbnail,
            **instructions,
        }

    @classmethod
    def from_item(cls, record: dict) -> Self:
        return cls(
            name=record['name']['S'],
            category=record['category']['S'],
            target=record['target']['S'],
            asset=record.get('asset', {}).get('S'),
            thumbnail=record.get('thumbnail', {}).get('S'),
            instructions=record.get('instructions', {}).get('S'),
        )

    @property
    def type(self) -> str:
        return _exercise_type

    @property
    def pk(self) -> str:
        return _exercise_type

    @property
    def sk(self) -> str:
        return self.name

    @property
    def id(self) -> str:
        return self.name


@dataclass
class Set(DynamoModel):
    id: str
    completed: bool
    reps: int = None
    weight: float = None
    duration: float = None
    distance: float = None

    def _to_item(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'completed': self.completed,
            'reps': self.reps,
            'weight': self.weight,
            'duration': self.duration,
            'distance': self.distance,
        }

    @classmethod
    def from_item(cls, record: dict):
        pass

    @classmethod
    def from_dict(cls, d: dict) -> Self:
        return cls(
            id=d.get('id'),
            completed=d.get('completed'),
            reps=d.get('reps'),
            weight=d.get('weight'),
            duration=d.get('duration'),
            distance=d.get('distance'),
        )


@dataclass
class WorkoutExercise(DynamoModel):
    id: str
    exercise: str
    sets: list[Set]

    def _to_item(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'exercise': self.exercise,
            'sets': [
                {'M': each.to_item(exclude_nulls=True)}
                for each in self.sets
            ]
        }

    @classmethod
    def from_item(cls, record: dict) -> Self:
        pass

    @classmethod
    def from_dict(cls, d: dict) -> Self:
        return cls(
            id=d['id'],
            exercise=d['exercise'],
            sets=[
                Set.from_dict(each) for each in d['sets']
            ]
        )


@dataclass
class Workout(TypedModelWithSortableKey):
    user_id: str
    start: str
    _id: str
    end: str = None
    name: str = None
    exercises: list[WorkoutExercise] = field(default_factory=list)

    def _to_item(self) -> dict[str, Any]:
        return {
            'PK': self.pk,
            'SK': self.sk,
            'start': self.start,
            'end': self.end,
            'name': self.name,
            'exercises': [
                {'M': each.to_item()} for each in self.exercises
            ],
        }

    @classmethod
    def from_item(cls, record: dict):
        pass

    @classmethod
    def from_dict(cls, d: dict, user_id: str) -> Self:
        return cls(
            user_id=user_id,
            start=d['start'],
            _id=d['id'],
            end=d.get('end'),
            name=d.get('name'),
            exercises=[
                WorkoutExercise.from_dict(each)
                for each in d.get('exercises') or []
            ],
        )

    @property
    def type(self) -> str:
        return _workout_type

    @property
    def pk(self) -> str:
        return f'{_user_type}#{self.user_id}'

    @property
    def sk(self) -> str:
        return f'{self.type}#{self.start}'

    @property
    def id(self) -> str:
        return self._id
