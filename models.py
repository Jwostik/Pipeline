from pydantic import BaseModel, Extra
from enum import Enum
from typing import Union
import json


class StageAPI:
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class StageType(str, Enum):
    http = 'HTTP'


class StatusText(str, Enum):
    waiting = 'waiting'
    in_process = 'in process'
    success = 'success'
    error = 'error'


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
    type: StageType
    params: Union[HTTPStage]

    class Config:
        extra = Extra.forbid


class Pipeline(BaseModel):
    pipeline_name: str
    stages: list[Stage]

    class Config:
        extra = Extra.forbid


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
