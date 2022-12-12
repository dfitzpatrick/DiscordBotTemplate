from typing import Any

from pydantic import BaseModel


class UnknownEntity(Exception):
    pass


class PgNotify(BaseModel):
    table: str
    action: str
    entity: Any