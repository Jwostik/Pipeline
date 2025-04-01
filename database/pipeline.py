import json

import psycopg2.errors

import exceptions
from database.db_connection import connect
from models import Pipeline
import database.stage


@connect
def create(pipeline: Pipeline, curs=None) -> int:
    try:
        curs.execute("insert into pipelines (pipeline_name) values (%s) RETURNING pipeline_id", [pipeline.pipeline_name])
    except psycopg2.errors.UniqueViolation:
        raise exceptions.PipelineNameConflictException("Name of pipeline has already used")
    else:
        pipeline_id = curs.fetchone()
        first_stage_id = database.stage.create(pipeline_id, 1, pipeline.stages[0], curs)
        curs.execute("update pipelines set first_stage=%s where pipeline_id=%s", [first_stage_id, pipeline_id])
        for i in range(1, len(pipeline.stages)):
            database.stage.create(pipeline_id, i + 1, pipeline.stages[i], curs)
        return pipeline_id


@connect
def get_id_and_first_stage(pipeline_name: str, curs=None) -> (int, int):
    curs.execute("select pipeline_id, first_stage from pipelines where pipeline_name=%s", [pipeline_name])
    fetch_result = curs.fetchone()
    if fetch_result is None:
        raise exceptions.NoPipelineException("Pipeline " + pipeline_name + " does not exist")
    pipeline_id, first_stage, = fetch_result
    return pipeline_id, first_stage


@connect
def get(pipeline_name: str, curs=None) -> str:
    curs.execute("select pipeline_id from pipelines where pipeline_name=%s", [pipeline_name])
    pipeline_id = curs.fetchone()
    if pipeline_id is None:
        raise exceptions.NoPipelineException("Pipeline " + pipeline_name + " does not exist")
    responce = {"pipeline_name": pipeline_name}
    curs.execute("select type, params from stages where pipeline_id=%s order by index_in_pipeline", [pipeline_id])
    stages_from_db = curs.fetchall()
    stages = []
    for stage_from_db in stages_from_db:
        stages.append({"type": stage_from_db[0], "params": stage_from_db[1]})
    responce["stages"] = stages
    return json.dumps(responce)
