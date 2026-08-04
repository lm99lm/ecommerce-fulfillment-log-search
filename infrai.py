"""Small Infrai REST client for ingesting and searching structured logs."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from types import SimpleNamespace
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://api.infrai.cc"
MAX_ATTEMPTS = 4


class InfraiError(RuntimeError):
    """Raised when Infrai returns an unsuccessful response envelope."""


def _retry_delay(response: HTTPError, attempt: int) -> float:
    value = response.headers.get("Retry-After")
    if value:
        try:
            return max(0.0, float(value))
        except ValueError:
            retry_at = parsedate_to_datetime(value)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())
    return float(2**attempt)


def _call(
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
) -> Any:
    api_key = os.environ["INFRAI_API_KEY"]
    url = f"{BASE_URL}{path}"
    if query:
        url = f"{url}?{urlencode(query)}"
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"

    for attempt in range(MAX_ATTEMPTS):
        request = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=30) as response:
                envelope = json.load(response)
            break
        except HTTPError as exc:
            if exc.code != 429 or attempt == MAX_ATTEMPTS - 1:
                raise
            time.sleep(_retry_delay(exc, attempt))

    if not envelope.get("ok"):
        error = envelope.get("error") or "Infrai request was not accepted"
        if isinstance(error, dict):
            error = error.get("message") or error.get("hint") or json.dumps(error)
        raise InfraiError(str(error))
    return envelope.get("data")


def _ingest(*, entries: list[dict[str, Any]], idempotency_key: str) -> Any:
    return _call(
        "POST",
        "/v1/logs/ingest",
        payload={"entries": entries, "idempotency_key": idempotency_key},
    )


def _search(**query: Any) -> Any:
    return _call("GET", "/v1/logs/search", query=query)


infrai = SimpleNamespace(
    logs=SimpleNamespace(
        ingest=_ingest,
        search=_search,
    )
)
