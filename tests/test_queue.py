from wiremock.testing.testcontainer import wiremock_container
from wiremock.resources.mappings import HttpMethods

from init_test import *
import database.stage_queue


def insert_pipeline_and_job(path):
    pipeline_body = {
        "pipeline_name": "Test",
        "stages":
            [
                {
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
            ]
    }
    client.post("/pipeline", json=pipeline_body)
    job_body = {
        "path1": "1",
        "path2": "cba",
        "query1": "2",
        "query2": "abc",
        "login": "3c",
        "password": "c3"
    }
    response = client.post("/job?pipeline_name=Test", json=job_body)
    return str(response.json())


@pytest.mark.container_test
def test_configure_via_wiremock_container_context_manager():
    mappings = [
        (
            "hello-world.json",
            {
                "request": {"method": HttpMethods.POST, "url": "/fixed/1/fixed/cba?query1=2&query2=abc"},
                "response": {"status": 200, "body": '{"hello": "hello"}'},
            },
        )
    ]

    with wiremock_container(mappings=mappings, verify_ssl_certs=False) as wm:
        job_id = insert_pipeline_and_job(wm.get_url(""))
        database.stage_queue.execute()
        response = client.get("/job?job_id=" + job_id)
        print(response.json())


# @insert_correct_pipeline
# @insert_correct_job
# @insert_correct_job
# def test_execute():
#     database.stage_queue.execute_all()
#     response = client.get("/job?job_id=1")
#     assert response.status_code == 200
#     assert response.json() == "Success"
#     response = client.get("/job?job_id=2")
#     assert response.status_code == 200
#     assert response.json() == "Success"
