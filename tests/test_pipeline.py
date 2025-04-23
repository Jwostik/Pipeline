from init_test import *
from models import Pipeline


def test_insert_empty_pipeline():
    with pytest.raises(Exception):
        response = client.post("/pipeline")
        assert response.status_code == 400
        assert response.json == "Invalid request"


def test_insert_pipeline_without_stages():
    body = {
        "pipeline_name": "Authorization",
        "stages": []}
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


def test_insert_correct_pipeline():
    response = client.post("/pipeline", json=correct_body)
    assert response.status_code == 200
    response = client.get("/pipeline?pipeline_name=Authorization")
    assert response.status_code == 200
    assert Pipeline.model_validate(response.json()) == Pipeline.model_validate(correct_body)


def test_insert_pipeline_with_same_name():
    client.post("/pipeline", json=correct_body)
    with pytest.raises(Exception):
        response = client.post("/pipeline", json=correct_body)
        assert response.status_code == 409
        assert response.json == "Name of pipeline has already used"


def test_get_non_existing_pipeline():
    response = client.get("/pipeline?pipeline_name=Authorization")
    assert response.status_code == 400
    assert response.json() == "Pipeline Authorization does not exist"
