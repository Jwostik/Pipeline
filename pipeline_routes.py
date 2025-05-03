from typing import Any, Annotated

from fastapi import FastAPI, Request, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from prometheus_client import Counter, make_asgi_app

import exceptions
import models
import service
from models import Pipeline

app = FastAPI()

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
http_requests = Counter('http_requests', 'A counter of all http requests made')


@app.exception_handler(RequestValidationError)
async def custom_form_validation_error(request, exc):
    return JSONResponse(status_code=400, content=str(exc))


@app.middleware("http")
async def error_middleware(request: Request, call_next):
    try:
        http_requests.inc()
        return await call_next(request)
    except exceptions.PipelineNameConflictException as e:
        return JSONResponse(status_code=409, content=e.args[0])
    except exceptions.NoStageException as e:
        return JSONResponse(status_code=400, content=e.args[0])
    except exceptions.NoPipelineException as e:
        return JSONResponse(status_code=400, content=e.args[0])
    except exceptions.NoJobException as e:
        return JSONResponse(status_code=400, content=e.args[0])
    except Exception as e:
        return JSONResponse(status_code=500, content=e.args[0])


@app.post("/pipeline", responses=models.create_pipeline_responses)
async def create_pipeline(pipeline: Pipeline):
    return service.create_pipeline(pipeline)


@app.get("/pipeline", responses=models.get_pipeline_responses)
async def get_pipeline(request: Request, pipeline_name: Annotated[str, Query()]):
    pipeline_name = request.query_params.get('pipeline_name')
    return service.get_pipeline(pipeline_name)


@app.post("/job", responses=models.start_job_responses)
async def start_job(request: Request, body: dict[str, Any], pipeline_name: Annotated[str, Query()]):
    pipeline_name = request.query_params.get('pipeline_name')
    return service.start_job(body, pipeline_name)


@app.get("/job", responses=models.get_status_job_responses)
async def get_status_job(request: Request, job_id: Annotated[int, Query()]):
    job_id = request.query_params.get('job_id')
    return service.get_status_job(int(job_id))
