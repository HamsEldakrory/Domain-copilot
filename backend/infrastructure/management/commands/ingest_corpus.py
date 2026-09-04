import glob
import os
import re
from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone

from application.use_cases.ingest_document import IngestDocumentUseCase
from infrastructure.composition_root import build_embedding_provider
from infrastructure.ingestion.docx_extractor import DocxExtractor
from infrastructure.ingestion.pdf_extractor import PdfExtractor
from infrastructure.ingestion.section_chunker import NumberedHeadingChunker
from infrastructure.persistence.django_chunk_repository import DjangoChunkRepository
from infrastructure.persistence.models import Client, Document, Policy, PolicyVersion

FILENAME_RE = re.compile(r"policy_\d+_(?P<code>[a-z_]+)_(?P<version>\d{4}-\d{2})\.(pdf|docx)$")

VERSION_DATES = {
    "2023-01": (date(2023, 1, 1), date(2024, 1, 1)),
    "2024-01": (date(2024, 1, 1), date(2025, 1, 1)),
    "2025-01": (date(2025, 1, 1), date(2026, 1, 1)),
}

EXTRACTORS = {".pdf": PdfExtractor(), ".docx": DocxExtractor()}


class Command(BaseCommand):
    help = "Ingest all documents in the corpus/ folder: extract, chunk, embed, index."

    def add_arguments(self, parser):
        parser.add_argument("--corpus-dir", default="../corpus")

    def handle(self, *args, **options):
        corpus_dir = options["corpus_dir"]
        client, _ = Client.objects.get_or_create(name="Default Synthetic Client")

        chunker = NumberedHeadingChunker()
        embedding_provider_name = os.getenv("EMBEDDING_PROVIDER", "openai")
        llm_provider = build_embedding_provider()
        chunk_repo = DjangoChunkRepository()
        use_case = IngestDocumentUseCase(
            chunker=chunker,
            llm_provider=llm_provider,
            chunk_repository=chunk_repo,
            embedding_provider_name=embedding_provider_name,
        )

        files = sorted(
            glob.glob(os.path.join(corpus_dir, "*.pdf"))
            + glob.glob(os.path.join(corpus_dir, "*.docx"))
        )
        self.stdout.write(f"Found {len(files)} files in {corpus_dir}, embedding via {embedding_provider_name}")

        for file_path in files:
            filename = os.path.basename(file_path)
            ext = os.path.splitext(filename)[1].lower()

            match = FILENAME_RE.search(filename)
            if match:
                code = match.group("code")
                version_label = match.group("version")
                effective_from, effective_to = VERSION_DATES.get(
                    version_label, (timezone.now().date(), None)
                )
            else:
                code = os.path.splitext(filename)[0]
                version_label = "v1"
                effective_from, effective_to = timezone.now().date(), None
                self.stdout.write(self.style.WARNING(
                    f"  {filename}: filename doesn't match expected pattern, using fallback metadata"
                ))

            policy, _ = Policy.objects.get_or_create(client=client, policy_number=code)
            policy_version, _ = PolicyVersion.objects.get_or_create(
                policy=policy, version=version_label,
                defaults={"effective_from": effective_from, "effective_to": effective_to},
            )
            document, _ = Document.objects.get_or_create(
                policy_version=policy_version, filename=filename,
                defaults={"file_type": ext.lstrip("."), "status": "pending"},
            )

            extractor = EXTRACTORS[ext]
            result = use_case.execute(document.id, file_path, extractor)

            if result.status == "ingested":
                self.stdout.write(self.style.SUCCESS(f"  {filename}: ingested ({result.chunk_count} chunks)"))
            elif result.status == "unchanged":
                self.stdout.write(f"  {filename}: unchanged, skipped")
            else:
                self.stdout.write(self.style.ERROR(f"  {filename}: FAILED - {result.error}"))