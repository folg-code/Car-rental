# documents — granice odpowiedzialności

## Cel aplikacji

**Artefakty dokumentowe niemutowalne** — generowanie PDF, faktury księgowe, wysyłka email, przechowywanie prywatne. Dane wejściowe biorą ze **snapshotów**, nie z „żywego” stanu operacji.

---

## Co robi (IN scope)

- Modele: `Document`, `DocumentTemplate`, `EmailLog`, `Invoice`, `InvoiceItem`
- `DocumentService` — generuj PDF protokołu / umowy z przekazanych DTO/snapshotów
- `InvoiceService` — wystawienie faktury na podstawie `PriceLine` / ustalonych pozycji (nie przeliczanie cennika)
- Prywatne storage: `PrivateDocumentStorage` → `private_documents/` (poza publicznym `MEDIA_ROOT`); pobieranie tylko przez autoryzowany widok (Task 7.8)
- `EmailService` — wysyłka z załącznikiem, log w `EmailLog`
- Selektory: dokumenty po wynajmie/kliencie, status wysyłki
- Szablony HTML → PDF (WeasyPrint / wkhtml / wybrana technologia — decyzja implementacyjna)

---

## Czego nie robi (OUT of scope)

| Obszar | Właściwa aplikacja |
|--------|-------------------|
| Kalkulacja cen | `pricing` |
| Rejestracja wpłaty | `payments` |
| Protokół operacyjny (dane źródłowe) | `operations` |
| Snapshot cen | `bookings` (`PriceLine`) |
| Snapshot uszkodzeń | `operations` (`DamageSnapshot`) |
| Dane auta / klienta (master) | `fleet`, `bookings` |
| Publiczny portal — tylko link do pobrania | `website` (widok) + autoryzacja `accounts` |

**Zasada:** `documents` wie *„jaki plik wygenerowano i komu wysłano”*, nie *„czy auto jest wolne”*.

---

## Modele (zaimplementowane — Sprint 7 / Task 7.1)

- `DocumentTemplate` — szablon HTML → PDF (slug, `template_path`)
- `Document` — plik PDF, hash, powiazania (`Rental`, protokoly, `Invoice`); **niemutowalny** po utworzeniu
- `EmailLog` — log wysylek (pending / sent / failed)
- `Invoice`, `InvoiceItem` — faktura oddzielona od `Payment`; pozycje z `PriceLine` (opcjonalnie)

## Serwisy (zaimplementowane — Task 7.3)

- `PdfRenderer` — HTML (Django templates) → PDF przez WeasyPrint
- `HandoverDocumentData` / `ReturnDocumentData` — zamrozone DTO ze snapshotow protokolu (`selectors/protocol_data.py`)
- Szablony: `documents/pdf/handover_protocol.html`, `return_protocol.html`, `invoice.html`
- `constants.py` — domyslne sciezki szablonow; seed w migracji `0004_seed_document_templates`

## Serwisy (planowane — Task 7.5+)

- `DocumentService.generate_handover_pdf(snapshot_data)`
- `InvoiceService.create_from_price_lines(...)`
- `EmailService.send_document(...)`
- Wszystkie metody generujące przyjmują **komplet danych** w argumencie — brak cichego odczytu live DB dla pól historycznych

---

## Zależności

| Kierunek | Aplikacja | Powód |
|----------|-----------|--------|
| ← wywoływana przez | `operations`, `bookings`, `website`, `dashboard` | Po zdarzeniach biznesowych |
| → czyta (read-only) | `bookings`, `operations`, `payments` | Id powiązań, nie mutacja |
| → nie wywołuje | `pricing` do przeliczenia | Faktura z istniejących linii |

---

## Reguły integracji

- **Payment ≠ Invoice** — faktura może istnieć bez pełnej zapłaty; status płatności w `payments`.
- Ponowne generowanie „tego samego” dokumentu = nowy rekord `Document` z wersją / nowym UUID, nie nadpisanie pliku historycznego (polityka wersjonowania — do ustalenia).
- Email failure — log w `EmailLog`, retry przez serwis, nie w szablonie.

---

## Antywzorce

- `generate_pdf()` które samo odpytuje `fleet.Damage` zamiast snapshotu
- Przechowywanie całego PDF w `HandoverProtocol`
- Tworzenie `Payment` przy wystawianiu faktury
- Dynamiczne „przelicz i wstaw do starego PDF”
