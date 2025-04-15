from pypika import PostgreSQLQuery, Table

import database.job
from database.db_connection import connect


def append(job_status_id: int, curs=None) -> int:
    curs.execute(PostgreSQLQuery.into('queue').columns('job_status_id').insert(job_status_id).returning(
        'stage_queue_id').get_sql())
    return curs.fetchone()[0]


@connect
def execute(job_status_id, curs=None):
    next_stage = database.job.execute(job_status_id, curs)
    if next_stage != -1:
        append(job_status_id, curs)


@connect
def execute_all(curs=None):
    queue_table = Table('queue')
    curs.execute(PostgreSQLQuery.from_(queue_table).select('stage_queue_id', 'job_status_id').where(
        queue_table.started == False).orderby('stage_queue_id').get_sql())
    fetch_result = curs.fetchone()
    while fetch_result is not None:
        stage_queue_id, job_status_id = fetch_result
        curs.execute(PostgreSQLQuery.update(queue_table).set(queue_table.started, True).where(
            queue_table.stage_queue_id == stage_queue_id).get_sql())
        execute(job_status_id)
        curs.execute(PostgreSQLQuery.from_(queue_table).select('stage_queue_id', 'job_status_id').where(
            queue_table.started == False).orderby('stage_queue_id').get_sql())
        fetch_result = curs.fetchone()
