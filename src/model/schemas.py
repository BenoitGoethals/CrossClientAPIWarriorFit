from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class RunnerBase(BaseModel):
    serial_number: Optional[str] = None
    running_time: float = Field(alias="time")


class RunnerCreate(RunnerBase):
    model_config = ConfigDict(populate_by_name=True)


class RunnerResponse(RunnerBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CrossBase(BaseModel):
    datetime_start: datetime
    distance: float
    executed: bool = False
    description: Optional[str] = None


class CrossCreate(CrossBase):
    pass


class CrossResponse(CrossBase):
    id: int
    runners: List[RunnerResponse] = []

    model_config = ConfigDict(from_attributes=True)


class CrossRunnersBase(BaseModel):
    cross_id: int
    runner_id: int


class CrossRunnersCreate(CrossRunnersBase):
    pass


class CrossRunnersResponse(CrossRunnersBase):
    model_config = ConfigDict(from_attributes=True)


class UnitBase(BaseModel):
    name: str
    base_location: str


class UnitCreate(UnitBase):
    pass


class UnitResponse(UnitBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
