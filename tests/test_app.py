import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "healthy"}


def test_chat_success(client):
    res = client.post(
        "/api/chat", json={"message": "How can I manage my monthly budget?"}
    )
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data.get("response"), str)
    assert len(data["response"]) > 0


def test_chat_empty_message(client):
    res = client.post("/api/chat", json={"message": "   "})
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_chat_missing_message(client):
    res = client.post("/api/chat", json={"prompt": "Hello"})
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_chat_invalid_json(client):
    res = client.post(
        "/api/chat", data="{invalid_json", content_type="application/json"
    )
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_chat_excessively_long_message(client):
    res = client.post("/api/chat", json={"message": "A" * 501})
    assert res.status_code == 400
    assert "error" in res.get_json()


@pytest.mark.parametrize("bad_value", [12345, ["hello"], {"text": "hi"}, True, None])
def test_chat_unexpected_input_type(client, bad_value):
    res = client.post("/api/chat", json={"message": bad_value})
    assert res.status_code == 400
    assert "error" in res.get_json()
