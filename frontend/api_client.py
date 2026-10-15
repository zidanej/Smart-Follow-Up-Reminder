import os
from typing import Any, Dict, List, Optional

import httpx

BASE_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
TIMEOUT = 8.0


class ApiError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def request(method: str, path: str, **kwargs: Any) -> Any:
    try:
        response = httpx.request(method, BASE_URL + path, timeout=TIMEOUT, **kwargs)
    except httpx.RequestError as exc:
        raise ApiError("The backend is unavailable. Start FastAPI and try again.") from exc
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", "Request failed")
        except ValueError:
            detail = "Request failed"
        if response.status_code == 422:
            raise ApiError("Please check the form values: %s" % detail, response.status_code)
        if response.status_code == 404:
            raise ApiError("The requested record was not found.", response.status_code)
        if response.status_code >= 500:
            raise ApiError("The backend encountered an internal error. Check the server logs and try again.", response.status_code)
        raise ApiError("Backend error (%s): %s" % (response.status_code, detail), response.status_code)
    if response.status_code == 204:
        return None
    try:
        return response.json()
    except ValueError as exc:
        raise ApiError("The backend returned an unexpected response.") from exc


def list_contacts(page: int = 1, page_size: int = 20, search: str = "", status: str = "", follow_up: str = "") -> Dict[str, Any]:
    params = {"page": page, "page_size": page_size}
    if search:
        params["search"] = search
    if status:
        params["status"] = status
    if follow_up:
        params["follow_up"] = follow_up
    return request("GET", "/api/v1/contacts", params=params)


def create_contact(payload: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
    headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
    return request("POST", "/api/v1/contacts", json=payload, headers=headers)


def get_contact(contact_id: int) -> Dict[str, Any]:
    return request("GET", "/api/v1/contacts/%s" % contact_id)


def update_contact(contact_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    return request("PATCH", "/api/v1/contacts/%s" % contact_id, json=payload)


def delete_contact(contact_id: int) -> bool:
    request("DELETE", "/api/v1/contacts/%s" % contact_id)
    return True


def create_interaction(contact_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    return request("POST", "/api/v1/contacts/%s/interactions" % contact_id, json=payload)


def list_interactions(contact_id: int) -> List[Dict[str, Any]]:
    return request("GET", "/api/v1/contacts/%s/interactions" % contact_id)


def dashboard_summary() -> Dict[str, Any]:
    return request("GET", "/api/v1/dashboard/summary")


def follow_ups(kind: str, days: int = 7) -> List[Dict[str, Any]]:
    path = "/api/v1/follow-ups/%s" % kind
    params = {"days": days} if kind == "upcoming" else {}
    return request("GET", path, params=params)
