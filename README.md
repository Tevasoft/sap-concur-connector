# 🔗 sap-concur-python

> **The most complete Python client for the SAP Concur API** — covering Expense Reports v4, Travel Itineraries, Users, Receipts, Attendees, and more. OAuth2 out of the box, fully typed, async-ready.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)
[![SAP Concur API](https://img.shields.io/badge/SAP%20Concur-API%20v4-orange)]()
[![PyPI](https://img.shields.io/badge/PyPI-sap--concur--python-blue)]()

Built with ❤️ by [TEVASOFT](https://tevasoft.eu) — creators of [EVA](https://tevasoft.eu), the AI-powered expense audit & e-invoicing platform.

---

## Why this library?

The SAP Concur API is powerful but underdocumented for Python developers. This client provides:

- **Full OAuth2 lifecycle** — password grant, company JWT, client credentials, token refresh
- **All major APIs covered** — Expense Reports, Entries, Receipts, Travel, Users, Attendees, Allocations
- **Async support** — `AsyncConcurClient` for high-throughput pipelines
- **Pydantic models** — all API responses are typed and validated
- **Pagination handled** — iterators that transparently page through thousands of records
- **Multi-datacenter** — EU, US, CN, AU endpoints
- **CLI included** — `concur reports list`, `concur users get`, ...

---

## 🚀 Quick start

```bash
pip install sap-concur-python
```

```python
from concur import ConcurClient

client = ConcurClient(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    company_token="YOUR_COMPANY_TOKEN",  # server-to-server
    datacenter="eu",
)

# Fetch approved expense reports
for report in client.expense.reports.list(approval_status="A_APPR"):
    print(f"{report.id} | {report.name} | {report.total} {report.currency_code}")

# Get a single report with all its entries
report = client.expense.reports.get("REPORT_ID")
for entry in report.entries:
    print(f"  {entry.expense_type_name}: {entry.approved_amount} {entry.report_currency}")

# Download receipt images
image_bytes = client.expense.receipts.get_image("IMAGE_ID")

# List company users
for user in client.users.list(active=True):
    print(f"{user.login_id} — {user.display_name}")
```

---

## 📦 Resources covered

| Resource | API Version | Methods |
|----------|-------------|---------|
| Expense Reports | v4 | list, get, create, submit, recall |
| Expense Entries | v4 | list, get, create, update, delete |
| Expense Attendees | v4 | list, get |
| Expense Allocations | v4 | list |
| Receipt Images | v4 | get, upload, list |
| Travel Itineraries | v4 | list, get |
| Travel Trips | v4 | list |
| Users (Identity) | v4 | list, get, create, update |
| Company Info | v1.1 | get |
| Lists & List Items | v4 | list, get, create |
| Financial Integration | v4 | get_documents |

---

## 🔐 Authentication

### Company token (server-to-server) — recommended
```python
client = ConcurClient(
    client_id="...",
    client_secret="...",
    company_token="...",  # From your Concur admin
    datacenter="eu",
)
```

### User credentials
```python
client = ConcurClient(client_id="...", client_secret="...", datacenter="eu")
client.auth.authenticate(username="user@corp.com", password="...")
```

### Client credentials (OAuth2 machine-to-machine)
```python
client = ConcurClient(client_id="...", client_secret="...", datacenter="eu")
client.auth.authenticate_client_credentials()
```

---

## ⚡ Async support

```python
from concur import AsyncConcurClient

async with AsyncConcurClient(client_id="...", client_secret="...",
                              company_token="...", datacenter="eu") as client:
    reports = await client.expense.reports.list_async(approval_status="A_APPR")
    tasks = [client.expense.reports.get_async(r.id) for r in reports[:10]]
    full_reports = await asyncio.gather(*tasks)
```

---

## 🔁 Pagination

All `list()` methods return iterators — no manual offset handling needed:

```python
# Iterates through ALL approved reports automatically
for report in client.expense.reports.list(
    approval_status="A_APPR",
    submit_date_after="2026-01-01",
):
    process(report)

# Or fetch as a list (loads all into memory)
reports = client.expense.reports.list_all(
    approval_status="A_APPR",
    limit=1000,
)
```

---

## 🗂️ Expense resources

```python
# Reports
report = client.expense.reports.get("RPRT1234")
entries = client.expense.entries.list(report_id="RPRT1234")
allocations = client.expense.allocations.list(report_id="RPRT1234")
attendees = client.expense.attendees.list(entry_id="ENTRY_ID")

# Receipts
image_bytes = client.expense.receipts.get_image("IMG_ID")
images_meta = client.expense.receipts.list_images(report_id="RPRT1234")

# Submit a report
client.expense.reports.submit("RPRT1234")

# Recall (unsubmit)
client.expense.reports.recall("RPRT1234")
```

---

## 🧳 Travel resources

```python
# Itineraries
for trip in client.travel.itineraries.list(start_date="2026-01-01"):
    print(f"{trip.trip_name}: {trip.start_date} → {trip.end_date}")
    for segment in trip.segments:
        print(f"  {segment.type}: {segment.origin} → {segment.destination}")

# Trips
trips = client.travel.trips.list(active=True)
```

---

## 👥 User management

```python
# List active users
for user in client.users.list(active=True):
    print(f"{user.login_id}: {user.display_name} ({user.country_code})")

# Get specific user
user = client.users.get_by_login("jean.dupont@acme.fr")

# Update user
client.users.update(user.uuid, {"active": False})
```

---

## 💰 Financial Integration

```python
# Get financial documents for approved reports (for ERP posting)
docs = client.financial.get_documents(batch_id="BATCH_001")
for doc in docs:
    for line in doc.journal_entries:
        print(f"  {line.account_code}: {line.debit or line.credit} {line.currency}")
```

---

## 🖥️ CLI

```bash
# Reports
concur reports list --status approved --from 2026-01-01
concur reports get REPORT_ID
concur reports export --format csv --output reports.csv

# Entries
concur entries list --report REPORT_ID

# Users
concur users list --active
concur users get jean.dupont@acme.fr

# Auth
concur auth test  # verify credentials work
```

---

## 🏢 About TEVASOFT

[TEVASOFT](https://tevasoft.eu) builds **EVA**, an AI-powered platform for expense report audit and e-invoicing compliance for enterprise.

---

## 📄 License

Apache 2.0
