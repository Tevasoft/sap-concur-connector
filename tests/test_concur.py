"""
Tests for sap-concur-python — all HTTP calls are mocked.
"""
from __future__ import annotations
import json
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest

from concur import ConcurClient
from concur.auth import ConcurAuth, TokenResponse
from concur.models import (
    ApprovalStatus, ExpenseEntry, ExpenseReport,
    PaymentStatus, User, Itinerary,
)
from concur.resources import (
    ExpenseReportsResource, ExpenseEntriesResource,
    UsersResource, AttendeesResource, AllocationsResource,
)


# ---------------------------------------------------------------------------
# Auth tests
# ---------------------------------------------------------------------------
class TestConcurAuth:
    def _auth(self):
        return ConcurAuth("CID", "SECRET", datacenter="eu")

    def test_auth_headers_raise_without_token(self):
        auth = self._auth()
        with pytest.raises(RuntimeError, match="Not authenticated"):
            auth.auth_headers()

    def test_token_not_expired_when_fresh(self):
        import time
        token = TokenResponse(
            access_token="tok", expires_in=3600, issued_at=time.time()
        )
        assert not token.is_expired

    def test_token_expired(self):
        token = TokenResponse(
            access_token="tok", expires_in=60, issued_at=0
        )
        assert token.is_expired

    def test_bearer_header_format(self):
        import time
        auth = self._auth()
        auth._token = TokenResponse(
            access_token="MY_ACCESS_TOKEN", expires_in=3600, issued_at=time.time(),
            geolocation="https://eu.api.concursolutions.com",
        )
        headers = auth.auth_headers()
        assert headers["Authorization"] == "Bearer MY_ACCESS_TOKEN"
        assert "Content-Type" in headers


# ---------------------------------------------------------------------------
# Report parsing
# ---------------------------------------------------------------------------
class TestExpenseReportParsing:
    def _resource(self):
        auth = MagicMock()
        http = MagicMock()
        return ExpenseReportsResource(auth, http)

    def _sample(self):
        return {
            "ID": "RPT001",
            "Name": "Mission Paris",
            "Total": "155.00",
            "CurrencyCode": "EUR",
            "ApprovalStatusCode": "A_APPR",
            "PaymentStatusCode": "P_NOTP",
            "UserDefinedDate": "2026-05-15T00:00:00",
            "OwnerLoginID": "j.dupont@acme.fr",
            "OwnerName": "Jean Dupont",
            "AmountDueEmployee": "155.00",
            "AmountDueCompanyCard": "0",
            "BusinessPurpose": "Client visit",
        }

    def test_parse_report(self):
        r = self._resource()._parse(self._sample())
        assert r.id == "RPT001"
        assert r.name == "Mission Paris"
        assert r.total == Decimal("155.00")
        assert r.currency_code == "EUR"
        assert r.approval_status_code == ApprovalStatus.APPROVED
        assert r.is_approved is True
        assert r.owner_login_id == "j.dupont@acme.fr"

    def test_parse_report_date(self):
        r = self._resource()._parse(self._sample())
        assert r.report_date == date(2026, 5, 15)

    def test_parse_amounts(self):
        r = self._resource()._parse(self._sample())
        assert r.amount_due_employee == Decimal("155.00")
        assert r.amount_due_company_card == Decimal("0")

    def test_not_approved_report(self):
        d = self._sample()
        d["ApprovalStatusCode"] = "A_PEND"
        r = self._resource()._parse(d)
        assert not r.is_approved


# ---------------------------------------------------------------------------
# Entry parsing
# ---------------------------------------------------------------------------
class TestExpenseEntryParsing:
    def _resource(self):
        return ExpenseEntriesResource(MagicMock(), MagicMock())

    def _sample(self):
        return {
            "ID": "ENTRY001",
            "ReportID": "RPT001",
            "ExpenseTypeCode": "HOTEL",
            "ExpenseTypeName": "Hotel",
            "TransactionDate": "2026-05-10T00:00:00",
            "TransactionAmount": "120.00",
            "TransactionCurrencyCode": "EUR",
            "ApprovedAmount": "120.00",
            "ReportCurrencyCode": "EUR",
            "VendorDescription": "Ibis Paris",
            "IsPersonal": False,
        }

    def test_parse_entry(self):
        e = self._resource()._parse(self._sample())
        assert e.id == "ENTRY001"
        assert e.expense_type_code == "HOTEL"
        assert e.transaction_amount == Decimal("120.00")
        assert e.vendor_description == "Ibis Paris"
        assert e.is_personal is False

    def test_parse_entry_date(self):
        e = self._resource()._parse(self._sample())
        assert e.transaction_date == date(2026, 5, 10)

    def test_personal_entry(self):
        d = self._sample()
        d["IsPersonal"] = True
        e = self._resource()._parse(d)
        assert e.is_personal is True


# ---------------------------------------------------------------------------
# User parsing
# ---------------------------------------------------------------------------
class TestUserParsing:
    def _resource(self):
        return UsersResource(MagicMock(), MagicMock())

    def _sample(self):
        return {
            "ID": "uuid-001",
            "LoginID": "j.dupont@acme.fr",
            "FirstName": "Jean",
            "LastName": "Dupont",
            "EmailAddress": "j.dupont@acme.fr",
            "Active": True,
            "CountryCode": "FR",
            "CurrencyCode": "EUR",
            "EmployeeID": "EMP001",
        }

    def test_parse_user(self):
        u = self._resource()._parse(self._sample())
        assert u.login_id == "j.dupont@acme.fr"
        assert u.display_name == "Jean Dupont"
        assert u.active is True
        assert u.country_code == "FR"
        assert u.employee_id == "EMP001"


# ---------------------------------------------------------------------------
# Pagination helper
# ---------------------------------------------------------------------------
class TestPagination:
    def test_paginate_single_page(self):
        auth = MagicMock()
        auth.get_valid_token.return_value = MagicMock(geolocation="https://eu.api.concursolutions.com")
        auth.auth_headers.return_value = {"Authorization": "Bearer tok"}

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "Items": [{"ID": "R1"}, {"ID": "R2"}],
            "NextPage": None,
        }

        http = MagicMock()
        http.get.return_value = mock_resp

        resource = ExpenseReportsResource(auth, http)
        items = list(resource._paginate("/api/v3.0/expense/reports"))
        assert len(items) == 2
        assert items[0]["ID"] == "R1"

    def test_paginate_empty(self):
        auth = MagicMock()
        auth.get_valid_token.return_value = MagicMock(geolocation="https://eu.api.concursolutions.com")
        auth.auth_headers.return_value = {"Authorization": "Bearer tok"}

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"Items": [], "NextPage": None}

        http = MagicMock()
        http.get.return_value = mock_resp

        resource = ExpenseReportsResource(auth, http)
        items = list(resource._paginate("/api/v3.0/expense/reports"))
        assert items == []


# ---------------------------------------------------------------------------
# Model properties
# ---------------------------------------------------------------------------
class TestModels:
    def test_expense_report_is_approved(self):
        r = ExpenseReport(
            id="R1", name="Test",
            approval_status_code=ApprovalStatus.APPROVED,
            payment_status_code=PaymentStatus.NOT_PAID,
            owner_login_id="u@c.fr",
        )
        assert r.is_approved

    def test_expense_report_not_approved(self):
        r = ExpenseReport(
            id="R1", name="Test",
            approval_status_code=ApprovalStatus.PENDING,
            payment_status_code=PaymentStatus.NOT_PAID,
            owner_login_id="u@c.fr",
        )
        assert not r.is_approved

    def test_expense_entry_fields(self):
        e = ExpenseEntry(
            id="E1", expense_type_code="TAXI",
            transaction_amount=Decimal("35.00"),
            approved_amount=Decimal("35.00"),
        )
        assert e.expense_type_code == "TAXI"
        assert not e.is_personal

    def test_user_fields(self):
        u = User(login_id="j@acme.fr", display_name="Jean",
                 active=True, country_code="FR")
        assert u.active
        assert u.country_code == "FR"

    def test_itinerary_fields(self):
        it = Itinerary(id="IT1", trip_name="Paris London", segments=[])
        assert it.trip_name == "Paris London"
        assert it.segments == []
