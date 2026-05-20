# Aplikacje domenowe (`backend/apps/`)

Pakiet zawiera **wyłącznie** logikę domenową wynajmu. Konfiguracja projektu (settings, WSGI, root URLs) jest w `backend/config/`.

## Lista aplikacji

| App | Odpowiedzialność w jednym zdaniu |
|-----|----------------------------------|
| [accounts](accounts/README.md) | Tożsamość, role, uprawnienia |
| [fleet](fleet/README.md) | Pojazdy, szkody, blokady — źródło prawdy o flocie |
| [bookings](bookings/README.md) | Klienci, rezerwacje, wynajmy, snapshoty cen na rezerwacji |
| [pricing](pricing/README.md) | Cenniki i silnik naliczania opłat |
| [payments](payments/README.md) | Ruch pieniężny (w tym kaucje) |
| [operations](operations/README.md) | Protokoły wydania/zwrotu i snapshoty operacyjne |
| [documents](documents/README.md) | PDF, faktury, email — artefakty niemutowalne |
| [dashboard](dashboard/README.md) | Panel wewnętrzny i agregaty operacyjne |
| [website](website/README.md) | Kanał publiczny i self-service klienta |

Przed dodaniem kodu w appce — przeczytaj jej `README.md` (granice odpowiedzialności).
