# payments — granice odpowiedzialności

## Cel aplikacji

Rejestracja **ruchu pieniężnego** — wpłaty, kaucje, zwroty, opłaty dodatkowe — oraz integracja z bramką płatności. Nie zastępuje faktury księgowej ani kalkulacji cennika.

---

## Co robi (IN scope)

- Modele: `PaymentIntent`, `Payment`, `Refund`, `PaymentProviderEvent`
- Typy płatności: `rental_fee`, `deposit`, `refund`, `extra_charge`, `damage_charge`
- Metody: `online_gateway`, `cash`, `bank_transfer`, `card`, `blik`
- `PaymentService` — rejestracja wpłaty, alokacja do `Rental` / `Reservation`, zwrot kaucji
- Obsługa webhooków bramki (zdarzenia w `PaymentProviderEvent`)
- Selektory: saldo kaucji, nieopłacone wynajmy, historia płatności klienta
- Reguła: **depozyt ≠ przychód** (zobowiązanie do zwrotu)

---

## Czego nie robi (OUT of scope)

| Obszar | Właściwa aplikacja |
|--------|-------------------|
| Naliczanie opłat z cennika | `pricing` |
| Snapshot cen na rezerwacji | `bookings` (`PriceLine`) |
| Faktura, pozycje VAT, PDF faktury | `documents` |
| Ustalenie dopłaty za uszkodzenie (opis szkody) | `fleet` + `operations`; kwota — `pricing` / ręcznie |
| Protokół wydania/zwrotu | `operations` |
| Raport „przychód miesiąca” (agregacja) | `dashboard` (czyta `payments` + reguły revenue) |

**Zasada:** `payments` wie *„ile i kiedy przeszło pieniądze”*, nie *„co powinno być na fakturze”*.

---

## Modele (zaimplementowane — Sprint 5 MVP)

- `PaymentIntent` — przygotowanie pod bramke online; FK `rental` i/lub `reservation` (min. jedno)
- `Payment` — FK do `Rental` (+ opcjonalnie `Reservation`, `PaymentIntent`)
- `PaymentProviderEvent` — log webhookow (szkielet)
- Typy: `rental_fee`, `deposit`, `refund`, `extra_charge`, `damage_charge`
- Metody: `cash`, `bank_transfer`, `card`, `blik`, `online_gateway`

---

## Serwisy (zaimplementowane)

- `PaymentService.record_payment`, `record_deposit`, `record_rental_fee`, `refund_deposit`
- Selektory: `get_rental_payment_summary`, `get_rental_revenue_total`, `get_rental_deposit_balance`
- Panel: `/panel/platnosci/`, platnosci per wynajem `/panel/platnosci/wynajem/<id>/`
- **Kaucja ≠ przychód** — `REVENUE_PAYMENT_TYPES` bez `deposit` / `refund`

Planowane (Sprint 9): `PaymentGatewayService`, adapter bramki, webhooki, intent dla `Reservation`

### Sprint 9 — taski

| ID | Task | Status |
|----|------|--------|
| **9.1** | `PaymentIntent` + FK `reservation` | ✅ |
| **9.2** | Adapter bramki (mock) | ⬜ |
| **9.3** | `PaymentGatewayService` | ⬜ |
| **9.4** | Webhook endpoint | ⬜ |
| **9.5–9.6** | Website init + confirm po platnosci | ⬜ |
| **9.10** | Testy flow online | ⬜ |

Szczegóły: [`../../../PROJECT_PLAN.md`](../../../PROJECT_PLAN.md) — Sprint 9.

---

## Zależności

| Kierunek | Aplikacja | Powód |
|----------|-----------|--------|
| → czyta | `bookings` | Powiązanie z wynajmem/rezerwacją |
| ← wywoływana przez | `website` (płatność online), `dashboard`, `operations` (dopłata) | |
| → nie mutuje | `bookings` statusów wynajmu | Zmiana statusu płatności ≠ status operacyjny (orkiestracja wyżej jeśli potrzeba) |

---

## Reguły integracji

- Płatność online: `website` inicjuje → `payments` obsługuje intent → callback aktualizuje `Payment`; `bookings` może dostać sygnał przez serwis aplikacji nadrzędnej, nie przez sygnał Django w `payments`.
- Kaucja zwracana jako osobny `Refund` / payment type `refund`.
- **Nigdy** nie sumować `deposit` do przychodu w raportach finansowych.

---

## Antywzorce

- Model `Invoice` w `payments`
- Ustawianie `Reservation.total_paid` bez rekordu `Payment`
- Traktowanie kaucji jako `rental_fee` w raportach
- Logika bramki rozproszona w `website.views`
