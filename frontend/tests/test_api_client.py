import httpx
import pytest

from frontend.api_client import ApiError, request


def test_server_errors_are_sanitized(monkeypatch):
    class FakeResponse:
        status_code = 500

        @staticmethod
        def json():
            return {"detail": "secret database credentials"}

    monkeypatch.setattr(httpx, "request", lambda *args, **kwargs: FakeResponse())
    with pytest.raises(ApiError, match="internal error") as error:
        request("GET", "/health")
    assert "secret" not in str(error.value)


def test_connection_errors_are_user_friendly(monkeypatch):
    def fail(*args, **kwargs):
        raise httpx.ConnectError("connection refused", request=httpx.Request("GET", "http://backend"))

    monkeypatch.setattr(httpx, "request", fail)
    with pytest.raises(ApiError, match="backend is unavailable"):
        request("GET", "/health")
