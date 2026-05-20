# Architektura backendu

Platforma operacyjna wynajmu samochodów — monolit Django z podziałem na aplikacje domenowe.

Szczegóły biznesowe i reguły globalne: [`../AGENT_CONTEXT.md`](../AGENT_CONTEXT.md)  
Plan sprintów i postęp: [`../PROJECT_PLAN.md`](../PROJECT_PLAN.md)

---

## Zasady globalne

| Zasada | Opis |
|--------|------|
| Warstwa serwisów | Mutacje i workflow w `services/`; widoki i admin tylko orkiestrują |
| Selektory | Odczyt w `selectors/` — bez efektów ubocznych |
| Dostępność | Wyliczana z rezerwacji, wynajmów i blokad — brak `Car.is_available` |
| Rezerwacja ≠ wynajem | `Reservation` → konwersja → `Rental` |
| Cena ≠ płatność ≠ faktura | Osobne aplikacje: `pricing`, `payments`, `documents` |
| Kaucja ≠ przychód | Depozyty to zobowiązania (`payments`) |
| Historia niemutowalna | Snapshoty, PDF, `PriceLine` — nie przebudowywać z live DB |

---

## Struktura katalogów

```text
backend/
├── config/                 # settings, root urls, wsgi/asgi
├── apps/
│   ├── accounts/           # użytkownicy, role, uprawnienia
│   ├── fleet/              # pojazdy, szkody, blokady dostępności
│   ├── bookings/           # klienci, rezerwacje, wynajmy, PriceLine
│   ├── pricing/            # cenniki, reguły, kalkulacja opłat
│   ├── payments/           # płatności, kaucje, zwroty, bramka
│   ├── operations/         # protokoły wydania/zwrotu, podpisy
│   ├── documents/          # PDF, faktury, email, storage
│   ├── dashboard/          # panel wewnętrzny, metryki, alerty
│   └── website/            # strona publiczna, rezerwacja online
├── templates/              # szablony globalne (base, layout wewnętrzny)
└── static/
```

Każda aplikacja:

```text
apps/<nazwa>/
├── README.md       # granice odpowiedzialności (co robi / czego nie robi)
├── apps.py
├── models.py
├── admin.py
├── views.py
├── urls.py
├── tests.py
├── services/       # logika mutująca, workflow
├── selectors/      # zapytania read-only
└── migrations/
```

---

## Mapa aplikacji i zależności

```text
                    ┌─────────────┐
                    │  accounts   │
                    └──────┬──────┘
                           │ auth / permissions
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
   ┌──────────┐     ┌───────────┐     ┌──────────┐
   │  fleet   │◄────│ bookings  │────►│ pricing  │
   └────┬─────┘     └─────┬─────┘     └──────────┘
        │                 │
        │           ┌─────▼─────┐
        │           │ payments  │
        │           └─────┬─────┘
        │                 │
        └────────►┌───────▼───────┐     ┌───────────┐
                  │  operations   │────►│ documents │
                  └───────┬───────┘     └───────────┘
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
        ┌───────────┐           ┌──────────┐
        │ dashboard │           │ website  │
        └───────────┘           └──────────┘
```

**Kierunek zależności:** aplikacja wyżej może wywoływać publiczne serwisy/selektory aplikacji niżej; unikać importów cyklicznych i logiki biznesowej w `models.py` / szablonach.

---

## Planowane prefiksy URL (Sprint 1+)

| Aplikacja | Prefix | Użytkownik |
|-----------|--------|------------|
| `website` | `/` | Klient / publiczny |
| `dashboard` | `/panel/` | Pracownik / właściciel |
| `fleet` | `/panel/flota/` | Wewnętrzny |
| `bookings` | `/panel/rezerwacje/` | Wewnętrzny |
| `operations` | `/panel/operacje/` | Wewnętrzny (mobile-first) |
| `payments` | `/panel/platnosci/` | Wewnętrzny |
| `documents` | `/panel/dokumenty/` | Wewnętrzny |
| `accounts` | `/konto/` | Wszyscy zalogowani |

`pricing` — brak własnego panelu URL na start; konfiguracja przez admin lub widoki w `dashboard`.

---

## Konwencje kodu

- **Import serwisów:** `from apps.bookings.services.reservation import ReservationService`
- **Nie używać** sygnałów Django do workflow (wyjątki: rzadkie, udokumentowane)
- **Testy:** `apps/<nazwa>/tests/` lub `test_*.py` — serwisy krytyczne w pierwszej kolejności
- **Typowanie:** type hints w serwisach i selektorach (Python 3.12+)

---

## Dokumentacja per aplikacja

| Aplikacja | Plik granic |
|-----------|-------------|
| accounts | [`apps/accounts/README.md`](apps/accounts/README.md) |
| fleet | [`apps/fleet/README.md`](apps/fleet/README.md) |
| bookings | [`apps/bookings/README.md`](apps/bookings/README.md) |
| pricing | [`apps/pricing/README.md`](apps/pricing/README.md) |
| payments | [`apps/payments/README.md`](apps/payments/README.md) |
| operations | [`apps/operations/README.md`](apps/operations/README.md) |
| documents | [`apps/documents/README.md`](apps/documents/README.md) |
| dashboard | [`apps/dashboard/README.md`](apps/dashboard/README.md) |
| website | [`apps/website/README.md`](apps/website/README.md) |
