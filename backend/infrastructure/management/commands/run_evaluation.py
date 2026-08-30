from django.core.management.base import BaseCommand
from application.use_cases.retrieve_chunks import RetrieveChunksUseCase
from infrastructure.retrieval.dense_retriever import DenseRetriever
from infrastructure.retrieval.keyword_retriever import KeywordRetriever
from infrastructure.composition_root import build_embedding_provider
from evaluation.golden_set import GOLDEN_SET

class Command(BaseCommand):
    help = "Run the golden evaluation set against the retrieval pipeline and report metrics."
    def handle(self, *args, **options):
        use_case = RetrieveChunksUseCase(
            dense_retriever=DenseRetriever(build_embedding_provider()),
            keyword_retriever=KeywordRetriever(),
        )
        hits = 0
        refusal_correct = 0
        for case in GOLDEN_SET:
            result = use_case.execute(case["query"], top_k=5)

            if case["should_refuse"]:
                correct_refusal = result.refused
                refusal_correct += int(correct_refusal)
                hit = None
                actual = f"{'REFUSED (correct)' if result.refused else 'NOT refused'} - dense_sim={result.top_dense_similarity:.4f}"
                if result.refused:
                    actual = "REFUSED (correct)"
                else:
                    top = result.chunks[0]
                    actual = f"top1: doc={top.document_filename} section='{top.section}' dense_sim={result.top_dense_similarity:.4f}"
            else:
                correct_refusal = not result.refused
                refusal_correct += int(correct_refusal)
                hit = False
                if result.refused:
                    actual = "REFUSED (incorrectly)"
                else:
                    for chunk in result.chunks:
                        doc_match = (
                            case["expected_document_contains"] is None
                            or case["expected_document_contains"] in chunk.document_filename
                        )
                        section_match = (
                            case["expected_section_contains"] is None
                            or case["expected_section_contains"] in (chunk.section or "")
                        )
                        if doc_match and section_match:
                            hit = True
                            break
                    top = result.chunks[0]
                    actual = f"top1: doc={top.document_filename} section='{top.section}' score={top.score:.4f}"
                hits += int(hit)

            status = "OK" if correct_refusal and (hit is None or hit) else "MISS"
            self.stdout.write(f"[{status}] ({case['case_type']}) {case['query'][:55]}")
            self.stdout.write(f"       expected: doc~'{case['expected_document_contains']}' section~'{case['expected_section_contains']}'")
            self.stdout.write(f"       actual:   {actual}")

        normal_cases = [c for c in GOLDEN_SET if not c["should_refuse"]]
        hit_rate = hits / len(normal_cases) if normal_cases else 0
        refusal_accuracy = refusal_correct / len(GOLDEN_SET)

        self.stdout.write(self.style.SUCCESS(f"\nHit-rate (normal cases): {hits}/{len(normal_cases)} = {hit_rate:.1%}"))
        self.stdout.write(self.style.SUCCESS(f"Refusal correctness (all cases): {refusal_correct}/{len(GOLDEN_SET)} = {refusal_accuracy:.1%}"))