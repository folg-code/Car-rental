# accounts — granice odpowiedzialności

## Cel aplikacji

Zarządzanie **tożsamością**, **autentykacją** i **autoryzacją** w systemie wynajmu. Jedyny właściciel modelu użytkownika i mapowania ról.

---

## Co robi (IN scope)

- Model użytkownika (`User`) i powiązanie z rolami biznesowymi
- Logowanie, wylogowanie, sesja, reset hasła (workflow Django + ewentualne rozszerzenia)
- Role: `owner`, `manager`, `employee`, `accountant`, `customer`
- Uprawnienia: kto ma dostęp do panelu wewnętrznego vs portalu klienta
- Serwisy: tworzenie użytkownika pracownika, przypisanie roli, dezaktywacja konta
- Selektory: użytkownik po ID, lista pracowników, sprawdzenie roli
- Integracja z `AUTH_USER_MODEL` w settings

---

## Czego nie robi (OUT of scope)

| Obszar | Właściwa aplikacja |
|--------|-------------------|
| Dane klienta wynajmu (NIP, adres, historia rezerwacji) | `bookings` (`Customer`) |
| Płatności i rozliczenia | `payments` |
| Widoki panelu operacyjnego / metryki | `dashboard` |
| Rejestracja rezerwacji z formularza publicznego | `website` (orkiestracja) + `bookings` (dane) |
| Wysyłka emaili transakcyjnych (potwierdzenie rezerwacji) | `documents` |

**Zasada:** `accounts` odpowiada na pytanie *„kto jest zalogowany i co wolno?”*, nie *„co klient wynajął?”*.

---

## Modele (planowane)

- `User` (custom, `AbstractUser` lub `AbstractBaseUser` + profile)

Role mogą być: pole enum / osobna tabela `Role` — decyzja implementacyjna w Sprint 1.

---

## Serwisy (planowane)

- `UserService` — create, deactivate, change_role
- (Opcjonalnie) `PermissionService` — centralne sprawdzanie uprawnień do akcji domenowych

---

## Zależności

| Kierunek | Aplikacja | Powód |
|----------|-----------|--------|
| ← wywoływana przez | `dashboard`, `website`, wszystkie `panel/*` | Dekoratory / mixin uprawnień |
| → nie importuje | `bookings`, `fleet`, `payments`, … | Brak zależności domenowych w dół |

---

## Reguły integracji

- Inne aplikacje odwołują się do użytkownika przez `settings.AUTH_USER_MODEL`, nie duplikują tabel użytkowników.
- Klient biznesowy (`Customer`) to osobny byt — konto `User` z rolą `customer` może być powiązane 1:1 w `bookings`, nie w `accounts`.

---

## Antywzorce

- Przechowywanie danych rezerwacji na modelu `User`
- Sprawdzanie uprawnień rozproszone w szablonach zamiast w widokach/serwisach
- Sygnały `post_save` do nadawania ról bez jawnego serwisu
