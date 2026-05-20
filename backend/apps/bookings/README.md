# bookings — granice odpowiedzialności

## Cel aplikacji

**Cykl życia rezerwacji i wynajmu** oraz dane **klienta biznesowego**. Przechowuje intent rezerwacji (`Reservation`) i operacyjny wynajem (`Rental`). Przechowuje **snapshot cen** (`PriceLine`) powiązany z rezerwacją.

---

## Co robi (IN scope)

- Modele: `Customer`, `Reservation`, `Rental`, `PriceLine`
- Statusy rezerwacji: `draft`, `pending_payment`, `confirmed`, `cancelled`, `expired`, `converted_to_rental`
- Statusy wynajmu: `scheduled`, `active`, `returned`, `closed`, `cancelled`
- Workflow: `Reservation → Rental` (konwersja tylko z dozwolonego statusu)
- `ReservationService`, `RentalService` — create, cancel, expire, convert_to_rental
- Zapis `PriceLine` po kalkulacji z `pricing` (snapshot — niemutowalny po zatwierdzeniu)
- Selektory: rezerwacje w okresie, aktywne wynajmy, klient po ID
- Walidacja: brak nakładających się rezerwacji/wynajmów na tym samym aucie (z `fleet.AvailabilityService`)

---

## Czego nie robi (OUT of scope)

| Obszar | Właściwa aplikacja |
|--------|-------------------|
| Definicja cennika, reguły weekend/święto | `pricing` |
| Kalkulacja kwot (algorytm cen) | `pricing.PricingService` |
| Rejestracja wpłaty, kaucja, zwrot | `payments` |
| Protokół wydania/zwrotu, podpis, zdjęcia | `operations` |
| Generowanie PDF / faktury | `documents` |
| Definicja auta, szkody flotowe | `fleet` |
| Logowanie użytkownika | `accounts` |
| Agregaty KPI (przychód miesiąca) | `dashboard` |
| Formularz publiczny (HTML) | `website` |

**Zasada:** `bookings` wie *„kto, co, kiedy zarezerwował/wynajął i ile miał zapłacić (snapshot)”*, nie *„ile faktycznie wpłynęło na konto”*.

---

## Modele (planowane)

- `Customer` — dane kontrahenta; opcjonalne powiązanie z `User` (rola customer)
- `Reservation` — intent; FK do `Car`, `Customer`
- `Rental` — wynajem operacyjny; powiązanie z `Reservation`
- `PriceLine` — pozycje snapshotu ceny (powstałe z kalkulacji `pricing`)

---

## Serwisy (planowane)

- `ReservationService`
- `RentalService`
- (Orchestracja) wywołanie `PricingService` przy zapisie, potem utrwalenie `PriceLine`

---

## Zależności

| Kierunek | Aplikacja | Powód |
|----------|-----------|--------|
| → wywołuje | `pricing` | Kalkulacja przed snapshotem |
| → wywołuje | `fleet` | Walidacja dostępności |
| ← wywoływana przez | `website`, `dashboard`, `operations`, `payments` | Rezerwacja, wynajem, powiązanie płatności |
| → nie importuje | `documents`, `operations` (modele) | Unikaj cykli — orkiestracja w serwisach wyższego poziomu lub sygnał jawny w jednym miejscu |

---

## Reguły integracji

- **Reservation ≠ Rental** — osobne tabele i statusy; jedna rezerwacja → co najwyżej jeden wynajem.
- Po `converted_to_rental` rezerwacja nie powinna wracać do `confirmed` bez jawnego workflow anulowania wynajmu.
- `PriceLine` nie jest przeliczany po zmianie `PriceList` w `pricing`.

---

## Antywzorce

- Przechowywanie kwoty „zapłacono” na `Reservation` (to `payments`)
- Tworzenie `HandoverProtocol` w `bookings`
- Przebudowa `PriceLine` z aktualnego cennika
- Fat models z logiką statusów — statusy przez serwisy
