# operations — granice odpowiedzialności

## Cel aplikacji

**Workflow operacyjny w terenie** — wydanie i zwrot pojazdu: przebieg, paliwo, zdjęcia, podpisy oraz **snapshoty** stanu na moment protokołu. Zoptymalizowane pod urządzenia mobilne.

---

## Co robi (IN scope)

- Modele: `HandoverProtocol`, `ReturnProtocol`, `ProtocolPhoto`, `Signature`, `DamageSnapshot`
- UI mobilne: formularze krok po kroku, HTMX, `capture="environment"` na uploadzie zdjęć
- `HandoverService` — workflow wydania (§9 AGENT_CONTEXT)
- `ReturnService` — workflow zwrotu, porównanie ze snapshotem wydania
- Kopiowanie aktywnych `Damage` z `fleet` → `DamageSnapshot` (zamrożenie)
- Rejestracja **nowych** uszkodzeń z protokołu (delegacja zapisu do `fleet.DamageService`)
- Selektory: protokół po wynajmie, zdjęcia protokołu
- Powiązanie protokołu wyłącznie z `Rental` (nie z samą `Reservation`)

---

## Czego nie robi (OUT of scope)

| Obszar | Właściwa aplikacja |
|--------|-------------------|
| Trwała historia szkód floty | `fleet` (`Damage`) |
| Generowanie pliku PDF | `documents` (dane ze snapshotów) |
| Wysyłka emaila z protokołem | `documents` |
| Naliczanie opłat z cennika | `pricing` |
| Pobranie dopłaty / kaucja | `payments` |
| Tworzenie wynajmu z rezerwacji | `bookings` |
| Lista aut / dostępność | `fleet` |
| Dashboard KPI | `dashboard` |

**Zasada:** `operations` wie *„co było na pojeździe w momencie wydania/zwrotu (dowód)”*, nie *„jaka jest aktualna cena w cenniku”*.

---

## Modele (planowane)

`DamageSnapshot` — kopia pól z `Damage` w chwili protokołu; **nie aktualizować** po edycji `fleet.Damage`.

---

## Serwisy (planowane)

- `HandoverService` — complete_handover, attach_photo, capture_signature
- `ReturnService` — complete_return, calculate_surcharges (wynik → caller zapisuje w `pricing`/`payments`)
- `DamageSnapshotService` — freeze_damages_for_protocol

---

## Zależności

| Kierunek | Aplikacja | Powód |
|----------|-----------|--------|
| → wywołuje | `fleet`, `bookings` | Auto, wynajem, szkody |
| → wywołuje (po zakończeniu) | `documents` | PDF + email |
| → może wywołać | `pricing`, `payments` | Dopłaty po zwrocie |
| ← wywoływana przez | `dashboard` (link do wydania/zwrotu) | |

---

## Reguły integracji

- PDF budowany z `DamageSnapshot` + danych protokołu — **nigdy** z live listy `Damage`.
- Zdjęcia protokołu ≠ zdjęcia szkód flotowych (`DamagePhoto` vs `ProtocolPhoto`).
- Po zamknięciu protokołu edycja pól krytycznych zablokowana (serwis / status).

---

## Antywzorce

- Aktualizacja `DamageSnapshot` gdy zmieni się `fleet.Damage`
- Logika PDF w `operations.views`
- Protokół powiązany tylko z `Reservation` bez `Rental`
- Przebudowa protokołu z aktualnych danych DB „dla poprawki”
