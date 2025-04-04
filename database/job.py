import json
from pypika import PostgreSQLQuery, Table

from database.db_connection import connect
import exceptions


@connect
def create(pipeline_id: int, first_stage: int, job_body, curs=None) -> int:
    curs.execute(
        PostgreSQLQuery.into('jobs_status').columns('pipeline_id', 'stage_id', 'job_status', 'data', 'started').insert(
            pipeline_id, first_stage, 'waiting', json.dumps(job_body), False).returning(
            'job_status_id').get_sql())
    job_status_id, = curs.fetchone()
    curs.execute(PostgreSQLQuery.into('queue').columns('job_status_id').insert(job_status_id).get_sql())
    return job_status_id


@connect
def get_status(job_id: int, curs=None) -> str:
    jobs_status = Table('jobs_status')
    curs.execute(PostgreSQLQuery.from_(jobs_status).select('pipeline_id', 'stage_id', 'job_status', 'job_error').where(
        jobs_status.job_status_id == job_id).get_sql())
    fetch_result = curs.fetchone()
    if fetch_result is None:
        raise exceptions.NoJobException("Job with id " + str(job_id) + " does not exist")
    pipeline_id, stage_id, job_status, job_error, = fetch_result
    if job_status == "error":
        return job_error
    if job_status == "success":
        return "Success"
    pipelines = Table('pipelines')
    curs.execute(
        PostgreSQLQuery.from_(pipelines).select('pipeline_name').where(pipelines.pipeline_id == pipeline_id).get_sql())
    pipeline_name, = curs.fetchone()
    stages = Table('stages')
    curs.execute(PostgreSQLQuery.from_(stages).select('index_in_pipeline').where(stages.stage_id == stage_id).get_sql())
    index_in_pipeline, = curs.fetchone()
    return "Job " + pipeline_name + " " + job_status + " on stage " + str(index_in_pipeline)
