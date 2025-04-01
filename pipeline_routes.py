from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

import service
import exceptions
from fastapi_classes import Pipeline
from typing import Any

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def custom_form_validation_error(request, exc):
    return JSONResponse(status_code=400, content="Invalid request")


@app.middleware("http")
async def error_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except exceptions.PipelineNameConflictException as e:
        return JSONResponse(status_code=409, content=e.args[0])
    except exceptions.InvalidStageKeyException as e:
        return JSONResponse(status_code=422, content=e.args[0])
    except exceptions.InvalidStageNumerationException as e:
        return JSONResponse(status_code=422, content=e.args[0])
    except exceptions.NoStageException as e:
        return JSONResponse(status_code=422, content=e.args[0])
    except exceptions.QueryParameterException as e:
        return JSONResponse(status_code=422, content=e.args[0])
    except exceptions.NoPipelineException as e:
        return JSONResponse(status_code=422, content=e.args[0])
    except exceptions.NoJobException as e:
        return JSONResponse(status_code=422, content=e.args[0])


@app.post("/pipeline")
async def create_pipeline(pipeline: Pipeline):
    return service.create_pipeline(pipeline)


@app.get("/pipeline")
async def get_pipeline(pipeline: Pipeline):
    return service.create_pipeline(pipeline)


@app.post("/job")
async def start_job(request: Request, body: dict[str, Any]):
    if not request.query_params.get('pipeline_name'):
        raise exceptions.QueryParameterException("No pipeline_name in query")
    pipeline_name = request.query_params.get('pipeline_name')
    return service.start_job(body, pipeline_name)


@app.get("/job")
async def get_status_job(request: Request):
    if not request.query_params.get('job_id'):
        raise exceptions.QueryParameterException("No job_id in query")
    job_id = request.query_params.get('job_id')
    if not job_id.isdigit():
        raise exceptions.QueryParameterException("job_id must be integer")
    job_id = request.query_params.get('job_id')
    return service.get_status_job(int(job_id))
