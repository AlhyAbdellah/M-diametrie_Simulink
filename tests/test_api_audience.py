import pytest

@pytest.mark.parametrize("file", [
    "audience_valid.json"
])
def test_add_audience_valid(client, load_data, file):
    for item in load_data(file):
        r = client.post("http://127.0.0.1:5002/audience/add", json=item)
        assert r.status_code == 201

@pytest.mark.parametrize("file", [
    "audience_invalid.json"
])
def test_add_audience_invalid(client, load_data, file):
    for item in load_data(file):
        r = client.post("http://127.0.0.1:5002/audience/add", json=item)
        assert r.status_code in (400, 422)
