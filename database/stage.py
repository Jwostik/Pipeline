from pypika import PostgreSQLQuery, Table
import jq
import requests

from models import Stage
from exceptions import HTTPStageException, JQStringException, PostgresStageException
from typing import Any
import psycopg2
from prometheus_client import Counter, Histogram


all_stages = Counter('all_stages', 'A counter of all stages made')
stages_time = Histogram('stages_time', 'Time spent to stages')


def create(pipeline_id: int, stage_index_in_pipeline: int, stage: Stage, curs=None) -> int:
    curs.execute(PostgreSQLQuery.
                 into('stages').
                 columns('pipeline_id', 'index_in_pipeline', 'type', 'params').
                 insert(pipeline_id, stage_index_in_pipeline, stage.type, stage.params.toJSON()).
                 returning('stage_id').get_sql())
    stage_id, = curs.fetchone()
    return stage_id


def execute(stage_id: int, data, curs=None):
    stage_table = Table('stages')
    curs.execute(PostgreSQLQuery.
                 from_(stage_table).
                 select('pipeline_id', 'index_in_pipeline', 'params', 'type').
                 where(stage_table.stage_id == stage_id).get_sql())
    pipeline_id, index_in_pipeline, params, stage_type = curs.fetchone()
    with stages_time.time():
        if stage_type == "HTTP":
            data = http_execute(params, data)
        elif stage_type == "Postgres":
            data = postgres_execute(params, data)
    all_stages.inc()
    curs.execute(PostgreSQLQuery.
                 from_(stage_table).
                 select('stage_id').
                 where(
        stage_table.pipeline_id == pipeline_id and stage_table.index_in_pipeline == index_in_pipeline + 1).
                 get_sql())
    fetch_result = curs.fetchone()
    if fetch_result is None:
        next_stage = -1
    else:
        next_stage = fetch_result[0]
    data["stage_" + str(index_in_pipeline)] = 'completed'
    return next_stage, data


def transform_json(params: str, data: Any) -> str:
    if params is None:
        return ''
    try:
        return jq.compile(params).input_value(data).first()
    except ValueError as e:
        raise JQStringException("Invalid jq string: " + str(e))


def http_execute(params: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    path = transform_json(params["path_params"], data)
    if path and path[0] == '/':
        path = path[1:]

    query = transform_json(params["query_params"], data)
    if query:
        query = "?" + query

    body = transform_json(params["body"], data)

    if params["url_path"][-1] == '/':
        url_path = params["url_path"] + path + query
    else:
        url_path = params["url_path"] + '/' + path + query

    try:
        if params["method"] == "POST":
            response = requests.post(url_path, json=body, verify=False)
        elif params["method"] == "GET":
            response = requests.get(url_path, verify=False)
    except Exception as e:
        raise HTTPStageException(str(e))

    if response.status_code not in params["return_codes"]:
        raise HTTPStageException("Invalid return code of stage: " + str(response.status_code) + ' ' + str(response.content))

    try:
        response_data = response.json()
    except Exception as e:
        raise HTTPStageException(str(e))
    for key, jq_string in params["return_values"].items():
        data[key] = transform_json(jq_string, response_data)
    return data


def postgres_execute(params: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    connection = transform_json(params["connection"], data)
    query = transform_json(params["query"], data)
    try:
        with psycopg2.connect(connection) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                if cur.statusmessage[:6] == 'SELECT':
                    response_data = cur.fetchall()
                    for key, jq_string in params["return_values"].items():
                        data[key] = transform_json(jq_string, response_data)
                conn.commit()
    except Exception as e:
        raise PostgresStageException(str(e))
    return data
