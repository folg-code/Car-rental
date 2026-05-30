from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateDocumentStorage(FileSystemStorage):
    """
    Storage for generated PDFs and invoices.

    Files live outside public MEDIA_ROOT and are not exposed via /media/.
    Download only through authorized panel views (Task 7.8).
    """

    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("location", str(settings.DOCUMENTS_PRIVATE_ROOT))
        kwargs.setdefault("base_url", None)
        super().__init__(**kwargs)

    def url(self, name: str, expire=None) -> str:
        raise NotImplementedError(
            "Prywatne dokumenty nie maja publicznego URL. "
            "Uzyj autoryzowanego widoku pobierania."
        )
