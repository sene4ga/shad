import dataclasses


@dataclasses.dataclass
class PickleVersion:
    is_new_format: bool
    version: int


def get_pickle_version(data: bytes) -> PickleVersion:
    """
    Returns used protocol version for serialization.

    :param data: serialized object in pickle format.
    :return: protocol version.
    """
    if len(data) >= 2 and data[0] == 0x80:
        return PickleVersion(True, data[1])

    return PickleVersion(False, -1)
