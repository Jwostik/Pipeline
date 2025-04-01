import pydantic
from pydantic import BaseModel, RootModel
from typing import Union, Any
import json


class HTTPStage(BaseModel):
    url_path: str
    method: str
    path_params: Union[str, None] = None
    query_params: Union[str, None] = None
    body: Union[str, None] = None
    return_values: Union[dict[str, str], None] = None
    return_codes: list[int]

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class DatabaseStage(BaseModel):
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class Stage(BaseModel):
    type: str
    params: Union[HTTPStage, DatabaseStage]


class Pipeline(BaseModel):
    pipeline_name: str
    stages: dict[str, Stage]

