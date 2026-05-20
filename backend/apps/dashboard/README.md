# dashboard — granice odpowiedzialności

## Cel aplikacji

**Panel operacyjny wewnętrzny** — agregacja metryk, alerty, skróty do workflow. Czyta dane z innych aplikacji przez selektory; **nie jest właścicielem** danych domenowych.

---

## Co robi (IN scope)

- Widoki pod prefixem `/panel/` (layout wewnętrzny, nawigacja modułów)
- Strona główna panelu: aktywne wynajmy, wolne auta, nadchodzące zwroty, nieopłacone
- Metryki: obłożenie floty, przychód miesiąca (z `payments` z regułą revenue), wygasające OC/przeglądy (z `fleet`)
- Alerty: konfiguracja progów (opcjonalnie model `AlertRule` w tej app lub w `fleet`)
- Selektory **agregujące** — tylko read, bez mutacji encji bookings/fleet
- HTMX: fragmenty tabel, odświeżanie widgetów
- Ochrona dostępu: role z `accounts` (manager, owner, employee)

---

## Czego nie robi (OUT of scope)

| Obszar | Właściwa aplikacja |
|--------|-------------------|
| CRUD aut, szkód, rezerwacji | `fleet`, `bookings` (własne widoki pod `/panel/flota/` itd.) |
| Protokół wydania/zwrotu (formularze) | `operations` |
| Silnik cen | `pricing` |
| Rejestracja płatności | `payments` |
| Generowanie PDF | `documents` |
| Strona publiczna | `website` |
| Logika dostępności (algorytm) | `fleet.AvailabilityService` — dashboard tylko wywołuje |

**Zasada:** `dashboard` wie *„co pokazać menedżerowi na jednym ekranie”*, nie *„jak zapisać rezerwację”*.

---

## Modele (planowane)

Opcjonalnie i minimalnie:
- `DashboardWidgetConfig`, `UserDashboardPreference` — wyłącznie UX panelu

Brak duplikacji `Car`, `Reservation`, `Payment`.

---

## Serwisy (planowane)

- `DashboardMetricsService` — zbiorcze KPI na dziś / tydzień / miesiąc
- `AlertService` — lista alertów do wyświetlenia (czyta selektory cross-app)

Mutacje domenowe **nie** w `dashboard.services`.

---

## Zależności

| Kierunek | Aplikacja | Powód |
|----------|-----------|--------|
| → czyta | wszystkie domenowe | Agregacja |
| ← wywoływana przez | `accounts` (auth) | |
| → nie mutuje | `bookings`, `fleet`, `payments`, … | Tylko redirect/link do właściwego modułu |

---

## Reguły integracji

- Przycisk „Zarejestruj płatność” → przekierowanie do widoku `payments`, nie POST z dashboardu omijający serwis.
- Przychód w KPI: wyłączyć depozyty (reguła z `payments` selektora).
- Cache metryk — opcjonalny, z invalidacją dokumentowaną; nie wymagany w MVP.

---

## Antywzorce

- Model `Reservation` w `dashboard`
- Zapis rezerwacji w widoku widgetu
- Duplikacja `AvailabilityService`
- Logika faktur/PDF w szablonach dashboardu
