from init_test import *


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
    post_response = client.post("/job?pipeline_name=Authorization", json=job_body)
    assert post_response.status_code == 200
    get_response = client.get(f"/job?job_id={post_response.json()}")
    assert get_response.status_code == 200
    get_response_value = get_response.json()
    assert get_response_value[0] == "Job Authorization waiting on stage 1"
    assert get_response_value[1] == job_body


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
        assert response.status_code == 400
        assert response.json == "Pipeline Authorization does not exist"


def test_status_job_without_query():
    with pytest.raises(Exception):
        response = client.get("/job")
        assert response.status_code == 400
        assert response.json == "No job_id in query"


def test_status_job_with_not_integer_id():
    with pytest.raises(Exception):
        response = client.get("/job?job_id=a")
        assert response.status_code == 400
        assert response.json == "job_id must be integer"


def test_status_non_existing_job():
    with pytest.raises(Exception):
        response = client.get("/job?job_id=1")
        assert response.status_code == 400
        assert response.json == "Job with id 1 does not exist"
