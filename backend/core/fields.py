import os
import time
import uuid

from django.db import models


def uuidv8() -> uuid.UUID:
    ts = int(time.time() * 1000)
    rand = os.urandom(10)

    time_low = ts & 0xFFFFFFFF
    time_mid = (ts >> 32) & 0xFFFF
    time_hi = (ts >> 48) & 0x0FFF

    b = bytearray(16)
    b[0:4] = time_low.to_bytes(4, byteorder="big")
    b[4:6] = time_mid.to_bytes(2, byteorder="big")
    b[6:8] = (time_hi | (8 << 12)).to_bytes(2, byteorder="big")

    clock_seq = 0x8000 | ((rand[0] << 8) | rand[1]) & 0x3FFF
    b[8:10] = clock_seq.to_bytes(2, byteorder="big")
    b[10:16] = rand[2:8]

    return uuid.UUID(bytes=bytes(b))


class UUIDv8Field(models.UUIDField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("default", uuidv8)
        kwargs.setdefault("editable", False)
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is not None:
            if isinstance(value, uuid.UUID):
                return value.hex
            elif isinstance(value, str) and '-' in value:
                return value.replace('-', '')
        return value

    def from_db_value(self, value, expression, connection):
        if value is not None:
            if isinstance(value, uuid.UUID):
                return value
            elif isinstance(value, str) and len(value) == 32:
                return uuid.UUID(hex=value)
        return value