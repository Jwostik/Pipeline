from pypika import PostgreSQLQuery, Table
import datetime

import database.job
from database.db_connection import connect


def append(job_status_id: int, curs=None):
    curs.execute(PostgreSQLQuery.into('queue').
                 columns('job_status_id').
                 insert(job_status_id).
                 returning('stage_queue_id').get_sql())


@connect
def execute(curs=None):
    queue_table = Table('queue')
    curs.execute(PostgreSQLQuery.
                 update(queue_table).
                 set(queue_table.status, 'started').
                 set(queue_table.started_time, datetime.datetime.now()).
                 where(queue_table.stage_queue_id == PostgreSQLQuery.
                       from_(queue_table).
                       select('stage_queue_id').
                       where(queue_table.status == 'waiting').
                       orderby('stage_queue_id').
                       limit(1)).
                 returning('stage_queue_id', 'job_status_id').
                 get_sql())
    fetch_result = curs.fetchone()
    if fetch_result is not None:
        stage_queue_id, job_status_id = fetch_result
        next_stage = database.job.execute(job_status_id, curs)
        curs.execute(PostgreSQLQuery.
                     update(queue_table).
                     set(queue_table.status, 'done').
                     set(queue_table.started_time, datetime.datetime.now()).
                     where(queue_table.stage_queue_id == stage_queue_id).
                     get_sql())
        if next_stage != -1:
            append(job_status_id, curs)


@connect
def healthcheck(interval: int, curs=None):
    queue_table = Table('queue')
    control_date = datetime.datetime.now() - datetime.timedelta(seconds=interval)
    curs.execute(PostgreSQLQuery.
                 from_(queue_table).
                 delete().
                 where(queue_table.status == 'done').
                 where(queue_table.started_time < control_date).
                 get_sql())
    curs.execute(PostgreSQLQuery.
                 from_(queue_table).
                 select(queue_table.job_status_id).
                 where(queue_table.started_time < control_date).
                 get_sql())
    if curs.rowcount > 0:
        print("Consumer dead")
        curs.execute(PostgreSQLQuery.
                     from_(queue_table).
                     select(queue_table.job_status_id).
                     where(queue_table.status == 'started').
                     where(queue_table.started_time < control_date).
                     get_sql())
        jobs_table = Table("jobs")
        for job_id in curs.fetchall():
            curs.execute(PostgreSQLQuery.
                         update(jobs_table).
                         set(jobs_table.job_status, 'error').
                         set(jobs_table.job_error, 'Internal error: consumer dead').
                         where(jobs_table.job_status_id == job_id).get_sql())
