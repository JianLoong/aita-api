from fastapi.testclient import TestClient

from main import API


api = API(use_test_db=True, update=False)


client = TestClient(api.app)


def test_ping():
    response = client.get("http://localhost/api/v2/ping")
    assert response.status_code == 200
    assert response.json() == {"details": "Pong"}


def test_health():
    response = client.get("http://localhost/api/v2/health")
    assert response.status_code == 200


def test_read_submission():
    response = client.get("http://localhost/api/v2/submission/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_read_submissions():
    response = client.get("http://localhost/api/v2/submissions")
    assert response.status_code == 200
    assert len(response.json()) == 10


def test_search_submission():
    response = client.get("http://localhost/api/v2/submissions")
    assert response.status_code == 200
    assert len(response.json()) == 10


def test_search_submission_by_submission_id():
    response = client.get(
        "http://localhost/api/v2/submisssions/search?submission_id=18wgvnk"
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_search_comment_by_submission_id():
    response = client.get(
        "http://localhost/api/v2/comments/search?submission_id=18wgvnk"
    )

    assert response.status_code == 200
    assert len(response.json()) == 224
