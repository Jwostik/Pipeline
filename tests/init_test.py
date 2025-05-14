import os

import psycopg2
import psycopg2.pool
import pytest
from fastapi.testclient import TestClient
from testcontainers.postgres import PostgresContainer
from pgmigrate import get_config, migrate, clean

import models

postgres = PostgresContainer("postgres:16").start()

os.environ["DB_HOST"] = postgres.get_container_host_ip()
os.environ["DB_PORT"] = postgres.get_exposed_port(5432)
os.environ["DB_USERNAME"] = postgres.username
os.environ["DB_PASSWORD"] = postgres.password
os.environ["DB_NAME"] = postgres.dbname

from pipeline_routes import app

client = TestClient(app)
migrations_dir = "pgmigrate_folder"


def get_connection():
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")
    dbname = os.getenv("DB_NAME")
    return psycopg2.connect(f"host={host} dbname={dbname} user={username} password={password} port={port}")


def drop_tables():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                drop table pipelines cascade;
                drop table stages cascade;
                drop table jobs_status cascade;
                drop table queue cascade;
                drop type stage_type cascade;
                drop type status_stage cascade;
                drop type status_text cascade;
                drop type http_stage_method;
                """)
            conn.commit()


@pytest.fixture(scope="function", autouse=True)
def setup_data():
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")
    dbname = os.getenv("DB_NAME")
    config = get_config(migrations_dir, models.Migration(target='latest',
                                                         conn=f"host={host} dbname={dbname} user={username} password={password} port={port} connect_timeout=1",
                                                         base_dir=migrations_dir))
    migrate(config)
    yield
    config = get_config(migrations_dir, models.Migration(
        conn=f"host={host} dbname={dbname} user={username} password={password} port={port} connect_timeout=1",
        base_dir=migrations_dir))
    clean(config)
    drop_tables()


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


def insert_correct_pipeline(func):
    def wrapper(*args, **kwargs):
        client.post("/pipeline", json=correct_body)
        result = func(*args, **kwargs)
        return result

    return wrapper


def insert_correct_job(func):
    def wrapper(*args, **kwargs):
        job_body = {
            "path_key1": ".path_value1",
            "path_key2": ".path_value2",
            "query_key1": ".query_value1",
            "query_key2": ".query_value2",
            "data_key1": ".data_value1",
            "data_key2": ".data_value2"
        }
        client.post("/job?pipeline_name=Authorization", json=job_body)
        result = func(*args, **kwargs)
        return result

    return wrapper
