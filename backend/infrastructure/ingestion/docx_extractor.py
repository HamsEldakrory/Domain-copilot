import os
import subprocess
import tempfile

from domain.ports.document_extractor import DocumentExtractor, ExtractedDocument
from infrastructure.ingestion.pdf_extractor import PdfExtractor


class DocxExtractor(DocumentExtractor):
    def supports(self, file_extension: str) -> bool:
        return file_extension.lower() == ".docx"
    def extract(self, file_path: str) -> ExtractedDocument:
        with tempfile.TemporaryDirectory() as tmp_dir:
            profile_dir = os.path.join(tmp_dir, "lo_profile")
            result = subprocess.run(
                [
                   "soffice", "--headless", "--norestore",
                   f"-env:UserInstallation=file://{profile_dir}",
                   "--convert-to", "pdf",
                   "--outdir", tmp_dir, file_path,
                ],
                capture_output=True,
                timeout=90,
                check=False,
                )
            if result.returncode != 0:
                raise RuntimeError(
                    f"LibreOffice conversion failed for {file_path}: {result.stderr.decode()}"
                    )
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            pdf_path = os.path.join(tmp_dir, f"{base_name}.pdf")
            return PdfExtractor().extract(pdf_path)