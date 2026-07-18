# operations — granice odpowiedzialności

## Cel aplikacji

**Workflow operacyjny w terenie — paperless.** Wszystkie protokoły wyłącznie elektroniczne;
telefon lub tablet wystarcza do pełnego wydania i zwrotu auta.

Wymagania produktowe (diagram, drafty, wyposażenie, rozliczenie): plik
`# Protokół wydania i zwrotu pojazdu.txt` (spec mobilny).

---

## Co robi (IN scope)

- Drafty wielokrokowe: `HandoverProtocol` / `ReturnProtocol` (`status`, `current_step`)
- `ProtocolDriver`, `ProtocolDamageMarker`, `ProtocolEquipmentLine`, `ProtocolSettlementLine`
- `ProtocolPhoto.category`, dyskretna skala paliwa (`fuel_level`) + kompatybilny `%`
- UI mobilne `/panel/operacje/` — long-press diagram, obowiązkowe zdjęcia przy zwrocie
- `HandoverService` / `ReturnService`: `start_*`, `save_*`, `finalize_*` (+ facade `complete_*`)
- Snapshoty szkód (`DamageSnapshot`) — PDF wyłącznie ze snapshotów
- Wyszukiwanie w kolejkach wydania/zwrotu
- Dopłaty po zwrocie → `payments` (zatwierdzone linie rozliczenia)

---

## Czego nie robi (OUT of scope)

| Obszar | Właściwa aplikacja |
|--------|-------------------|
| Katalog wyposażenia / pojemność baku | `fleet` (`EquipmentItem`, `Car.fuel_tank_capacity_liters`) |
| Trwała historia szkód floty | `fleet` (`Damage` + współrzędne diagramu) |
| Generowanie PDF / email | `documents` |
| Cennik dopłat | `pricing` (`POST_RENTAL_EXTRA_CODES`) |
| Pobranie dopłaty / kaucja | `payments` |

---

## Przepływ ekranów

**Wydanie:** wybór → kierowca → przebieg/paliwo → diagram → zdjęcia → wnętrze → wyposażenie → podsumowanie → podpis

**Zwrot:** wybór → przebieg/paliwo → nowe uszkodzenia → zdjęcia obowiązkowe → wyposażenie → czystość → rozliczenie → podsumowanie → podpis/odmowa

Po podpisie protokół jest zablokowany (`is_locked`).

---

## Antywzorce

- Aktualizacja `DamageSnapshot` gdy zmieni się `fleet.Damage`
- Hard-delete historii uszkodzeń (używaj soft-status / resolution)
- PDF z live listy `Damage`
- Edycja protokołu po `completed` / `closed_without_signature`
