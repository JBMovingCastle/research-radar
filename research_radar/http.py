from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class HttpFailure(RuntimeError):
    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


@dataclass(slots=True)
class HttpResponse:
    body: bytes
    status: int
    headers: dict[str, str]


class HttpClient:
    def __init__(self, timeout: int = 20, max_retries: int = 1, user_agent: str = "research-radar/0.1.1") -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent
        self.request_count = 0

    def request(
        self,
        url: str,
        *,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        data: bytes | None = None,
    ) -> HttpResponse:
        merged_headers = {"User-Agent": self.user_agent, "Accept": "*/*"}
        merged_headers.update(headers or {})
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            self.request_count += 1
            request = urllib.request.Request(url, data=data, headers=merged_headers, method=method)
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return HttpResponse(
                        body=response.read(),
                        status=getattr(response, "status", 200),
                        headers={key.lower(): value for key, value in response.headers.items()},
                    )
            except urllib.error.HTTPError as exc:
                last_error = exc
                retryable = exc.code == 429 or 500 <= exc.code < 600
                if not retryable or attempt >= self.max_retries:
                    raise HttpFailure(f"HTTP {exc.code} for {url}", exc.code) from exc
                retry_after = exc.headers.get("Retry-After", "") if exc.headers else ""
                delay = min(float(retry_after), 5.0) if retry_after.replace(".", "", 1).isdigit() else min(2**attempt, 5)
                time.sleep(delay)
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    raise HttpFailure(f"Network error for {url}: {exc}") from exc
                time.sleep(min(2**attempt, 5))
        raise HttpFailure(str(last_error or "request failed"))

    def get_json(self, url: str, *, headers: dict[str, str] | None = None) -> dict[str, Any]:
        response = self.request(url, headers={"Accept": "application/json", **(headers or {})})
        try:
            return json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HttpFailure(f"Invalid JSON from {url}") from exc

    def post_json(self, url: str, payload: dict[str, Any], *, headers: dict[str, str] | None = None) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        merged = {"Content-Type": "application/json", "Accept": "application/json", **(headers or {})}
        response = self.request(url, method="POST", headers=merged, data=data)
        try:
            return json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HttpFailure(f"Invalid JSON from {url}") from exc
