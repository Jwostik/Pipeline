import json

import psycopg2.errors
import psycopg2.pool

import exceptions
from fastapi_classes import Stage

pool = psycopg2.pool.SimpleConnectionPool(1, 5, user='postgres', password='postgres', database='tester')


def connect(func):
    def wrapper(*args, **kwargs):
        conn, curs = None, None
        try:
            conn = pool.getconn()
            curs = conn.cursor()

            kwargs['curs'] = curs
            result = func(*args, **kwargs)
            conn.commit()
        finally:
            if curs:
                curs.close()
            if conn:
                pool.putconn(conn)
        return result

    return wrapper


@connect
def create_stage(pipeline_id: int, stage_index_in_pipeline: int, stage: Stage, curs=None) -> int:
    curs.execute(
        "insert into stages (pipeline_id, index_in_pipeline, type, params) values (%s, %s, %s, %s) RETURNING stage_id",
        [pipeline_id, stage_index_in_pipeline, stage.type, stage.params.toJSON()])
    stage_id = curs.fetchone()
    return stage_id


@connect
def set_next_stage(stage_id: int, next_stage_id: int, curs=None) -> None:
    curs.execute("update stages set next_stage=%s where stage_id=%s", [next_stage_id, stage_id])


@connect
def create_pipeline(pipeline_name: str, curs=None) -> int:
    try:
        curs.execute("insert into pipelines (pipeline_name) values (%s) RETURNING pipeline_id", [pipeline_name])
        pipeline_id, = curs.fetchone()
        return pipeline_id
    except psycopg2.errors.UniqueViolation:
        raise exceptions.PipelineNameConflictException("Name of pipeline has already used")


@connect
def set_first_stage(pipeline_id: int, first_stage: int, curs=None) -> None:
    curs.execute("update pipelines set first_stage=%s where pipeline_id=%s", [first_stage, pipeline_id])


@connect
def create_job(pipeline_id: int, first_stage: int, job_body, curs=None) -> int:
    curs.execute(
        "insert into jobs_status (pipeline_id, stage_id, job_status, data, started) values (%s, %s, %s, %s, %s) RETURNING job_status_id",
        [pipeline_id, first_stage, 'waiting', json.dumps(job_body), False])
    job_status_id, = curs.fetchone()
    return job_status_id


@connect
def get_pipeline_id_and_first_stage_by_pipeline_name(pipeline_name: str, curs=None) -> (int, int):
    curs.execute("select pipeline_id, first_stage from pipelines where pipeline_name=%s", [pipeline_name])
    fetch_result = curs.fetchone()
    if fetch_result is None:
        raise exceptions.NoPipelineException("Pipeline " + pipeline_name + " does not exist")
    pipeline_id, first_stage, = fetch_result
    return pipeline_id, first_stage


@connect
def insert_job_in_queue(jobs_status_id: int, curs=None) -> None:
    curs.execute("insert into queue (job_status_id) values (%s)", [jobs_status_id])


@connect
def get_status_job(job_id: int, curs=None) -> str:
    curs.execute("select pipeline_id, stage_id, job_status, job_error from jobs_status where job_status_id = %s", [job_id])
    fetch_result = curs.fetchone()
    if fetch_result is None:
        raise exceptions.NoJobException("Job with id " + str(job_id) + " does not exist")
    pipeline_id, stage_id, job_status, job_error, = fetch_result
    if job_status == "error":
        return job_error
    if job_status == "success":
        return "Success"
    curs.execute("select pipeline_name from pipelines where pipeline_id = %s", [pipeline_id])
    pipeline_name, = curs.fetchone()
    curs.execute("select index_in_pipeline from stages where stage_id = %s", [stage_id])
    index_in_pipeline, = curs.fetchone()
    return "Job " + pipeline_name + " " + job_status + " on stage " + str(index_in_pipeline)

