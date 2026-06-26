"""
concur.resources — Resource clients for all SAP Concur APIs.
"""
from __future__ import annotations
from datetime import date
from decimal import Decimal
from typing import Iterator, Optional
import httpx

from .auth import BaseResource, ConcurAuth
from .models import (
    Allocation, Attendee, CompanyInfo, ConcurList, FinancialDocument,
    ExpenseEntry, ExpenseReport, Itinerary, JournalEntry, ListItem,
    ReceiptImage, Trip, TravelSegment, User,
    ApprovalStatus, PaymentStatus,
)


def _d(v) -> Optional[Decimal]:
    try: return Decimal(str(v)) if v is not None else None
    except: return None

def _date(s) -> Optional[date]:
    if not s: return None
    try:
        from datetime import datetime
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).date()
    except: return None

def _dt(s):
    if not s: return None
    try:
        from datetime import datetime
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except: return None


# ---------------------------------------------------------------------------
# Expense Reports
# ---------------------------------------------------------------------------
class ExpenseReportsResource(BaseResource):
    """SAP Concur Expense Reports API v4"""

    def list(
        self,
        approval_status: Optional[str] = None,
        payment_status: Optional[str] = None,
        submit_date_after: Optional[str] = None,
        submit_date_before: Optional[str] = None,
        user: str = "ALL",
        limit: int = 100,
    ) -> Iterator[ExpenseReport]:
        """Iterate over expense reports with optional filters."""
        for item in self._paginate(
            "/api/v3.0/expense/reports",
            approvalStatusCode=approval_status,
            paymentStatusCode=payment_status,
            submitDateAfter=submit_date_after,
            submitDateBefore=submit_date_before,
            user=user,
            limit=limit,
        ):
            yield self._parse(item)

    def list_all(self, **kwargs) -> list[ExpenseReport]:
        return list(self.list(**kwargs))

    def get(self, report_id: str, user: str = "ALL") -> ExpenseReport:
        data = self._get(f"/api/v3.0/expense/reports/{report_id}", user=user)
        report = self._parse(data)
        report.entries = list(ExpenseEntriesResource(self._auth, self._http).list(report_id))
        return report

    def submit(self, report_id: str) -> dict:
        return self._post(f"/api/v4.0/expense/reports/{report_id}/submit")

    def recall(self, report_id: str) -> dict:
        return self._post(f"/api/v4.0/expense/reports/{report_id}/recall")

    def approve(self, report_id: str, comment: str = "") -> dict:
        return self._post(f"/api/v4.0/expense/reports/{report_id}/approve",
                          json={"comment": comment})

    def send_back(self, report_id: str, comment: str) -> dict:
        return self._post(f"/api/v4.0/expense/reports/{report_id}/sendBack",
                          json={"comment": comment})

    def _parse(self, d: dict) -> ExpenseReport:
        return ExpenseReport(
            id=d.get("ID") or d.get("ReportID", ""),
            name=d.get("Name", ""),
            total=_d(d.get("Total")) or Decimal("0"),
            currency_code=d.get("CurrencyCode", "EUR"),
            approval_status_code=ApprovalStatus(d.get("ApprovalStatusCode", "A_NOTF")),
            payment_status_code=PaymentStatus(d.get("PaymentStatusCode", "P_NOTP")),
            report_date=_date(d.get("UserDefinedDate")),
            submit_date=_dt(d.get("SubmitDate")),
            owner_login_id=d.get("OwnerLoginID", ""),
            owner_name=d.get("OwnerName", ""),
            approver_login_id=d.get("ApproverLoginID"),
            amount_due_employee=_d(d.get("AmountDueEmployee")) or Decimal("0"),
            amount_due_company_card=_d(d.get("AmountDueCompanyCard")) or Decimal("0"),
            business_purpose=d.get("BusinessPurpose"),
            policy_id=d.get("PolicyID"),
            ledger_name=d.get("LedgerName"),
            last_modified_date=_dt(d.get("LastModifiedDate")),
        )


# ---------------------------------------------------------------------------
# Expense Entries
# ---------------------------------------------------------------------------
class ExpenseEntriesResource(BaseResource):
    """SAP Concur Expense Entries API v4"""

    def list(self, report_id: str, user: str = "ALL") -> Iterator[ExpenseEntry]:
        for item in self._paginate("/api/v3.0/expense/entries",
                                   reportID=report_id, user=user):
            yield self._parse(item)

    def get(self, entry_id: str) -> ExpenseEntry:
        return self._parse(self._get(f"/api/v3.0/expense/entries/{entry_id}"))

    def _parse(self, d: dict) -> ExpenseEntry:
        return ExpenseEntry(
            id=d.get("ID", ""),
            report_id=d.get("ReportID"),
            expense_type_code=d.get("ExpenseTypeCode", ""),
            expense_type_name=d.get("ExpenseTypeName", ""),
            transaction_date=_date(d.get("TransactionDate")),
            transaction_amount=_d(d.get("TransactionAmount")) or Decimal("0"),
            transaction_currency_code=d.get("TransactionCurrencyCode", "EUR"),
            approved_amount=_d(d.get("ApprovedAmount")) or Decimal("0"),
            report_currency_code=d.get("ReportCurrencyCode", "EUR"),
            exchange_rate=_d(d.get("ExchangeRate")),
            vendor_description=d.get("VendorDescription"),
            location_name=d.get("LocationName"),
            comment=d.get("Comment"),
            receipt_image_id=d.get("ReceiptImageID"),
            is_personal=bool(d.get("IsPersonal", False)),
        )


# ---------------------------------------------------------------------------
# Allocations
# ---------------------------------------------------------------------------
class AllocationsResource(BaseResource):
    def list(self, report_id: str) -> Iterator[Allocation]:
        for item in self._paginate("/api/v3.0/expense/allocations", reportID=report_id):
            yield Allocation(
                id=item.get("ID", ""),
                entry_id=item.get("EntryID", ""),
                percentage=_d(item.get("Percentage")) or Decimal("100"),
                amount=_d(item.get("Amount")),
                account_code=item.get("AccountCode"),
                cost_center=item.get("Custom1", {}).get("Value") if isinstance(item.get("Custom1"), dict) else None,
            )


# ---------------------------------------------------------------------------
# Attendees
# ---------------------------------------------------------------------------
class AttendeesResource(BaseResource):
    def list(self, entry_id: str) -> Iterator[Attendee]:
        for item in self._paginate("/api/v3.0/expense/attendees", entryID=entry_id):
            yield Attendee(
                id=item.get("ID", ""),
                name=item.get("FullName", item.get("FirstName", "") + " " + item.get("LastName", "")),
                title=item.get("Title"),
                company=item.get("Company"),
                attendee_type_code=item.get("AttendeeTypeCode"),
                amount=_d(item.get("Amount")),
            )


# ---------------------------------------------------------------------------
# Receipts
# ---------------------------------------------------------------------------
class ReceiptsResource(BaseResource):
    def get_image(self, image_id: str) -> bytes:
        return self._get_bytes(
            f"/api/v3.0/expense/receiptimages/{image_id}",
            accept="image/jpeg, image/png, application/pdf"
        )

    def list_images(self, report_id: str) -> Iterator[ReceiptImage]:
        for item in self._paginate("/api/v3.0/expense/receiptimages", reportID=report_id):
            yield ReceiptImage(
                id=item.get("ID", ""),
                url=item.get("URI"),
                content_type=item.get("ContentType"),
            )


# ---------------------------------------------------------------------------
# Expense namespace
# ---------------------------------------------------------------------------
class ExpenseNamespace:
    def __init__(self, auth: ConcurAuth, http: httpx.Client):
        self.reports = ExpenseReportsResource(auth, http)
        self.entries = ExpenseEntriesResource(auth, http)
        self.allocations = AllocationsResource(auth, http)
        self.attendees = AttendeesResource(auth, http)
        self.receipts = ReceiptsResource(auth, http)


# ---------------------------------------------------------------------------
# Travel / Itineraries
# ---------------------------------------------------------------------------
class ItinerariesResource(BaseResource):
    def list(self, start_date: Optional[str] = None,
             end_date: Optional[str] = None) -> Iterator[Itinerary]:
        for item in self._paginate("/api/travel/v4/itineraries",
                                   startDate=start_date, endDate=end_date):
            yield self._parse(item)

    def get(self, itinerary_id: str) -> Itinerary:
        return self._parse(self._get(f"/api/travel/v4/itineraries/{itinerary_id}"))

    def _parse(self, d: dict) -> Itinerary:
        segs = []
        for s in d.get("Segments", []):
            segs.append(TravelSegment(
                type=s.get("Type", ""),
                origin=s.get("Origin") or s.get("DepartureCity"),
                destination=s.get("Destination") or s.get("ArrivalCity"),
                start_date=_dt(s.get("StartDateLocal") or s.get("DepartureDate")),
                end_date=_dt(s.get("EndDateLocal") or s.get("ArrivalDate")),
                carrier=s.get("Vendor") or s.get("AirlineCode"),
                flight_number=s.get("FlightNumber"),
                amount=_d(s.get("TotalCost")),
            ))
        return Itinerary(
            id=d.get("ID", d.get("ItineraryID", "")),
            trip_name=d.get("TripName"),
            start_date=_date(d.get("StartDateLocal")),
            end_date=_date(d.get("EndDateLocal")),
            destination=d.get("Destination"),
            user_login_id=d.get("UserLoginID"),
            booking_source=d.get("BookingSource"),
            segments=segs,
            total_cost=_d(d.get("TotalCost")),
        )


class TripsResource(BaseResource):
    def list(self, active: bool = True) -> Iterator[Trip]:
        for item in self._paginate("/api/travel/v4/trips",
                                   status="ACTIVE" if active else None):
            yield Trip(
                id=item.get("ID", ""),
                name=item.get("TripName"),
                start_date=_date(item.get("StartDateLocal")),
                end_date=_date(item.get("EndDateLocal")),
                destination=item.get("Destination"),
            )


class TravelNamespace:
    def __init__(self, auth: ConcurAuth, http: httpx.Client):
        self.itineraries = ItinerariesResource(auth, http)
        self.trips = TripsResource(auth, http)


# ---------------------------------------------------------------------------
# Users / Identity
# ---------------------------------------------------------------------------
class UsersResource(BaseResource):
    def list(self, active: Optional[bool] = None,
             country: Optional[str] = None) -> Iterator[User]:
        for item in self._paginate("/api/v3.0/common/users",
                                   isActive=active, country=country):
            yield self._parse(item)

    def get(self, user_id: str) -> User:
        return self._parse(self._get(f"/api/v3.0/common/users/{user_id}"))

    def get_by_login(self, login_id: str) -> Optional[User]:
        for item in self._paginate("/api/v3.0/common/users", loginId=login_id):
            return self._parse(item)
        return None

    def update(self, user_id: str, changes: dict) -> dict:
        return self._put(f"/api/v3.0/common/users/{user_id}", json=changes)

    def _parse(self, d: dict) -> User:
        return User(
            uuid=d.get("ID"),
            login_id=d.get("LoginID", ""),
            display_name=f"{d.get('FirstName', '')} {d.get('LastName', '')}".strip(),
            first_name=d.get("FirstName"),
            last_name=d.get("LastName"),
            email=d.get("EmailAddress"),
            active=bool(d.get("Active", True)),
            country_code=d.get("CountryCode"),
            currency_code=d.get("CurrencyCode"),
            locale=d.get("LocalCode"),
            department=d.get("OrgUnit1"),
            manager_login_id=d.get("ManagerLoginID"),
            employee_id=d.get("EmployeeID"),
        )


# ---------------------------------------------------------------------------
# Financial Integration
# ---------------------------------------------------------------------------
class FinancialResource(BaseResource):
    def get_documents(self, batch_id: Optional[str] = None) -> list[FinancialDocument]:
        params = {}
        if batch_id:
            params["batchID"] = batch_id
        data = self._get("/api/v4.0/financial/documents", **params)
        docs = []
        for item in data.get("Items", []):
            entries = []
            for je in item.get("JournalEntries", []):
                entries.append(JournalEntry(
                    account_code=je.get("AccountCode", ""),
                    account_name=je.get("AccountName"),
                    debit=_d(je.get("Debit")),
                    credit=_d(je.get("Credit")),
                    currency=je.get("CurrencyCode", "EUR"),
                    cost_center=je.get("CostCenter"),
                    project_code=je.get("ProjectCode"),
                    description=je.get("Description"),
                ))
            docs.append(FinancialDocument(
                id=item.get("ID", ""),
                report_id=item.get("ReportID", ""),
                batch_id=item.get("BatchID"),
                document_date=_date(item.get("DocumentDate")),
                currency_code=item.get("CurrencyCode", "EUR"),
                total_amount=_d(item.get("TotalAmount")) or Decimal("0"),
                journal_entries=entries,
            ))
        return docs


# ---------------------------------------------------------------------------
# Lists
# ---------------------------------------------------------------------------
class ListsResource(BaseResource):
    def list(self) -> Iterator[ConcurList]:
        for item in self._paginate("/api/v3.0/common/lists"):
            yield ConcurList(id=item.get("ID", ""), name=item.get("Name", ""))

    def get_items(self, list_id: str) -> Iterator[ListItem]:
        for item in self._paginate(f"/api/v3.0/common/listitems", listID=list_id):
            yield ListItem(
                id=item.get("ID", ""),
                name=item.get("Name", ""),
                level=item.get("Level", 1),
                parent_id=item.get("ParentID"),
            )


# ---------------------------------------------------------------------------
# Company Info
# ---------------------------------------------------------------------------
class CompanyResource(BaseResource):
    def get(self) -> CompanyInfo:
        d = self._get("/api/v1.1/company")
        return CompanyInfo(
            id=d.get("ID", ""),
            name=d.get("Name", ""),
            default_currency=d.get("DefaultCurrencyCode", "EUR"),
            default_locale=d.get("DefaultLanguageCode", "fr-FR"),
        )
