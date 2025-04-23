import psycopg2.errors
from pypika import PostgreSQLQuery, Table

import database.stage
import exceptions
from database.db_connection import connect
from models import Pipeline


@connect
def create(pipeline: Pipeline, curs=None) -> int:
    pipelines_table = Table('pipelines')
    try:
        curs.execute(PostgreSQLQuery.
                     into(pipelines_table).
                     columns('pipeline_name').
                     insert(pipeline.pipeline_name).
                     returning('pipeline_id').get_sql())
    except psycopg2.errors.UniqueViolation:
        raise exceptions.PipelineNameConflictException("Name of pipeline has already used")
    else:
        pipeline_id, = curs.fetchone()
        first_stage_id = database.stage.create(pipeline_id, 1, pipeline.stages[0], curs)
        curs.execute(PostgreSQLQuery.
                     update(pipelines_table).
                     set(pipelines_table.first_stage, first_stage_id).
                     where(pipelines_table.pipeline_id == pipeline_id).get_sql())
        for i in range(1, len(pipeline.stages)):
            database.stage.create(pipeline_id, i + 1, pipeline.stages[i], curs)
        return pipeline_id


@connect
def get_id_and_first_stage(pipeline_name: str, curs=None) -> (int, int):
    pipelines_table = Table('pipelines')
    curs.execute(PostgreSQLQuery.
                 from_(pipelines_table).
                 select('pipeline_id', 'first_stage').
                 where(pipelines_table.pipeline_name == pipeline_name).get_sql())
    fetch_result = curs.fetchone()
    if fetch_result is None:
        raise exceptions.NoPipelineException("Pipeline " + pipeline_name + " does not exist")
    pipeline_id, first_stage, = fetch_result
    return pipeline_id, first_stage


@connect
def get(pipeline_name: str, curs=None):
    pipelines_table = Table('pipelines')
    curs.execute(PostgreSQLQuery.
                 from_(pipelines_table).
                 select('pipeline_id').
                 where(pipelines_table.pipeline_name == pipeline_name).get_sql())
    fetch_result = curs.fetchone()
    if fetch_result is None:
        raise exceptions.NoPipelineException("Pipeline " + pipeline_name + " does not exist")
    pipeline_id = fetch_result[0]
    response = {"pipeline_name": pipeline_name}
    stages = Table('stages')
    curs.execute(PostgreSQLQuery.
                 from_(stages).
                 select('type', 'params').
                 where(stages.pipeline_id == pipeline_id).
                 orderby('index_in_pipeline').get_sql())
    stages_from_db = curs.fetchall()
    stages = []
    for stage_from_db in stages_from_db:
        stages.append({"type": stage_from_db[0], "params": stage_from_db[1]})
    response["stages"] = stages
    return response
