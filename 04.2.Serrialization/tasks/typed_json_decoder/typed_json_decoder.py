import typing as tp
import json

from decimal import Decimal

def decode_typed_json(json_value: str) -> tp.Any:
    """
    Returns deserialized object from json string.
    Checks __custom_key_type__ in object's keys to choose appropriate type.

    :param json_value: serialized object in json format
    :return: deserialized object
    """

    def convert(obj):
        if isinstance(obj, dict):
            key_type = obj.get("__custom_key_type__")

            new_obj = {}
            for k, v in obj.items():
                if k == "__custom_key_type__":
                    continue
                new_obj[k] = convert(v)

            if key_type:
                converter = get_converter(key_type)
                return {converter(k): v for k, v in new_obj.items()}

            return new_obj

        elif isinstance(obj, list):
            return [convert(item) for item in obj]

        else:
            return obj

    def get_converter(type_name: str):
        if type_name == "int":
            return int
        elif type_name == "float":
            return float
        elif type_name == "decimal":
            return Decimal
        else:
            raise ValueError(f"Unsupported type: {type_name}")

    parsed = json.loads(json_value)
    return convert(parsed)
