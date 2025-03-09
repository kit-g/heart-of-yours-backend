import re
from datetime import datetime
from decimal import Decimal

camel_pattern = re.compile(r'(?<!^)(?=[A-Z])')


def camel_to_snake(s: str) -> str:
    return re.sub(camel_pattern, '_', s).lower()


def snake_to_camel(s: str) -> str:
    components = s.split('_')
    # Capitalize the first letter of each component except the first one
    return components[0] + ''.join(x.capitalize() for x in components[1:])


def dash_to_snake(s: str) -> str:
    return s.replace('-', '_')


def custom_serializer(obj):
    match obj:
        case datetime():
            return obj.isoformat()
        case Decimal():
            return int(obj)
        case _:
            raise TypeError("Type not serializable")
