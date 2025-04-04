import json

import psycopg2.errors

import exceptions
from database.db_connection import connect
from models import Pipeline
import database.stage
from pypika import PostgreSQLQuery , Table


@connect
def create(pipeline: Pipeline, curs=None) -> int:
    pipelines = Table('pipelines')
    try:
        curs.execute(PostgreSQLQuery.into(pipelines).columns('pipeline_name').insert(pipeline.pipeline_name).returning(
            'pipeline_id').get_sql())
    except psycopg2.errors.UniqueViolation:
        raise exceptions.PipelineNameConflictException("Name of pipeline has already used")
    else:
        pipeline_id, = curs.fetchone()
        first_stage_id = database.stage.create(pipeline_id, 1, pipeline.stages[0], curs)
        curs.execute(PostgreSQLQuery.update(pipelines).set(pipelines.first_stage, first_stage_id).where(
            pipelines.pipeline_id == pipeline_id).get_sql())
        for i in range(1, len(pipeline.stages)):
            database.stage.create(pipeline_id, i + 1, pipeline.stages[i], curs)
        return pipeline_id


@connect
def get_id_and_first_stage(pipeline_name: str, curs=None) -> (int, int):
    pipelines = Table('pipelines')
    curs.execute(PostgreSQLQuery.from_(pipelines).select('pipeline_id', 'first_stage').where(
        pipelines.pipeline_name == pipeline_name).get_sql())
    fetch_result = curs.fetchone()
    if fetch_result is None:
        raise exceptions.NoPipelineException("Pipeline " + pipeline_name + " does not exist")
    pipeline_id, first_stage, = fetch_result
    return pipeline_id, first_stage


@connect
def get(pipeline_name: str, curs=None) -> str:
    pipelines = Table('pipelines')
    curs.execute(
        PostgreSQLQuery.from_(pipelines).select('pipeline_id').where(pipelines.pipeline_name == pipeline_name).get_sql())
    pipeline_id, = curs.fetchone()
    if pipeline_id is None:
        raise exceptions.NoPipelineException("Pipeline " + pipeline_name + " does not exist")
    response = {"pipeline_name": pipeline_name}
    stages = Table('stages')
    curs.execute(
        PostgreSQLQuery.from_(stages).select('type', 'params').where(stages.pipeline_id == pipeline_id).orderby(
            'index_in_pipeline').get_sql())
    stages_from_db = curs.fetchall()
    stages = []
    for stage_from_db in stages_from_db:
        stages.append({"type": stage_from_db[0], "params": stage_from_db[1]})
    response["stages"] = stages
    return json.dumps(response)
