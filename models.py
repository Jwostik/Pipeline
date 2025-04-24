from pydantic import BaseModel, Extra, Field
from enum import Enum
from typing import Union
import json


class StageAPI:
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class Forbidden(BaseModel):
    class Config:
        extra = Extra.forbid


class StageType(str, Enum):
    http = 'HTTP'
    postgres = 'Postgres'


class StatusText(str, Enum):
    waiting = 'waiting'
    in_process = 'in process'
    success = 'success'
    error = 'error'


class HTTPStageMethod(str, Enum):
    post = "POST"
    get = "GET"


class HTTPStage(Forbidden, StageAPI):
    url_path: str = Field(
        description="URL-path to service",
        example="server.com/users"
    )
    method: HTTPStageMethod = Field(
        description="HTTP-method of request"
    )
    path_params: Union[str, None] = Field(
        default=None,
        description="String with jq filters needed to convert path params of stage from incoming data",
        example='"/fixed/" + .path1 + "/fixed/" + .path2'
    )
    query_params: Union[str, None] = Field(
        default=None,
        description="String with jq filters needed to convert query params of stage from incoming data",
        example='"query1=" + .query1 + "&query2=" + .query2'
    )
    body: Union[str, None] = Field(
        default=None,
        description="String with jq filters needed to convert data needed in stage from incoming data",
        example='{login: .login, password: .password}'
    )
    return_values: Union[dict[str, str], None] = Field(
        default=None,
        description="HashMap of keys of return values of stage with jq filters needed to "
                    "transform them to data send to next stage",
        example={
            "user_id": ".hello"
        }
    )
    return_codes: list[int] = Field(
        description="Correct HTTP-response codes to continue execute stages",
        example=[200]
    )


class PostgresStage(Forbidden, StageAPI):
    connection: str = Field(
        description="Jq string consist of connection string to Postgres database",
        example='"host=" + .host + " dbname=" + .dbname + " user=" + .username + '
                '" password=" + .password + " port=" + .port'
    )
    query: str = Field(
        description="Jq string consist of database query",
        example='"select " + .first + ", " + .second " from " + .db_name + ";"'
    )
    return_values: Union[dict[str, str], None] = Field(
        default=None,
        description="HashMap of keys of return values of stage with jq filters "
                    "needed to transform them to data send to next stage",
        example={
            "user_id": ".hello"
        }
    )


class Stage(Forbidden):
    type: StageType
    params: Union[HTTPStage, PostgresStage]


class Pipeline(Forbidden):
    pipeline_name: str = Field(
        description="Name of pipeline"
    )
    stages: list[Stage] = Field(
        description="Array of stages of pipeline"
    )


class Migration:
    def __init__(self, *, target=None, conn, base_dir=''):
        self.target = target
        self.conn = conn
        self.base_dir = base_dir


create_pipeline_responses = {
    200: {
        "description": "Id of created pipeline",
        "content": {
            "application/json": {
                "schema": {
                    "type": "integer",
                    "example": 1
                }
            }
        }
    },
    400: {
        "description": "Invalid input",
        "content": {
            "application/json": {
                "schema": {
                    "type": "string",
                    "example": "Invalid request"
                }
            }
        }
    },
    409: {
        "description": "Conflict name of pipeline",
        "content": {
            "application/json": {
                "schema": {
                    "type": "string",
                    "example": "Name of pipeline has already used"
                }
            }
        }
    },
}

get_pipeline_responses = {
    200: {
        "description": "Info about existing pipeline",
        "content": {
            "application/json": {
                "schema": {
                    "$ref": "#/components/schemas/Pipeline"
                }
            }
        }
    },
    400: {
        "description": "Invalid input",
        "content": {
            "application/json": {
                "schema": {
                    "type": "string",
                    "example": "Invalid request"
                }
            }
        }
    },
    422: {
        "description": "Validation exception",
        "content": {
            "application/json": {
                "schema": {
                    "type": "string",
                    "example": "No pipeline_name in query"
                }
            }
        }
    }
}

start_job_responses = {
    200: {
        "description": "Id of created job",
        "content": {
            "application/json": {
                "schema": {
                    "type": "integer",
                    "description": "ID started job",
                    "example": 10
                }
            }
        }
    },
    400: {
        "description": "Invalid input",
        "content": {
            "application/json": {
                "schema": {
                    "type": "string",
                    "example": "Invalid request"
                }
            }
        }
    },
    422: {
        "description": "Validation exception",
        "content": {
            "application/json": {
                "schema": {
                    "type": "string",
                    "example": "No pipeline_name in query"
                }
            }
        }
    }
}

get_status_job_responses = {
    200: {
        "description": "Status of job",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "oneOf": [
                        {
                            "type": "string",
                            "example": "Success"
                        },
                        {
                            "type": "string",
                            "description": "Message about processing job with id of current executing stage",
                            "example": "Job MyJob in process on stage 2"
                        },
                        {
                            "type": "string",
                            "description": "Error message",
                            "example": "Can't insert into database via conflict name"
                        },
                        {
                            "type": "string",
                            "description": "Message about processing job with id of current stage",
                            "example": "Job MyJob waiting on stage 2"
                        }
                    ]
                }
            }
        }
    },
    400: {
        "description": "Invalid input",
        "content": {
            "application/json": {
                "schema": {
                    "type": "string",
                    "example": "Invalid request"
                }
            }
        }
    },
    422: {
        "description": "Validation exception",
        "content": {
            "application/json": {
                "schema": {
                    "type": "string",
                    "example": "No job_id in query"
                }
            }
        }
    }
}
