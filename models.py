from pydantic import BaseModel, Extra
from typing import Union
import json


class StageAPI:
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class HTTPStage(BaseModel, StageAPI):
    url_path: str
    method: str
    path_params: Union[str, None] = None
    query_params: Union[str, None] = None
    body: Union[str, None] = None
    return_values: Union[dict[str, str], None] = None
    return_codes: list[int]

    class Config:
        extra = Extra.forbid


class Stage(BaseModel):
    type: str
    params: Union[HTTPStage]

    class Config:
        extra = Extra.forbid


class Pipeline(BaseModel):
    pipeline_name: str
    stages: list[Stage]

    class Config:
        extra = Extra.forbid
