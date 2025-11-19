import pytest

def test_status(client):
    r = client.get("http://127.0.0.1:5002/status")
    assert r.status_code == 200
    assert r.json()["api"] == "running"

@pytest.mark.parametrize("file", [
    "devices_valid.json"
])
def test_add_device_valid(client, load_data, file):
    for item in load_data(file):
        r = client.post("http://127.0.0.1:5002/device/add", json=item)
        assert r.status_code == 201

@pytest.mark.parametrize("file", [
    "devices_invalid.json"
])
def test_add_device_invalid(client, load_data, file):
    for item in load_data(file):
        r = client.post("http://127.0.0.1:5002/device/add", json=item)
        assert r.status_code in (400, 422)
