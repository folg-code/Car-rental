# operations — granice odpowiedzialności

## Cel aplikacji

**Workflow operacyjny w terenie — paperless.** Wszystkie protokoły wyłącznie elektroniczne; telefon lub tablet wystarcza do pełnego wydania i zwrotu auta. Obejmuje: przebieg, paliwo, zdjęcia, podpisy, **snapshoty** szkód oraz (docelowo) PDF + email bez papieru.

Pełna roadmapa kroków: [`PROJECT_PLAN.md`](../../../PROJECT_PLAN.md#roadmap--operations-paperless) · [`AGENT_CONTEXT.md`](../../../AGENT_CONTEXT.md) — sekcja `operations/`.

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

## Modele (zaimplementowane — Sprint 6 MVP)

- `HandoverProtocol`, `ReturnProtocol` — powiazanie 1:1 z `Rental`
- `ProtocolPhoto`, `Signature` — zdjecia i podpis (upload z `capture="environment"`)
- `DamageSnapshot` — kopia pol z `Damage` w chwili protokolu; **nie aktualizowac** po edycji `fleet.Damage`

---

## Serwisy (zaimplementowane)

- `HandoverService.complete_handover` — km, paliwo, zdjecia, podpis, snapshot szkod, `RentalService.start`, **auto PDF** (`DocumentService`)
- `ReturnService.complete_return` — porownanie paliwa/km, snapshot, `RentalService.mark_returned`, **auto PDF** (`DocumentService`)
- `SurchargePreviewService` — podglad doplat (paliwo/km z `ExtraService`: `fuel_refill`, `extra_km`)
- `get_return_damage_comparison` — porownanie snapshotow wydania z aktywna flota przy zwrocie
- `DamageSnapshotService` — freeze aktywnych szkod, snapshot nowych zgloszen
- Panel: `/panel/operacje/` — kolejka wydan i zwrotow

### Roadmap — docelowe workflow (paperless)

**Wydanie:** otwarcie wynajmu na telefonie → protokół → km / paliwo / uwagi → zdjęcia → szkody → podpis palcem → PDF → email → `Rental` **active**.

**Zwrot:** otwarcie zwrotu → km / paliwo / uwagi → porównanie szkód z wydaniem → nowe szkody → wyliczenie dopłat → podpis → PDF → email → zamknięcie wynajmu.

| Element | Status |
|---------|--------|
| Kolejka + formularze mobilne, km/paliwo/uwagi, zdjęcia, szkody, podpis | ✅ MVP (Sprint 6) |
| `Rental` → active po wydaniu | ✅ |
| `Rental` → returned po zwrocie | ✅ |
| PDF po protokole | ✅ auto (`DocumentService` w `complete_handover` / `complete_return`) |
| Email do klienta | ✅ auto po PDF (`EmailService`) |
| HTMX krok po kroku | ✅ wizard wydania (3 kroki); zwrot: podgląd dopłat HTMX |
| Wyliczenie dopłat → `payments` | ✅ naliczenie `RentalCharge` po zwrocie; panel pokazuje saldo do zaplaty |
| UI porównania szkód wydanie/zwrot | ✅ |
| `close` po rozliczeniu finansowym | ✅ auto-close gdy `total_due` = 0 |

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
