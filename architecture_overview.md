# Car Rental Platform — Architecture Overview

# 1. System Overview

The project is a Django-based modular monolith designed for managing car rental operations.

Primary goals:
- operational reliability,
- auditability,
- maintainability,
- mobile-friendly workflows,
- explicit business logic,
- incremental scalability.

The platform is intended for:
- small-to-medium rental companies,
- internal operational usage,
- customer reservation workflows,
- future extension without architectural rewrites.

---

# 2. High-Level Architecture

```text
┌────────────────────────────────────────────┐
│                 Browser                    │
│      Django Templates + HTMX + CSS        │
└────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────┐
│                 Django Views               │
│          Request / Response Layer          │
└────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────┐
│           Services / Workflows             │
│     Business Logic + Transactions          │
└────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────┐
│              Django ORM Models             │
│          PostgreSQL Persistence            │
└────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────┐
│                PostgreSQL                  │
└────────────────────────────────────────────┘
```

---

# 3. Architectural Philosophy

The project follows:
- modular monolith architecture,
- explicit workflows,
- service-layer orchestration,
- Django-native patterns,
- server-rendered frontend,
- minimal JavaScript usage.

The architecture intentionally avoids:
- premature microservices,
- overengineered abstractions,
- repository pattern layers,
- frontend SPA complexity,
- hidden state mutations.

---

# 4. Core Architectural Principles

## Explicit Over Implicit

Business workflows should be visible and predictable.

Preferred:

```python
ReservationService.confirm_reservation()
```

Avoid:
- Django signals for core logic,
- hidden side effects,
- implicit mutations.

---

## Service Layer Architecture

Business logic belongs in services.

Services handle:
- workflow orchestration,
- transactions,
- pricing,
- reservations,
- operational flows,
- payment coordination.

Views should remain thin.

---

## Query/Mutation Separation

Selectors:
- readonly queries,
- filtering,
- aggregations,
- ORM optimization.

Services:
- state changes,
- workflow execution,
- persistence.

This improves maintainability and debugging.

---

## Historical Integrity

Historical operational records must never mutate retroactively.

Examples:
- pricing snapshots,
- rental protocols,
- generated PDFs,
- invoices,
- damage snapshots.

Historical documents are immutable.

---

# 5. Technology Stack

# Backend

- Python
- Django
- PostgreSQL

# Frontend

- Django Templates
- HTMX
- TailwindCSS
- minimal JavaScript

# Infrastructure

- Docker Compose
- Gunicorn
- Nginx/Caddy
- VPS deployment

---

# 6. Application Structure

```text
backend/
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

  common/
  config/
  templates/
  static/
  media/
```

---

# 7. Domain Applications

# accounts/

Responsibilities:
- authentication,
- permissions,
- user roles.

---

# fleet/

Responsibilities:
- vehicle management,
- damage history,
- service records,
- availability blocks.

Core entities:
- Car
- Damage
- AvailabilityBlock
- RepairRecord

---

# bookings/

Responsibilities:
- reservations,
- rentals,
- customers,
- booking workflows.

Core entities:
- Reservation
- Rental
- Customer

---

# pricing/

Responsibilities:
- pricing engine,
- discounts,
- surcharges,
- extra services.

Core concepts:
- seasonal pricing,
- holiday surcharges,
- additional services,
- pricing snapshots.

---

# payments/

Responsibilities:
- online payments,
- deposits,
- refunds,
- payment tracking.

Core concepts:
- Payment
- Refund
- Deposit
- PaymentIntent

---

# operations/

Responsibilities:
- handover workflows,
- return workflows,
- signatures,
- operational photos.

Mobile-first operational domain.

---

# documents/

Responsibilities:
- PDF generation,
- invoices,
- email delivery,
- private document storage.

---

# dashboard/

Responsibilities:
- operational overview,
- occupancy metrics,
- financial indicators,
- alerts.

---

# website/

Responsibilities:
- customer-facing website,
- reservation flow,
- fleet browsing,
- customer portal.

---

# 8. Layered Architecture

# Request Layer

Responsible for:
- HTTP requests,
- forms,
- template rendering,
- authentication,
- permissions.

Components:
- Django Views
- Django Forms
- HTMX endpoints

---

# Business Layer

Responsible for:
- workflows,
- orchestration,
- business rules,
- transactions.

Components:
- services,
- workflow orchestration.

Example:

```python
RentalService.start_rental()
PricingService.calculate_total()
```

---

# Persistence Layer

Responsible for:
- ORM models,
- database persistence,
- constraints,
- indexes.

Components:
- Django ORM
- PostgreSQL

---

# 9. HTMX Frontend Philosophy

The frontend architecture prioritizes:
- server-rendered UI,
- progressive enhancement,
- minimal JavaScript,
- operational simplicity.

HTMX is used for:
- partial updates,
- modals,
- dynamic tables,
- inline actions.

Avoid:
- frontend state duplication,
- SPA architecture,
- complex client-side stores.

---

# 10. Pricing Architecture

Pricing is intentionally separated from payments.

```text
Pricing -> What should be charged
Payments -> What was paid
Invoices -> Accounting artifact
```

This separation prevents accounting inconsistencies.

---

# 11. Availability Architecture

Vehicle availability is calculated dynamically.

Availability derives from:
- reservations,
- active rentals,
- maintenance blocks,
- manual blocks.

Avoid:

```python
car.is_available = True
```

Availability is computed, not stored.

---

# 12. Operational Workflow Architecture

# Reservation Flow

```text
Customer Request
    ↓
Reservation
    ↓
Payment
    ↓
Confirmation
    ↓
Rental Creation
```

---

# Rental Lifecycle

```text
Scheduled
    ↓
Handover
    ↓
Active Rental
    ↓
Return
    ↓
Closed
```

---

# Handover Workflow

```text
Mileage
Fuel
Photos
Damage Snapshot
Signature
PDF Generation
Email Delivery
```

---

# 13. Media & Document Handling

Operational media:
- photos,
- PDFs,
- signatures,
- invoices.

Requirements:
- private storage,
- immutable snapshots,
- secure uploads,
- audit logging.

---

# 14. Security Principles

Required:
- HTTPS,
- strong authentication,
- audit logging,
- private media storage,
- CSRF protection,
- secure file uploads.

Avoid:
- public operational documents,
- mutable historical records,
- hidden permissions.

---

# 15. Deployment Architecture

Recommended production stack:

```text
Internet
    ↓
Nginx / Caddy
    ↓
Gunicorn
    ↓
Django Application
    ↓
PostgreSQL
```

Docker Compose orchestrates:
- app container,
- database,
- reverse proxy.

---

# 16. Development Philosophy

The system should evolve incrementally.

Recommended implementation order:
1. fleet
2. bookings
3. pricing
4. payments
5. operations
6. documents
7. dashboard
8. website

Focus on:
- correctness,
- workflows,
- operational usability,
- maintainability.

Avoid:
- speculative abstractions,
- premature scaling optimizations,
- unnecessary async infrastructure.

---

# 17. Testing Strategy

Testing priority:
1. services
2. pricing logic
3. availability logic
4. workflows
5. permissions
6. views

Critical domains requiring strong tests:
- pricing,
- availability,
- payment handling,
- operational workflows.

---

# 18. Long-Term Scalability

The modular monolith structure allows:
- clear domain separation,
- future extraction if necessary,
- independent domain evolution,
- maintainable code organization.

The project intentionally optimizes for:
- operational simplicity,
- maintainability,
- auditability,
- predictable workflows.

Not for:
- premature distributed systems,
- hyper-scale architecture,
- unnecessary infrastructure complexity.

---

# 19. Final Architectural Priorities

Highest priorities:
1. Historical integrity
2. Pricing correctness
3. Availability correctness
4. Operational simplicity
5. Auditability
6. Maintainability
7. Mobile usability

The architecture should remain:
- Django-native,
- explicit,
- predictable,
- production-oriented,
- easy to reason about,
- easy to debug.
