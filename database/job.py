import json

from database.db_connection import connect
import exceptions


@connect
def create(pipeline_id: int, first_stage: int, job_body, curs=None) -> int:
    curs.execute(
        "insert into jobs_status (pipeline_id, stage_id, job_status, data, started) values (%s, %s, %s, %s, %s) RETURNING job_status_id",
        [pipeline_id, first_stage, 'waiting', json.dumps(job_body), False])
    job_status_id = curs.fetchone()
    curs.execute("insert into queue (job_status_id) values (%s)", [job_status_id])
    return job_status_id


@connect
def get_status(job_id: int, curs=None) -> str:
    curs.execute("select pipeline_id, stage_id, job_status, job_error from jobs_status where job_status_id = %s",
                 [job_id])
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
