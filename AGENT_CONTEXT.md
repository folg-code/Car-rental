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

Rental workflow:
- `RentalService.convert_from_reservation()` — only from `confirmed` + existing `PriceLine`; sets reservation to `converted_to_rental`
- `RentalService.start` / `mark_returned` / `close` / `cancel` (cancel only while `scheduled`)
- One rental per reservation (`OneToOne`); `deposit_amount` snapshot from `CarCategory` at conversion
- Availability: `BLOCKING_RENTAL_STATUSES` block the car; `converted_to_rental` reservation does **not** block (rental does)

Panel:
- `/panel/rezerwacje/wynajmy/` — list, detail, status actions
- „Utworz wynajem” on confirmed reservation detail

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
- PaymentIntent — prepared for online gateway (MVP: manual booking via `Payment`)
- Payment — FK `Rental` (required), optional `Reservation`, `PaymentIntent`
- PaymentProviderEvent — webhook log skeleton
- Refunds are `Payment` rows with `payment_type=refund` (no separate `Refund` model)

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

Implemented (Sprint 5 MVP):
- `PaymentService.record_payment`, `record_deposit`, `record_rental_fee`, `refund_deposit`
- Selectors: `get_rental_payment_summary`, `get_rental_revenue_total`, `get_rental_deposit_balance`
- `REVENUE_PAYMENT_TYPES` — rental_fee, extra_charge, damage_charge only (**deposit ≠ revenue**)
- Panel: `/panel/platnosci/`, `/panel/platnosci/wynajem/<id>/` (form + quick deposit/refund)
- Payment summary embedded on rental detail

Not implemented yet:
- `PaymentGatewayService`, live webhooks, online checkout

---

# operations/

**Product vision:** fully **paperless** field workflow — all protocols electronic; phone/tablet sufficient for complete handover and return (no paper, no separate tools). Roadmap: [`PROJECT_PLAN.md` — Roadmap operations (paperless)](./PROJECT_PLAN.md#roadmap--operations-paperless).

Responsibilities:
- handover workflows,
- return workflows,
- signatures,
- operational photos,
- snapshots.

Models (implemented):
- HandoverProtocol, ReturnProtocol (1:1 with Rental)
- ProtocolPhoto, Signature
- DamageSnapshot — frozen copy of fleet.Damage at protocol time; **never update** when fleet.Damage changes

Services:
- HandoverService.complete_handover → mileage/fuel, photos, signature, damage snapshots, RentalService.start
- ReturnService.complete_return → compare handover, new damages, surcharge notes, RentalService.mark_returned
- DamageSnapshotService

Panel: `/panel/operacje/` — pending handover/return queues; `/wydanie/<id>/`, `/zwrot/<id>/` (mobile forms)

### Target workflow — handover (release)

1. Open rental on phone (operations queue)
2. Start handover protocol
3. Enter mileage, fuel level, notes
4. Add vehicle photos
5. Mark damages (freeze existing + record new)
6. Customer finger signature
7. Generate PDF — **planned** (`documents`)
8. Auto-send email — **planned** (`documents`)
9. Auto `Rental` → **active** — **done**

### Target workflow — return

1. Open return (active rental)
2. Enter mileage, fuel, notes
3. Compare damages vs handover snapshots — snapshots **done**; rich comparison UI **planned**
4. Add new damages — **done**
5. Calculate surcharges (fuel/km/damage per price list) — **planned** (`pricing` + `payments`; notes only today)
6. Customer signature — **done**
7. Generate PDF — **planned** (`documents`)
8. Email to customer — **planned** (`documents`)
9. Close rental (`returned` / `closed` after settlement) — **partial** (`mark_returned` done; `close` after payments **planned**)

Mobile requirements:
- touch-friendly forms, `capture="environment"` on photo upload
- HTMX step-by-step workflow — backlog

Not implemented yet:
- PDF generation and email (documents app)
- automatic surcharge calculation and posting to payments
- side-by-side damage comparison UI
- full rental close after financial settlement

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
- Avoid unnecessary Celery/Redis usage in early stages *(MVP: sync email w Sprint 7; plan async: [`docs/DOCKER.md`](docs/DOCKER.md) — Celery + Redis dla powiadomień klient/pracownik, Sprint 9+)*
- Prefer server-rendered workflows
- Prefer PostgreSQL as the primary source of truth
- Prefer explicit domain services
- Keep frontend JavaScript minimal
- Prefer TailwindCSS for UI consistency
- Optimize for maintainability and operational simplicity

---

# 19. Current Project Status

> Sprint tracking: [`PROJECT_PLAN.md`](./PROJECT_PLAN.md) — last updated 2026-05-20.

**Completed sprints:** 0 (fundament) · 1 (accounts + panel) · 2 (fleet) · 3 (bookings) · 4 (pricing + snapshots) · 5 (rental + payments MVP) · 6 (operations — handover/return)

**Next sprint:** 7 — documents (PDF protokołów, faktury, email ze snapshotów).

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
- bookings: `Rental` model, `RentalService`, `ReservationService.convert_to_rental()`, panel `/panel/rezerwacje/wynajmy/`, rental blocks availability (not `converted_to_rental` reservation)
- pricing: `PriceList`, `DailyRate`, `PricingRule`, `ExtraService`, `PricingService.calculate()`, panel `/panel/cenniki/`
- payments: `Payment`, `PaymentIntent`, `PaymentProviderEvent`, `PaymentService`, panel `/panel/platnosci/`, deposit/refund with balance validation, **deposit ≠ revenue**
- operations: `HandoverProtocol`, `ReturnProtocol`, `ProtocolPhoto`, `Signature`, `DamageSnapshot`, `HandoverService` / `ReturnService`, panel `/panel/operacje/` (mobile-first, `capture="environment"`), handover → `RentalService.start`, return → `mark_returned`, **DamageSnapshot immutable** after fleet `Damage` edits
- dashboard: layout, navigation, bookings + rental metrics on home
- CI/CD (GitHub Actions)
- `manage.py seed_demo` — fleet, customers, price list, sample reservation + rental (scheduled)

In progress:
- (none)

Not implemented yet:
- documents system (PDF, invoices)
- payment gateway integration (webhooks, online checkout)
- dashboard (full operational KPIs beyond home widgets)
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
