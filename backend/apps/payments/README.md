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

## Modele (planowane)

Zgodnie z `AGENT_CONTEXT.md` § payments. Powiązania FK do `Rental` / `Reservation` (nie do `Invoice` jako źródło prawdy).

---

## Serwisy (planowane)

- `PaymentService` — record_payment, record_deposit, refund_deposit
- `PaymentGatewayService` — intent, webhook, idempotencja zdarzeń
- Jawne rozróżnienie revenue vs liability w selektorach raportowych

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
