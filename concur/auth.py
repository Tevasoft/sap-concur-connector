"""
concur.auth — OAuth2 authentication for SAP Concur API v4.
concur._base — Base HTTP client with retry and pagination.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator, Optional
import httpx

DATACENTER_URLS = {
    "us": "https://us.api.concursolutions.com",
    "eu": "https://eu.api.concursolutions.com",
    "cn": "https://cn.api.concursolutions.com",
    "au": "https://au.api.concursolutions.com",
}


@dataclass
class TokenResponse:
    access_token: str
    refresh_token: str = ""
    token_type: str = "Bearer"
    expires_in: int = 3600
    scope: str = ""
    geolocation: str = ""
    issued_at: float = field(default_factory=time.time)

    @property
    def is_expired(self) -> bool:
        return time.time() > self.issued_at + self.expires_in - 60

    @property
    def base_url(self) -> str:
        return self.geolocation or ""


class ConcurAuth:
    """OAuth2 token manager for SAP Concur."""

    def __init__(self, client_id: str, client_secret: str, datacenter: str = "eu"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = DATACENTER_URLS.get(datacenter, DATACENTER_URLS["eu"])
        self._token: Optional[TokenResponse] = None

    def authenticate(self, username: str, password: str) -> TokenResponse:
        """Password grant — user credentials."""
        return self._post_token({
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": username,
            "password": password,
            "credtype": "authtoken",
        })

    def authenticate_company(self, company_token: str) -> TokenResponse:
        """Company JWT grant — server-to-server."""
        return self._post_token({
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "assertion": company_token,
        })

    def authenticate_client_credentials(self) -> TokenResponse:
        """OAuth2 client credentials grant."""
        return self._post_token({
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        })

    def refresh(self) -> TokenResponse:
        if not self._token or not self._token.refresh_token:
            raise RuntimeError("No refresh token — authenticate first.")
        return self._post_token({
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self._token.refresh_token,
        })

    def get_valid_token(self) -> TokenResponse:
        if self._token is None:
            raise RuntimeError("Not authenticated.")
        if self._token.is_expired:
            self.refresh()
        return self._token

    def auth_headers(self) -> dict[str, str]:
        t = self.get_valid_token()
        return {"Authorization": f"Bearer {t.access_token}",
                "Content-Type": "application/json", "Accept": "application/json"}

    def _post_token(self, data: dict) -> TokenResponse:
        resp = httpx.post(
            f"{self.base_url}/oauth2/v0/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        resp.raise_for_status()
        d = resp.json()
        self._token = TokenResponse(
            access_token=d["access_token"],
            refresh_token=d.get("refresh_token", ""),
            expires_in=d.get("expires_in", 3600),
            scope=d.get("scope", ""),
            geolocation=d.get("geolocation", self.base_url),
        )
        return self._token


class BaseResource:
    """Base class for all Concur API resource clients."""

    def __init__(self, auth: ConcurAuth, http: httpx.Client):
        self._auth = auth
        self._http = http

    @property
    def _base(self) -> str:
        return self._auth.get_valid_token().geolocation

    def _get(self, path: str, **params) -> dict:
        resp = self._http.get(
            f"{self._base}{path}",
            headers=self._auth.auth_headers(),
            params={k: v for k, v in params.items() if v is not None},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, json: dict | None = None) -> dict:
        resp = self._http.post(
            f"{self._base}{path}",
            headers=self._auth.auth_headers(),
            json=json or {},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def _put(self, path: str, json: dict) -> dict:
        resp = self._http.put(
            f"{self._base}{path}",
            headers=self._auth.auth_headers(),
            json=json,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def _delete(self, path: str) -> None:
        resp = self._http.delete(
            f"{self._base}{path}",
            headers=self._auth.auth_headers(),
            timeout=30,
        )
        resp.raise_for_status()

    def _paginate(self, path: str, item_key: str = "Items",
                  **params) -> Iterator[dict]:
        """Transparent pagination — yields individual items."""
        offset = 0
        limit = params.pop("limit", 100)
        while True:
            data = self._get(path, limit=min(limit, 100), offset=offset, **params)
            items = data.get(item_key, [])
            if not items:
                break
            yield from items
            if not data.get("NextPage"):
                break
            offset += len(items)

    def _get_bytes(self, path: str, accept: str = "*/*") -> bytes:
        resp = self._http.get(
            f"{self._base}{path}",
            headers={**self._auth.auth_headers(), "Accept": accept},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.content
