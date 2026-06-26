"""
concur.models — Typed Pydantic models for all SAP Concur API resources.
"""
from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class ApprovalStatus(str, Enum):
    NOT_SUBMITTED = "A_NOTF"; SUBMITTED = "A_FILE"; PENDING = "A_PEND"
    APPROVED = "A_APPR"; SENT_BACK = "A_RESU"; PENDING_COST = "A_PECO"

class PaymentStatus(str, Enum):
    NOT_PAID = "P_NOTP"; ON_HOLD = "P_HOLD"; PROCESSING = "P_PROC"; PAID = "P_PAID"

class ReimbursementMethod(str, Enum):
    ADP = "ADPPAYR"; AP_CHECK = "APCHECK"; CONCUR_PAY = "CNQRPAY"; OTHER = "PMTSERV"


# ---------------------------------------------------------------------------
# Expense Report
# ---------------------------------------------------------------------------
class ExpenseReport(BaseModel):
    id: str
    name: str
    total: Decimal = Decimal("0")
    currency_code: str = "EUR"
    approval_status_code: ApprovalStatus = ApprovalStatus.NOT_SUBMITTED
    payment_status_code: PaymentStatus = PaymentStatus.NOT_PAID
    report_date: Optional[date] = None
    submit_date: Optional[datetime] = None
    owner_login_id: str = ""
    owner_name: str = ""
    approver_login_id: Optional[str] = None
    amount_due_employee: Decimal = Decimal("0")
    amount_due_company_card: Decimal = Decimal("0")
    business_purpose: Optional[str] = None
    policy_id: Optional[str] = None
    ledger_name: Optional[str] = None
    last_modified_date: Optional[datetime] = None
    custom_fields: dict[str, Any] = Field(default_factory=dict)
    entries: list[ExpenseEntry] = Field(default_factory=list)

    @property
    def is_approved(self) -> bool:
        return self.approval_status_code == ApprovalStatus.APPROVED


class ExpenseEntry(BaseModel):
    id: str
    report_id: Optional[str] = None
    expense_type_code: str = ""
    expense_type_name: str = ""
    transaction_date: Optional[date] = None
    transaction_amount: Decimal = Decimal("0")
    transaction_currency_code: str = "EUR"
    approved_amount: Decimal = Decimal("0")
    report_currency_code: str = "EUR"
    exchange_rate: Optional[Decimal] = None
    vendor_description: Optional[str] = None
    location_name: Optional[str] = None
    location_country: Optional[str] = None
    comment: Optional[str] = None
    receipt_image_id: Optional[str] = None
    is_personal: bool = False
    vat_amount: Optional[Decimal] = None
    vat_rate: Optional[Decimal] = None
    cost_center: Optional[str] = None
    project_code: Optional[str] = None


class Allocation(BaseModel):
    id: str
    entry_id: str
    percentage: Decimal = Decimal("100")
    amount: Optional[Decimal] = None
    account_code: Optional[str] = None
    cost_center: Optional[str] = None
    project_code: Optional[str] = None
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class Attendee(BaseModel):
    id: str
    name: str
    title: Optional[str] = None
    company: Optional[str] = None
    attendee_type_code: Optional[str] = None
    amount: Optional[Decimal] = None
    currency_code: str = "EUR"


class ReceiptImage(BaseModel):
    id: str
    url: Optional[str] = None
    content_type: Optional[str] = None
    file_name: Optional[str] = None
    length_bytes: Optional[int] = None


# ---------------------------------------------------------------------------
# Travel / Itinerary
# ---------------------------------------------------------------------------
class TravelSegment(BaseModel):
    type: str                     # AIR, RAIL, CAR, HOTEL, ...
    origin: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    carrier: Optional[str] = None
    flight_number: Optional[str] = None
    booking_ref: Optional[str] = None
    seat: Optional[str] = None
    class_of_service: Optional[str] = None
    amount: Optional[Decimal] = None
    currency_code: str = "EUR"


class Itinerary(BaseModel):
    id: str
    trip_name: Optional[str] = None
    trip_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    destination: Optional[str] = None
    user_login_id: Optional[str] = None
    booking_source: Optional[str] = None
    segments: list[TravelSegment] = Field(default_factory=list)
    total_cost: Optional[Decimal] = None
    currency_code: str = "EUR"


class Trip(BaseModel):
    id: str
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    destination: Optional[str] = None
    purpose: Optional[str] = None
    booking_source: Optional[str] = None


# ---------------------------------------------------------------------------
# Users / Identity
# ---------------------------------------------------------------------------
class User(BaseModel):
    uuid: Optional[str] = None
    login_id: str
    display_name: str = ""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    active: bool = True
    country_code: Optional[str] = None
    currency_code: Optional[str] = None
    locale: Optional[str] = None
    department: Optional[str] = None
    manager_login_id: Optional[str] = None
    employee_id: Optional[str] = None
    cost_center: Optional[str] = None
    custom_fields: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Financial Integration
# ---------------------------------------------------------------------------
class JournalEntry(BaseModel):
    account_code: str
    account_name: Optional[str] = None
    debit: Optional[Decimal] = None
    credit: Optional[Decimal] = None
    currency: str = "EUR"
    cost_center: Optional[str] = None
    project_code: Optional[str] = None
    description: Optional[str] = None


class FinancialDocument(BaseModel):
    id: str
    report_id: str
    batch_id: Optional[str] = None
    document_date: Optional[date] = None
    currency_code: str = "EUR"
    total_amount: Decimal = Decimal("0")
    journal_entries: list[JournalEntry] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Lists
# ---------------------------------------------------------------------------
class ListItem(BaseModel):
    id: str
    name: str
    level: int = 1
    parent_id: Optional[str] = None
    external_id: Optional[str] = None


class ConcurList(BaseModel):
    id: str
    name: str
    display_format: Optional[str] = None
    items: list[ListItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Company Info
# ---------------------------------------------------------------------------
class CompanyInfo(BaseModel):
    id: str
    name: str
    default_currency: str = "EUR"
    default_locale: str = "fr-FR"
    issuer_id: Optional[str] = None


# Re-export for convenience
__all__ = [
    "ExpenseReport", "ExpenseEntry", "Allocation", "Attendee", "ReceiptImage",
    "Itinerary", "TravelSegment", "Trip",
    "User", "FinancialDocument", "JournalEntry",
    "ConcurList", "ListItem", "CompanyInfo",
    "ApprovalStatus", "PaymentStatus", "ReimbursementMethod",
]
