# fleet — granice odpowiedzialności

## Cel aplikacji

**Źródło prawdy o pojazdach** — dane floty, historia uszkodzeń, serwis, dokumenty pojazdu oraz **blokady dostępności**. Nie prowadzi rezerwacji ani protokołów operacyjnych.

---

## Co robi (IN scope)

- Modele: `Car`, `CarCategory`, `CarImage`, `CarDocument`, `AvailabilityBlock`, `Damage`, `DamagePhoto`, `RepairRecord`
- CRUD pojazdów i kategorii (panel wewnętrzny)
- Globalna historia `Damage` — niezależna od protokołów wydania/zwrotu
- Blokady ręczne i serwisowe (`AvailabilityBlock`)
- `AvailabilityService` — **wyliczanie** dostępności w przedziale dat (rezerwacje/wynajmy/blokady — dane z innych app przez selektory)
- Selektory: lista aut, auto po ID, aktywne uszkodzenia, blokady w okresie
- Admin floty, zdjęcia, dokumenty techniczne (OC, przegląd)

---

## Czego nie robi (OUT of scope)

| Obszar | Właściwa aplikacja |
|--------|-------------------|
| Rezerwacje, wynajmy, klienci | `bookings` |
| Naliczanie cen, cenniki | `pricing` |
| Snapshot uszkodzeń na protokole | `operations` (`DamageSnapshot`) |
| PDF protokołu, faktury | `documents` |
| Płatność za szkodę / dopłata | `payments` (kwota z `operations` / `pricing`) |
| Publiczna lista aut na stronie | `website` (widok) + selektory `fleet` |
| Pole `is_available` na `Car` | **Zabronione** — dostępność tylko wyliczana |

**Zasada:** `fleet` wie *„jakie jest auto i jakie ma szkody/blokady”*, nie *„czy klient zapłacił”*.

---

## Modele (planowane)

Zgodnie z `AGENT_CONTEXT.md` § fleet.

`Damage` pozostaje „żywą” historią; protokół operacyjny kopiuje stan do `DamageSnapshot` w `operations`.

---

## Serwisy (planowane)

- `AvailabilityService` — `is_car_available(car, start, end)` z uwzględnieniem danych z `bookings`
- `DamageService` — dodanie/aktualizacja uszkodzenia, zdjęcia
- `FleetMaintenanceService` — blokady serwisowe, `RepairRecord`

---

## Zależności

| Kierunek | Aplikacja | Powód |
|----------|-----------|--------|
| → czyta (selektory) | `bookings` | Rezerwacje/wynajmy wpływają na dostępność |
| ← wywoływana przez | `bookings`, `operations`, `dashboard`, `website` | Wybór auta, lista floty |
| → nie mutuje | `bookings`, `operations` | Brak tworzenia rezerwacji z `fleet` |

Unikać importu `bookings.models` w `fleet.models` — tylko serwis/selektor cross-app.

---

## Reguły integracji

- `operations` przy wydaniu **kopiuje** aktywne `Damage` do snapshotu — nie przenosi własności szkód do `operations`.
- Nowe uszkodzenie z protokołu zwrotu: zapis do `fleet.Damage` przez jawny serwis (orkiestracja w `operations` lub wspólny workflow).

---

## Antywzorce

- `Car.is_available = True/False`
- Usuwanie historii `Damage` po zamknięciu protokołu
- Logika cen w module floty
- Bezpośrednie zapytania o rezerwacje w widokach fleet zamiast `AvailabilityService`
