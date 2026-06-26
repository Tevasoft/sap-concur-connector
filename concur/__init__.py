"""
concur — Python client for the SAP Concur API.

Usage:
    from concur import ConcurClient
    client = ConcurClient(client_id=..., client_secret=..., company_token=..., datacenter="eu")
    for report in client.expense.reports.list(approval_status="A_APPR"):
        print(report.name)
"""
from __future__ import annotations
from typing import Optional
import httpx

from .auth import ConcurAuth
from .resources import (
    CompanyResource, ExpenseNamespace, FinancialResource,
    ListsResource, TravelNamespace, UsersResource,
)


class ConcurClient:
    """
    Synchronous SAP Concur API client.

    Args:
        client_id:      Concur OAuth2 application client ID.
        client_secret:  Concur OAuth2 application client secret.
        company_token:  Company JWT token (server-to-server auth). Optional if using user auth.
        datacenter:     "eu" | "us" | "cn" | "au"
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        company_token: Optional[str] = None,
        datacenter: str = "eu",
    ):
        self.auth = ConcurAuth(client_id, client_secret, datacenter)
        if company_token:
            self.auth.authenticate_company(company_token)
        self._http = httpx.Client(timeout=30)

        # Resource namespaces
        self.expense = ExpenseNamespace(self.auth, self._http)
        self.travel = TravelNamespace(self.auth, self._http)
        self.users = UsersResource(self.auth, self._http)
        self.financial = FinancialResource(self.auth, self._http)
        self.lists = ListsResource(self.auth, self._http)
        self.company = CompanyResource(self.auth, self._http)

    def authenticate(self, username: str, password: str) -> None:
        """Authenticate with user credentials (password grant)."""
        self.auth.authenticate(username, password)

    def close(self) -> None:
        self._http.close()

    def __enter__(self): return self
    def __exit__(self, *args): self.close()


__version__ = "0.1.0"
__all__ = ["ConcurClient"]
