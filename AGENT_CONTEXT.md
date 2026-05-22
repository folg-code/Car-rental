# Car Rental Operations Platform
## Full Project Description for Future AI Agent

# 1. Project Overview

This project is a Django-based web application for managing a small-to-medium car rental business.

The system is intended to be:
- an operational business platform,
- optimized for internal workflows,
- mobile-friendly,
- reliable,
- auditable,
- easy to extend incrementally.

Primary use case:
- approximately 15 vehicles,
- single business owner or small team,
- web-based operations,
- mobile handover/return workflows.

---

# 2. Technical Stack

## Backend
- Python
- Django
- PostgreSQL

## Frontend
- Django Templates
- HTML
- SCSS
- HTMX
- minimal JavaScript

## Infrastructure
- Docker Compose
- Gunicorn
- Caddy or Nginx
- VPS deployment

---

# 3. Project Structure

```text
apps/
  accounts/
  fleet/
  bookings/
  pricing/
  payments/
  operations/
  documents/
  dashboard/
  website/
```

---

# 4. Architectural Philosophy

The project follows:
- modular Django apps,
- service-layer architecture,
- selector/query separation,
- explicit business workflows,
- immutable historical snapshots.

Avoid:
- business logic inside templates,
- large fat views,
- hidden side effects,
- excessive signals,
- premature microservices.

---

# 5. Global Business Rules

## Availability is derived

Cars do NOT have:

```python
is_available = True
```

Availability is calculated from:
- reservations,
- rentals,
- service blocks,
- manual blocks.

---

## Reservation != Rental

Reservation:
- booking intent.

Rental:
- actual operational rental lifecycle.

Flow:

```text
Reservation -> Rental
```

---

## Payment != Invoice

Payment:
- money movement.

Invoice:
- accounting artifact.

---

## Deposit != Revenue

Deposits are liabilities.
Never count deposits as revenue.

---

## Historical Documents Are Immutable

Generated:
- PDFs,
- protocols,
- snapshots,
- pricing breakdowns

must never rebuild dynamically from current DB state.

---

# 6. App Descriptions

# accounts/

Responsibilities:
- authentication,
- permissions,
- user roles.

Models:
- User

Roles:
- owner
- manager
- employee
- accountant
- customer

---

# fleet/

Responsibilities:
- vehicle management,
- damage history,
- service records,
- availability blocks.

Models:
- Car
- CarCategory
- CarImage
- CarDocument
- AvailabilityBlock
- Damage
- DamagePhoto
- RepairRecord

Important:
Damage history is global and independent from protocols.
`CarCategory.deposit` — refundable deposit amount (PLN) per category; used for display until `payments` records actual deposit transactions.

---

# bookings/

Responsibilities:
- reservations,
- rentals,
- customers,
- pricing snapshots.

Models:
- Customer
- Reservation
- Rental
- PriceLine

Reservation statuses:
- draft
- pending_payment
- confirmed
- cancelled
- expired
- converted_to_rental

Reservation pricing modes (`pricing_mode`):
- `auto` — default price list for reservation start date
- `price_list` — explicit `PriceList` FK on reservation
- `custom` — manual `custom_total` → single immutable `PriceLine` (MANUAL)

Pricing snapshots:
- `PriceSnapshotService.freeze()` writes `PriceLine` rows (never recalculate confirmed reservations with existing lines)
- Panel: create/edit reservation selects pricing mode; detail shows breakdown and category deposit

Rental statuses:
- scheduled
- active
- returned
- closed
- cancelled

---

# pricing/

Responsibilities:
- pricing engine,
- dynamic pricing,
- discounts,
- surcharges,
- extra services.

Models:
- PriceList
- DailyRate
- PricingRule
- ExtraService

Examples:
- holiday surcharge,
- weekend surcharge,
- child seat,
- additional driver,
- cleaning fee,
- fuel refill,
- extra kilometers.

Implemented services:
- `PricingService.calculate()` — daily rate, rules (weekend/season/holiday), long-rental discount, extras; optional explicit `price_list`
- `PriceSnapshotService` lives in `bookings` (freeze only; pricing app does not FK to `Reservation`)

Panel:
- `/panel/cenniki/` — CRUD price lists, daily rates, rules, extra services

Important:
All pricing calculations must live in services.
Pricing app calculates only; `bookings.PriceLine` is the immutable snapshot at reservation time.

---

# payments/

Responsibilities:
- online payments,
- bank transfers,
- cash payments,
- deposits,
- refunds.

Models:
- PaymentIntent
- Payment
- Refund
- PaymentProviderEvent

Supported methods:
- online_gateway
- cash
- bank_transfer
- card
- blik

Supported payment types:
- rental_fee
- deposit
- refund
- extra_charge
- damage_charge

---

# operations/

Responsibilities:
- handover workflows,
- return workflows,
- signatures,
- operational photos,
- snapshots.

Models:
- HandoverProtocol
- ReturnProtocol
- ProtocolPhoto
- Signature
- DamageSnapshot

Mobile requirements:
- touch support,
- camera upload,
- responsive UI,
- tablet support.

Photo upload should support:

```html
<input type="file" accept="image/*" capture="environment">
```

---

# documents/

Responsibilities:
- PDF generation,
- invoice generation,
- email sending,
- encrypted PDFs,
- private storage.

Models:
- Document
- DocumentTemplate
- EmailLog
- Invoice
- InvoiceItem

Security requirements:
- encrypted PDFs,
- private media storage,
- audit logging.

---

# dashboard/

Responsibilities:
- operational metrics,
- financial metrics,
- alerts,
- occupancy metrics,
- operational overview.

Examples:
- active rentals,
- available cars,
- monthly revenue,
- upcoming returns,
- expiring insurance,
- unpaid rentals.

---

# website/

Responsibilities:
- customer-facing website,
- fleet listing,
- reservation flow,
- customer portal.

Customer capabilities:
- search available cars,
- create reservation,
- pay online,
- download documents,
- view reservation history.

### AI customer consultant (chatbot)

Public-facing **AI assistant** embedded in the website — helps customers before and during booking.

Capabilities (target):
- answer FAQ (warunki wynajmu, kaucja, dokumenty, godziny odbioru),
- help search available cars (dates → `AvailabilityService` + fleet selectors),
- explain pricing estimates (read-only via `PricingService` — no binding quote without reservation flow),
- guide user to reservation form (deep link with pre-filled dates/car),
- for logged-in customers: general status of own reservation (read-only via `bookings` selectors — no PII leakage to other users).

Out of scope for chatbot:
- creating or modifying reservations directly in chat (must go through `ReservationService` / form),
- processing payments,
- staff / internal operations,
- legal/tax/accounting advice beyond scripted policy snippets,
- access to other customers' data.

Architecture:
- UI and orchestration: `website` app,
- LLM provider: **adapter** (`website/adapters/llm.py`) — OpenAI / Anthropic / other via env,
- conversation persistence: `ChatSession`, `ChatMessage` models in `website` (audit + UX, not source of business truth),
- system prompt built from **curated context** (fleet categories, FAQ, policies) — never raw DB dump,
- rate limiting, session token (anonymous or linked to `User` with role `customer`).

See: [`docs/AI_CONSULTANT.md`](docs/AI_CONSULTANT.md).

---

# 7. Service Layer Architecture

Every major workflow should use services.

Examples:

```python
AvailabilityService
PricingService
ReservationService
RentalService
PaymentService
HandoverService
DocumentService
```

---

# 8. Pricing Philosophy

The system separates:

```text
Pricing -> what should be charged
Payments -> what was paid
Invoices -> what was invoiced
```

This separation is critical.

---

# 9. Operational Workflow

## Handover

1. Select rental
2. Enter mileage
3. Enter fuel level
4. Upload photos
5. Show active damages
6. Add new damages
7. Capture customer signature
8. Generate PDF
9. Send email

---

## Return

1. Enter return mileage
2. Enter return fuel
3. Compare damages
4. Add new damages
5. Calculate surcharges
6. Capture signature
7. Generate PDF

---

# 10. Dynamic Pricing

Supported:
- seasonal pricing,
- weekend pricing,
- holiday surcharges,
- long rental discounts,
- manual discounts.

Extra services:
- child seat,
- additional driver,
- fuel refill,
- cleaning fee,
- delivery fee,
- late return fee,
- extra kilometers.

---

# 11. Damage Snapshot Philosophy

At handover:
- active damages are loaded from DB,
- copied into snapshots,
- frozen historically.

This guarantees protocol integrity.

---

# 12. Deployment

Recommended production stack:

```text
VPS
Docker Compose
Gunicorn
Caddy/Nginx
PostgreSQL
```

---

# 13. Backups

Required:
- PostgreSQL backups,
- media backups,
- offsite backups,
- restore testing.

---

# 14. Security

Required:
- HTTPS,
- private media,
- encrypted PDFs,
- strong admin passwords,
- audit logs,
- secure uploads.

---

# 15. Development Philosophy

Build incrementally.

Recommended order:
1. fleet
2. bookings
3. pricing
4. payments
5. operations
6. documents
7. dashboard
8. website

Avoid building advanced integrations too early.

---

# 16. Final Priorities

Critical priorities:
1. Historical integrity
2. Pricing correctness
3. Availability correctness
4. Payment correctness
5. Mobile operational workflows
6. Simplicity
7. Auditability


---

# 17. Engineering Conventions

- Prefer explicit code over magic abstractions
- Avoid Django signals unless absolutely necessary
- Business logic belongs in services
- Queries/selectors should never mutate state
- Keep Django views thin
- Prefer service orchestration over fat models
- Prefer PostgreSQL features over custom implementations
- Use typed Python where reasonable
- Avoid premature optimization
- Avoid premature async architecture
- Maintain backward compatibility for historical records
- Prefer incremental migrations over large schema rewrites
- Prefer readability and auditability over clever abstractions
- Keep templates presentation-focused
- Avoid hidden side effects
- Avoid overengineering patterns from Java/C#
- Use Docker Compose for local development
- Write tests for critical business logic
- Prefer deterministic workflows

---

# 18. Preferred Technical Decisions

- Prefer Django Templates over SPA frontend
- Prefer HTMX over large JavaScript frameworks
- Prefer monolith architecture
- Avoid microservices
- Avoid GraphQL unless strongly justified
- Avoid repository pattern abstractions over Django ORM
- Avoid unnecessary Celery/Redis usage in early stages
- Prefer server-rendered workflows
- Prefer PostgreSQL as the primary source of truth
- Prefer explicit domain services
- Keep frontend JavaScript minimal
- Prefer TailwindCSS for UI consistency
- Optimize for maintainability and operational simplicity

---

# 19. Current Project Status

> Sprint tracking: [`PROJECT_PLAN.md`](./PROJECT_PLAN.md) — last updated 2026-05-20.

**Completed sprints:** 0 (fundament) · 1 (accounts + panel) · 2 (fleet) · 3 (bookings) · 4 (pricing + snapshots)

**Next sprint:** 5 — `Rental`, `Payment`, `convert_to_rental()`, deposit as liability (not revenue).

Implemented:
- Django project setup
- Docker Compose environment
- PostgreSQL integration
- TailwindCSS pipeline
- Pytest configuration
- Ruff + pre-commit setup
- Environment variable management
- Basic template structure
- accounts: User, roles, auth, panel access
- fleet: models, panel CRUD (`/panel/flota/`), category list + **edit** (`/kategorie/<id>/edycja/`), `CarCategory.deposit`, `AvailabilityService`
- bookings: Customer, Reservation, `PriceLine` snapshot, `ReservationService`, panel CRUD (`/panel/rezerwacje/`, clients under `/klienci/`)
- bookings: reservation pricing modes (`auto` / `price_list` / `custom`), `PriceSnapshotService.freeze()`, price breakdown on reservation detail
- pricing: `PriceList`, `DailyRate`, `PricingRule`, `ExtraService`, `PricingService.calculate()`, panel `/panel/cenniki/`
- dashboard: layout, navigation, bookings metrics on home
- CI/CD (GitHub Actions)
- `manage.py seed_demo` — fleet, customers, default price list, category deposits, sample reservation with price

In progress:
- (none)

Not implemented yet:
- `Rental` model and `ReservationService.convert_to_rental()`
- payments (`Payment`, `PaymentIntent`, deposit/refund recording; **deposit ≠ revenue**)
- operations workflows (handover/return protocols)
- documents system (PDF, invoices)
- dashboard (full operational metrics beyond current home widgets)
- customer-facing website (public booking channel)
- AI customer consultant (chatbot)

---

# 20. AI Agent Guidelines

When extending the system:

- Respect historical integrity
- Avoid introducing hidden state
- Prefer explicit workflows
- Avoid tightly coupling apps together
- Keep domain boundaries clear
- Prefer incremental changes
- Preserve auditability
- Do not introduce unnecessary abstractions
- Avoid replacing Django-native solutions without strong justification
- Favor operational correctness over premature feature complexity

When generating code:

- Keep implementations production-oriented
- Avoid placeholder architecture
- Avoid speculative abstractions
- Prefer practical and maintainable solutions
- Keep APIs explicit and predictable
- Ensure business rules are centralized and testable
