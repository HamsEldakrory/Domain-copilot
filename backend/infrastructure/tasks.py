from celery import shared_task


@shared_task(bind=True)
def adjudicate_claim_task(self, job_id: str, claim_id: str, claimed_amount: float, correlation_id: str | None = None, deductible_override: float | None = None):
    from application.agents.adjudication_drafter import AdjudicationDrafterAgent
    from application.agents.coverage_matcher import CoverageMatcherAgent
    from application.agents.exclusion_analyst import ExclusionAnalystAgent
    from application.use_cases.adjudication_pipeline import (
        AdjudicationPipelineOrchestrator,
    )
    from application.use_cases.retrieve_chunks import RetrieveChunksUseCase
    from domain.job_states import JOB_TERMINAL_STATUSES
    from infrastructure.composition_root import (
        build_completion_provider,
        build_embedding_provider,
    )
    from infrastructure.events.redis_job_event_publisher import RedisJobEventPublisher
    from infrastructure.persistence.django_agent_run_recorder import (
        DjangoAgentRunRecorder,
    )
    from infrastructure.persistence.django_cancellation_checker import (
        DjangoCancellationChecker,
    )
    from infrastructure.persistence.policy_lookup import django_policy_limit_lookup
    from infrastructure.retrieval.dense_retriever import DenseRetriever
    from infrastructure.retrieval.keyword_retriever import KeywordRetriever
    from infrastructure.tools.calculate_payout import CalculatePayoutTool
    from infrastructure.tools.detect_anomaly import DetectAnomalyTool
    from infrastructure.tools.get_policy_version import GetPolicyVersionTool
    from infrastructure.tools.search_policy import SearchPolicyTool

    event_publisher = RedisJobEventPublisher()
    cancellation_checker = DjangoCancellationChecker()
    run_recorder = DjangoAgentRunRecorder(existing_job_id=job_id, event_publisher=event_publisher)

    if run_recorder.is_cancelled(job_id):
        return {"job_id": job_id, "skipped": True, "reason": "Job already cancelled before task started"}

    job_status = _get_job_status(job_id)
    if job_status in JOB_TERMINAL_STATUSES:
        return {"job_id": job_id, "skipped": True, "reason": f"Job already in terminal state {job_status}"}

    run_recorder.update_job_status(job_id, "RUNNING")
    llm = build_completion_provider()
    retrieve_use_case = RetrieveChunksUseCase(DenseRetriever(build_embedding_provider()), KeywordRetriever())
    get_policy_version = GetPolicyVersionTool()
    search_policy = SearchPolicyTool(retrieve_use_case)
    orchestrator = AdjudicationPipelineOrchestrator(
        coverage_matcher=CoverageMatcherAgent(llm, get_policy_version, search_policy, event_publisher, cancellation_checker),
        exclusion_analyst=ExclusionAnalystAgent(llm, search_policy, event_publisher, cancellation_checker),
        adjudication_drafter=AdjudicationDrafterAgent(llm, CalculatePayoutTool(), DetectAnomalyTool(), event_publisher, cancellation_checker),
        run_recorder=run_recorder,
        policy_limit_lookup=django_policy_limit_lookup,
        search_policy_tool=search_policy,
        get_policy_version_tool=get_policy_version,
        correlation_id=correlation_id,
    )
    result = orchestrator.run(claim_id=claim_id, claimed_amount=claimed_amount, deductible_override=deductible_override)
    return {"job_id": result.job_id, "degraded": result.degraded}

def _get_job_status(job_id):
    from infrastructure.persistence.models import Job
    job = Job.objects.filter(id=job_id).only("status").first()
    return job.status if job else None

@shared_task
def ingest_document_task(document_id: str, file_path: str, file_extension: str):
    from application.use_cases.ingest_document import IngestDocumentUseCase
    from infrastructure.composition_root import build_embedding_provider
    from infrastructure.ingestion.docx_extractor import DocxExtractor
    from infrastructure.ingestion.pdf_extractor import PdfExtractor
    from infrastructure.ingestion.section_chunker import NumberedHeadingChunker
    from infrastructure.persistence.django_chunk_repository import DjangoChunkRepository

    extractor = PdfExtractor() if file_extension == "pdf" else DocxExtractor()
    embedding_provider_name = __import__("os").getenv("EMBEDDING_PROVIDER", "openai")

    use_case = IngestDocumentUseCase(
        chunker=NumberedHeadingChunker(),
        llm_provider=build_embedding_provider(),
        chunk_repository=DjangoChunkRepository(),
        embedding_provider_name=embedding_provider_name,
    )
    result = use_case.execute(document_id, file_path, extractor)
    return {"document_id": document_id, "status": result.status, "chunk_count": result.chunk_count}