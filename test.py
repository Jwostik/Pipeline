import json
import os
import pytest
from pypika import Query

import psycopg2
import psycopg2.pool
from fastapi.testclient import TestClient
from testcontainers.postgres import PostgresContainer

import database.db_connection
from pipeline_routes import app

client = TestClient(app)


def get_connection():
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")
    dbname = os.getenv("DB_NAME")
    return psycopg2.connect(f"host={host} dbname={dbname} user={username} password={password} port={port}")


def replace_pool():
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")
    dbname = os.getenv("DB_NAME")
    database.db_connection.pool = psycopg2.pool.SimpleConnectionPool(1, 5,
                                                       f"host={host} dbname={dbname} user={username} password={password} port={port}")


def create_tables():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                create table pipelines (
                    pipeline_id bigserial primary key, 
                    pipeline_name text unique);
                create table stages (
                    stage_id bigserial primary key, 
                    pipeline_id bigint references pipelines(pipeline_id), 
                    index_in_pipeline int, 
                    type stage_type, 
                    params jsonb,
                    unique (pipeline_id, index_in_pipeline));
                alter table pipelines add column first_stage bigint references stages(stage_id);
                create table jobs_status (
                    job_status_id bigserial primary key, 
                    pipeline_id bigint references pipelines(pipeline_id), 
                    stage_id bigint references stages(stage_id), 
                    job_status status_text, 
                    job_error text, 
                    data jsonb, 
                    started boolean);
                create table queue (
                    job_status_id bigint references jobs_status(job_status_id));
                """)
            conn.commit()


def drop_tables():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                drop table pipelines cascade;
                drop table stages cascade;
                drop table jobs_status cascade;
                drop table queue cascade;
                """)
            conn.commit()


postgres = PostgresContainer("postgres:16")


@pytest.fixture(scope="module", autouse=True)
def setup(request):
    postgres.start()

    def remove_container():
        postgres.stop()

    request.addfinalizer(remove_container)
    os.environ["DB_HOST"] = postgres.get_container_host_ip()
    os.environ["DB_PORT"] = postgres.get_exposed_port(5432)
    os.environ["DB_USERNAME"] = postgres.username
    os.environ["DB_PASSWORD"] = postgres.password
    os.environ["DB_NAME"] = postgres.dbname
    replace_pool()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TYPE stage_type AS ENUM ('HTTP');
                CREATE TYPE status_text AS ENUM ('waiting', 'in process', 'success', 'error');
                """)


@pytest.fixture(scope="function", autouse=True)
def setup_data():
    create_tables()
    yield
    drop_tables()


def test_insert_empty_pipeline():
    with pytest.raises(Exception):
        response = client.post("/pipeline")
        assert response.status_code == 400
        assert response.json == "Invalid request"


def test_insert_pipeline_without_stages():
    body = {
        "pipeline_name": "Authorization",
        "stages": {}}
    with pytest.raises(Exception):
        response = client.post("/pipeline", json=body)
        assert response.status_code == 400
        assert response.json == "Invalid request"


def test_insert_pipeline_with_bad_fields():
    body = {
        "bad_field": "Authorization",
        "stages": {
            "1":
                {
                    "type": "HTTP",
                    "params":
                        {
                            "url_path": "server.com/users/${path1}",
                            "method": "POST",
                            "body": '{"login": ".login", "password": ".password"}',
                            "return_value":
                                {
                                    "user_id": ".user_id"
                                },
                            "return_codes": [200]
                        }
                }
        }
    }
    with pytest.raises(Exception):
        response = client.post("/pipeline", json=body)
        assert response.status_code == 400
        assert response.json == "Invalid request"


correct_body = {
        "pipeline_name": "Authorization",
        "stages":
            [
                {
                    "type": "HTTP",
                    "params":
                        {
                            "url_path": "server.com/users/${path1}",
                            "method": "POST",
                            "body": '{"login": ".login", "password": ".password"}',
                            "return_values":
                                {
                                    "user_id": ".user_id"
                                },
                            "return_codes": [200]
                        }
                },
                {
                    "type": "HTTP",
                    "params":
                        {
                            "url_path": "server.com/auth",
                            "method": "POST",
                            "body": '{"user_id": ".user_id"}',
                            "return_values":
                                {
                                    "jwt": ".jwt"
                                },
                            "return_codes": [200]
                        }
                }
            ]
    }

def test_correct_insert_pipeline():
    response = client.post("/pipeline", json=correct_body)
    assert response.status_code == 200
    assert response.json() == 1


def test_insert_pipeline_with_same_name():
    client.post("/pipeline", json=correct_body)
    with pytest.raises(Exception):
        response = client.post("/pipeline", json=correct_body)
        assert response.status_code == 409
        assert response.json == "Name of pipeline has already used"


def insert_correct_pipeline(func):
    def wrapper(*args, **kwargs):
        client.post("/pipeline", json=correct_body)
        result = func(*args, **kwargs)
        return result

    return wrapper


@insert_correct_pipeline
def test_insert_job():
    job_body = {
        "path_key1": ".path_value1",
        "path_key2": ".path_value2",
        "query_key1": ".query_value1",
        "query_key2": ".query_value2",
        "data_key1": ".data_value1",
        "data_key2": ".data_value2"
    }
    response = client.post("/job?pipeline_name=Authorization", json=job_body)
    assert response.status_code == 200
    assert response.json() == 1


@insert_correct_pipeline
def test_invalid_job_body():
    job_body = "invalid"
    with pytest.raises(Exception):
        response = client.post("/job?pipeline_name=Authorization", json=job_body)
        assert response.status_code == 400
        assert response.json == "Invalid request"
    job_body = 1
    with pytest.raises(Exception):
        response = client.post("/job?pipeline_name=Authorization", json=job_body)
        assert response.status_code == 400
        assert response.json == "Invalid request"
    job_body = [1, 2, 3]
    with pytest.raises(Exception):
        response = client.post("/job?pipeline_name=Authorization", json=job_body)
        assert response.status_code == 400
        assert response.json == "Invalid request"
    job_body = None
    with pytest.raises(Exception):
        response = client.post("/job?pipeline_name=Authorization", json=job_body)
        assert response.status_code == 400
        assert response.json == "Invalid request"


def test_start_job_without_query():
    with pytest.raises(Exception):
        response = client.post("/job")
        assert response.status_code == 422
        assert response.json == "No pipeline_name in query"


def test_start_job_without_pipeline():
    with pytest.raises(Exception):
        response = client.post("/job?pipeline_name=Authorization", json={})
        assert response.status_code == 422
        assert response.json == "Pipeline Authorization does not exist"


def test_status_job_without_query():
    with pytest.raises(Exception):
        response = client.get("/job")
        assert response.status_code == 422
        assert response.json == "No job_id in query"


def test_status_job_with_not_integer_id():
    with pytest.raises(Exception):
        response = client.get("/job?job_id=a")
        assert response.status_code == 422
        assert response.json == "job_id must be integer"


def test_status_non_existing_job():
    with pytest.raises(Exception):
        response = client.get("/job?job_id=1")
        assert response.status_code == 422
        assert response.json == "Job with id 1 does not exist"


def test_status_success_job():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("insert into jobs_status (job_status) values ('success')")
    response = client.get("/job?job_id=1")
    assert response.status_code == 200
    assert response.content == b'"Success"'


def test_status_error_job():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("insert into jobs_status (job_status, job_error) values ('error', 'Error job status')")
    response = client.get("/job?job_id=1")
    assert response.status_code == 200
    assert response.content == b'"Error job status"'


@insert_correct_pipeline
def test_status_waiting_job():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("insert into jobs_status (job_status, pipeline_id, stage_id) values ('waiting', 1, 2)")
    response = client.get("/job?job_id=1")
    assert response.status_code == 200
    assert response.content == b'"Job Authorization waiting on stage 2"'


@insert_correct_pipeline
def test_status_in_process_job():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(Query.into('jobs_status').columns('job_status', 'pipeline_id', 'stage_id').insert('in process', 1, 2).get_sql())
    response = client.get("/job?job_id=1")
    assert response.status_code == 200
    assert response.content == b'"Job Authorization in process on stage 2"'


@insert_correct_pipeline
def test_get_pipeline():
    response = client.get("/pipeline?pipeline_name=Authorization")
    assert response.status_code == 200
    # assert json.loads(response.json()) == correct_body - спросить про заданные поля по умолчанию
