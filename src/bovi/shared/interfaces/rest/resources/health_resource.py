from typing import Literal

from pydantic import BaseModel

Status = Literal["ok", "error"]


class HealthResource(BaseModel):
    status: Status
    database: Status
    version: str
