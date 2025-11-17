import pytest, json, requests

BASE_URL = "http://127.0.0.1:5002"

@pytest.fixture(scope="session")
def load_data():
    def _load(file):
        with open(f"data/{file}", "r") as f:
            return json.load(f)
    return _load

@pytest.fixture
def client():
    return requests
