from wiremock.resources.mappings import HttpMethods
from wiremock.testing.testcontainer import wiremock_container

from init_test import *
import database.stage_queue


def get_http_post_stage(path):
    return {
        "type": "HTTP",
        "params":
            {
                "url_path": path,
                "method": "POST",
                "path_params": '"/fixed/" + .path1 + "/fixed/" + .path2',
                "query_params": '"query1=" + .query1 + "&query2=" + .query2',
                "body": '{login: .login, password: .password}',
                "return_values":
                    {
                        "user_id": ".hello"
                    },
                "return_codes": [200]
            }
    }


postgres_stages = [
    {
        "type": "Postgres",
        "params":
            {
                "connection": '"host=" + .host + " dbname=" + .dbname + " user=" + .username + " password=" + .password + " port=" + .port',
                "query": '"create table " + .table_name + " " + .table_params'
            }
    },
    {
        "type": "Postgres",
        "params":
            {
                "connection": '"host=" + .host + " dbname=" + .dbname + " user=" + .username + " password=" + .password + " port=" + .port',
                "query": '"insert into " + .table_name + " " + .insert_params + " values " + .table_values'
            }
    },
    {
        "type": "Postgres",
        "params":
            {
                "connection": '"host=" + .host + " dbname=" + .dbname + " user=" + .username + " password=" + .password + " port=" + .port',
                "query": '"select * from " + .table_name',
                "return_values":
                    {
                        "first": ".[0]",
                        "second": ".[1]"
                    }
            }
    }
]


def insert_pipeline(stages):
    pipeline_body = {
        "pipeline_name": "Test",
        "stages":
            stages
    }
    client.post("/pipeline", json=pipeline_body)


def insert_job(job_body):
    response = client.post("/job?pipeline_name=Test", json=job_body)
    return str(response.json())


@pytest.mark.container_test
def test_execute_post_pipeline():
    body_patterns = [
        {
            "equalToJson":
                {
                    'login': '3c',
                    'password': 'c3'
                },
            "ignoreArrayOrder": True
        }
    ]
    mappings = [
        (
            "hello-world.json",
            {
                "request": {"method": HttpMethods.POST, "url": "/fixed/1/fixed/cba?query1=2&query2=abc",
                            "bodyPatterns": body_patterns},
                "response": {"status": 200, "body": '{"hello": "hello"}'},
            },
        )
    ]

    body = {
        "path1": "1",
        "path2": "cba",
        "query1": "2",
        "query2": "abc",
        "login": "3c",
        "password": "c3"
    }

    with wiremock_container(mappings=mappings, verify_ssl_certs=False) as wm:
        insert_pipeline([get_http_post_stage(wm.get_url(""))])
        job_id = insert_job(body)
        database.stage_queue.execute()
        response = client.get("/job?job_id=" + job_id)
        response_value = response.json()
        assert response_value[0] == "Success"
        assert response_value[1]['stage_1'] == 'completed'
        assert response_value[1]["user_id"] == 'hello'


def test_postgres_pipeline():
    insert_pipeline(postgres_stages)
    postgres_test = PostgresContainer("postgres:16").start()
    body = {
        "host": postgres_test.get_container_host_ip(),
        "port": postgres_test.get_exposed_port(5432),
        "username": postgres_test.username,
        "password": postgres_test.password,
        "dbname": postgres_test.dbname,
        "table_name": "test",
        "table_params": "(id int, description text)",
        "insert_params": "(id, description)",
        "table_values": "(1, 'first'), (2, 'second')"
    }
    job_id = insert_job(body)
    database.stage_queue.execute()
    database.stage_queue.execute()
    database.stage_queue.execute()
    response = client.get("/job?job_id=" + job_id)
    response_value = response.json()
    assert response_value[0] == "Success"
    assert response_value[1]['stage_1'] == 'completed'
    assert response_value[1]['stage_2'] == 'completed'
    assert response_value[1]['stage_3'] == 'completed'
    assert response_value[1]["first"] == [1, 'first']
    assert response_value[1]["second"] == [2, 'second']
    postgres_test.stop()
