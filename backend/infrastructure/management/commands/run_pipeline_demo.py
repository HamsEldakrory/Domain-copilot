from django.core.management.base import BaseCommand
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
from infrastructure.persistence.policy_lookup import django_policy_limit_lookup
class Command(BaseCommand):
    help = "Run the D2 adjudication pipeline against a test claim end-to-end."

    def add_arguments(self, parser):
        parser.add_argument("claim_id")
        parser.add_argument("--claimed-amount", type=float, default=5000)

    def handle(self, *args, **options):
        llm = build_completion_provider()
        retrieve_use_case = RetrieveChunksUseCase(
            dense_retriever=DenseRetriever(build_embedding_provider()),
            keyword_retriever=KeywordRetriever(),
        )
        get_policy_version = GetPolicyVersionTool()
        search_policy = SearchPolicyTool(retrieve_use_case)
        orchestrator = AdjudicationPipelineOrchestrator(
            coverage_matcher=CoverageMatcherAgent(llm, get_policy_version, search_policy),
            exclusion_analyst=ExclusionAnalystAgent(llm, search_policy),
            adjudication_drafter=AdjudicationDrafterAgent(llm, CalculatePayoutTool(), DetectAnomalyTool()),
            run_recorder=DjangoAgentRunRecorder(),
            policy_limit_lookup=django_policy_limit_lookup,
        )
        result = orchestrator.run(claim_id=options["claim_id"], claimed_amount=options["claimed_amount"])
        self.stdout.write(self.style.SUCCESS(f"Job {result.job_id} completed"))
        for step in result.steps:
            self.stdout.write(f"\n--- {step['agent']} ---")
            for k, v in step["result"].items():
                self.stdout.write(f"{k}: {v}")