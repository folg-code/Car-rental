# pricing — granice odpowiedzialności

## Cel aplikacji

**Silnik cenowy** — definicja cenników i **kalkulacja** tego, co *powinno* zostać naliczone. Nie rejestruje płatności ani nie wystawia faktur.

---

## Co robi (IN scope)

- Modele: `PriceList`, `DailyRate`, `PricingRule`, `ExtraService`
- Reguły: sezon, weekend, święto, rabat długoterminowy, dopłaty ręczne (uprawnienia)
- `PricingService` — wejście: auto/kategoria, daty, wybrane extras → wyjście: struktura pozycji do zapisu jako `PriceLine` w `bookings`
- Konfiguracja opłat jednorazowych: fotelik, dodatkowy kierowca, dostawa, mycie, paliwo, km dodatkowe
- Selektory: aktywny cennik, reguły dla daty
- Panel `/panel/cenniki/` — CRUD cenników, stawki, reguły, dodatki (Django Admin nadal dostępny)

---

## Czego nie robi (OUT of scope)

| Obszar | Właściwa aplikacja |
|--------|-------------------|
| Trwały snapshot na rezerwacji | `bookings` (`PriceLine`) |
| Płatność, kaucja, zwrot | `payments` |
| Faktura VAT, pozycje faktury | `documents` (`Invoice`, `InvoiceItem`) |
| Dopłata za zwrot po protokole (opóźnienie, szkoda) | Kalkulacja może użyć `pricing`; **decyzja i kwota do pobrania** — orchestracja `operations` + zapis w `payments` |
| Rezerwacja / wynajem | `bookings` |
| Dostępność auta | `fleet` |

**Zasada:** `pricing` odpowiada na *„ile wynika z cennika?”*, nie *„ile wpłynęło?”* ani *„co jest na fakturze?”*.

---

## Modele

- `PriceList` — cennik (okres obowiazywania, waluta, domyslny)
- `DailyRate` — stawka dzienna per `fleet.CarCategory`
- `PricingRule` — weekend, swieta/sezon, rabat dlugoterminowy, rabat reczny
- `ExtraService` — fotelik, dodatkowy kierowca, dostawa, mycie, paliwo, km

Snapshot na rezerwacji: `bookings.PriceLine` (brak FK z `pricing` do `Reservation`).

---

## Serwisy

- `PricingService.calculate(...)` → `PricingResult` / `CalculatedPriceLine`
- Selektory: `selectors/price_list.py` (cennik na datę, stawki, reguły, extras)

Zapis snapshotu: `bookings.PriceSnapshotService` (nie w `pricing`).

Wszystkie obliczenia cen **tylko** w `services/`, nigdy w szablonach.

---

## Zależności

| Kierunek | Aplikacja | Powód |
|----------|-----------|--------|
| → czyta (selektory) | `fleet` | Kategoria auta |
| ← wywoływana przez | `bookings`, `website`, `operations` (dopłaty) | Kalkulacja przed zapisem |
| → nie mutuje | `bookings`, `payments` | Zwraca wynik; caller zapisuje snapshot |

---

## Reguły integracji

- Wynik kalkulacji jest **kopiowany** do `PriceLine` przez `bookings` — `pricing` nie edytuje rezerwacji.
- Zmiana `DailyRate` nie wpływa na istniejące `PriceLine`.
- Faktura może odzwierciedlać `PriceLine`, ale model faktury żyje w `documents`.

---

## Antywzorce

- Model `Payment` w `pricing`
- Przechowywanie „finalnej ceny” tylko na rezerwacji bez rozbicia na linie
- Reguły cen w szablonach HTMX
- Import `bookings.models` w `pricing.models`
