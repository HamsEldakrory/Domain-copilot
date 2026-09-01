from celery import shared_task

@shared_task(bind=True)
def adjudicate_claim_task(self, claim_id: str, claimed_amount: float):
    from infrastructure.composition_root import build_embedding_provider, build_completion_provider
    from infrastructure.retrieval.dense_retriever import DenseRetriever
    from infrastructure.retrieval.keyword_retriever import KeywordRetriever
    from application.use_cases.retrieve_chunks import RetrieveChunksUseCase
    from infrastructure.tools.get_policy_version import GetPolicyVersionTool
    from infrastructure.tools.search_policy import SearchPolicyTool
    from infrastructure.tools.calculate_payout import CalculatePayoutTool
    from infrastructure.tools.detect_anomaly import DetectAnomalyTool
    from application.agents.coverage_matcher import CoverageMatcherAgent
    from application.agents.exclusion_analyst import ExclusionAnalystAgent
    from application.agents.adjudication_drafter import AdjudicationDrafterAgent
    from application.use_cases.adjudication_pipeline import AdjudicationPipelineOrchestrator
    from infrastructure.persistence.django_agent_run_recorder import DjangoAgentRunRecorder
    from infrastructure.persistence.django_audit_logger import DjangoAuditLogger
    from infrastructure.persistence.policy_lookup import django_policy_limit_lookup

    llm = build_completion_provider()
    retrieve_use_case = RetrieveChunksUseCase(DenseRetriever(build_embedding_provider()), KeywordRetriever())
    get_policy_version = GetPolicyVersionTool()
    search_policy = SearchPolicyTool(retrieve_use_case)
    orchestrator = AdjudicationPipelineOrchestrator(
        coverage_matcher=CoverageMatcherAgent(llm, get_policy_version, search_policy),
        exclusion_analyst=ExclusionAnalystAgent(llm, search_policy),
        adjudication_drafter=AdjudicationDrafterAgent(llm, CalculatePayoutTool(), DetectAnomalyTool()),
        run_recorder=DjangoAgentRunRecorder(),
        policy_limit_lookup=django_policy_limit_lookup,
        audit_logger=DjangoAuditLogger(),
        search_policy_tool=search_policy,
        get_policy_version_tool=get_policy_version,
    )
    result = orchestrator.run(claim_id=claim_id, claimed_amount=claimed_amount)
    return {"job_id": result.job_id, "degraded": result.degraded}