from typing import Any

import database.job
import database.pipeline
import exceptions
from models import Pipeline


def create_pipeline(pipeline: Pipeline) -> int:
    if len(pipeline.stages) == 0:
        raise exceptions.NoStageException("There is no stages in pipeline")
    return database.pipeline.create(pipeline)


def get_pipeline(pipeline_name: str):
    return database.pipeline.get(pipeline_name)


def start_job(job_body: dict[str, Any], pipeline_name: str) -> int:
    pipeline_id, first_stage = database.pipeline.get_id_and_first_stage(pipeline_name)
    jobs_status_id = database.job.create(pipeline_id, first_stage, job_body)
    return jobs_status_id


def get_status_job(job_id: int) -> str:
    return database.job.get_status(job_id)
