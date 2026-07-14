from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.website.services.chat_retention import ChatRetentionService


class Command(BaseCommand):
    help = "Usuwa wiadomosci czatu starsze niz CHAT_MESSAGE_RETENTION_DAYS (Sprint 8b)."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--days",
            type=int,
            default=None,
            help=(
                "Nadpisanie retencji z settings (domyslnie CHAT_MESSAGE_RETENTION_DAYS)"
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Pokaz liczby bez usuwania",
        )

    def handle(self, *args, **options) -> None:
        retention_days = options["days"] or settings.CHAT_MESSAGE_RETENTION_DAYS
        dry_run = options["dry_run"]

        try:
            result = ChatRetentionService.purge_old_data(
                retention_days,
                dry_run=dry_run,
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        mode = "DRY-RUN" if result.dry_run else "PURGE"
        self.stdout.write(
            self.style.SUCCESS(
                f"[{mode}] retencja={result.retention_days}d — "
                f"wiadomosci={result.messages_deleted}, "
                f"sessje={result.sessions_deleted}",
            ),
        )
