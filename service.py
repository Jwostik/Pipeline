import database
import utilities
from fastapi_classes import Pipeline
from typing import Any


def create_pipeline(pipeline: Pipeline) -> int:
    if utilities.validate_stages(pipeline.stages):
        pipeline_id = database.create_pipeline(pipeline.pipeline_name)
        stage_id = database.create_stage(pipeline_id, 1, pipeline.stages['1'])
        database.set_first_stage(pipeline_id, stage_id)
        for i in range(2, len(pipeline.stages) + 1):
            next_stage_id = database.create_stage(pipeline_id, i, pipeline.stages[str(i)])
            database.set_next_stage(stage_id, next_stage_id)
            stage_id = next_stage_id
        return pipeline_id


def start_job(job_body: dict[str, Any], pipeline_name: str) -> int:
    pipeline_id, first_stage = database.get_pipeline_id_and_first_stage_by_pipeline_name(pipeline_name)
    jobs_status_id = database.create_job(pipeline_id, first_stage, job_body)
    database.insert_job_in_queue(jobs_status_id)
    return jobs_status_id


def get_status_job(job_id: int) -> str:
    return database.get_status_job(job_id)
