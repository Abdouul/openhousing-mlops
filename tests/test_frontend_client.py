import pytest
import requests
from frontend.client import OpenHousingAPIError, OpenHousingClient

class FakeResponse:
    def __init__(self, body, status_code=200):
        self.body, self.status_code = body, status_code
    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")
    def json(self):
        if isinstance(self.body, Exception):
            raise self.body
        return self.body

class FakeSession:
    def __init__(self, response):
        self.response, self.calls = response, []
    def request(self, method, url, timeout, **kwargs):
        self.calls.append((method, url, timeout, kwargs))
        return self.response

def test_predict_returns_estimated_price():
    session = FakeSession(FakeResponse({"estimated_price_usd": 26771.15, "model_name": "XGBoost"}))
    client = OpenHousingClient("https://api.example/", session=session)
    result = client.predict({"rm": 6.5})
    assert result["estimated_price_usd"] == 26771.15
    assert session.calls[0][0:3] == ("POST", "https://api.example/predict", 90)

def test_health_returns_api_status():
    client = OpenHousingClient("https://api.example", session=FakeSession(FakeResponse({"status": "ok"})))
    assert client.health() == {"status": "ok"}

def test_http_error_is_mapped_to_readable_error():
    client = OpenHousingClient("https://api.example", session=FakeSession(FakeResponse({}, status_code=503)))
    with pytest.raises(OpenHousingAPIError, match="API indisponible"):
        client.health()

@pytest.mark.parametrize("body", [[], {"model_name": "XGBoost"}])
def test_invalid_prediction_response_is_rejected(body):
    client = OpenHousingClient("https://api.example", session=FakeSession(FakeResponse(body)))
    with pytest.raises(OpenHousingAPIError):
        client.predict({"rm": 6.5})
