from apps.documents.services.document import DocumentService


class TestDocumentContentHash:
    def test_content_hash_is_stable_for_identical_html(self) -> None:
        html = "<html><body><p>Protokol wydania</p></body></html>"
        first = DocumentService._content_hash_from_html(html)
        second = DocumentService._content_hash_from_html(html)
        assert first == second
        assert len(first) == 64

    def test_content_hash_changes_when_html_changes(self) -> None:
        first = DocumentService._content_hash_from_html("<p>Opis A</p>")
        second = DocumentService._content_hash_from_html("<p>Opis B</p>")
        assert first != second
