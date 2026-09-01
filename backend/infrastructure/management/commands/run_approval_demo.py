from django.core.management.base import BaseCommand, CommandError
from infrastructure.composition_root import build_embedding_provider, build_completion_provider
from infrastructure.retrieval.dense_retriever import DenseRetriever
from infrastructure.retrieval.keyword_retriever import KeywordRetriever
from application.use_cases.retrieve_chunks import RetrieveChunksUseCase
from infrastructure.tools.get_policy_version import GetPolicyVersionTool
from infrastructure.tools.search_policy import SearchPolicyTool
from infrastructure.tools.calculate_payout import CalculatePayoutTool
from infrastructure.tools.detect_anomaly import DetectAnomalyTool
from infrastructure.tools.finalize_adjudication import FinalizeAdjudicationTool
from application.agents.coverage_matcher import CoverageMatcherAgent
from application.agents.exclusion_analyst import ExclusionAnalystAgent
from application.agents.adjudication_drafter import AdjudicationDrafterAgent
from application.use_cases.adjudication_pipeline import AdjudicationPipelineOrchestrator
from application.use_cases.approval_gate import ApprovalGateUseCase
from application.use_cases.get_run_trace import GetRunTraceUseCase
from infrastructure.persistence.django_agent_run_recorder import DjangoAgentRunRecorder
from infrastructure.persistence.django_audit_logger import DjangoAuditLogger
from infrastructure.persistence.django_approval_repository import DjangoApprovalRepository
from infrastructure.persistence.django_trace_repository import DjangoTraceRepository
from infrastructure.persistence.policy_lookup import django_policy_limit_lookup
from infrastructure.persistence.models import User

class Command(BaseCommand):
    help = "Run the full pipeline, approve it, and print the trace - Day 6 end-to-end."

    def add_arguments(self, parser):
        parser.add_argument("claim_id")
        parser.add_argument("--claimed-amount", type=float, default=5000)
        parser.add_argument("--decision", default="approve", choices=["approve", "reject", "edit"])
        parser.add_argument("--outcome", default=None, help="Required to demonstrate a real edit; differs from the AI recommendation")
        parser.add_argument("--rationale", default=None)

    def handle(self, *args, **options):
        if options["decision"] == "edit" and (not options["outcome"] or not options["rationale"]):
                    raise CommandError(
                        "--decision edit requires both --outcome and --rationale to be provided, "
                        "so the edit is actually distinguishable from a plain approve."
                    )
        llm = build_completion_provider()
        retrieve_use_case = RetrieveChunksUseCase(DenseRetriever(build_embedding_provider()), KeywordRetriever())
        get_policy_version = GetPolicyVersionTool()
        search_policy = SearchPolicyTool(retrieve_use_case)
        audit_logger = DjangoAuditLogger()
        orchestrator = AdjudicationPipelineOrchestrator(
            coverage_matcher=CoverageMatcherAgent(llm, get_policy_version, search_policy),
            exclusion_analyst=ExclusionAnalystAgent(llm, search_policy),
            adjudication_drafter=AdjudicationDrafterAgent(llm, CalculatePayoutTool(), DetectAnomalyTool()),
            run_recorder=DjangoAgentRunRecorder(),
            policy_limit_lookup=django_policy_limit_lookup,
            audit_logger=audit_logger,
            search_policy_tool=search_policy,
        )
        result = orchestrator.run(claim_id=options["claim_id"], claimed_amount=options["claimed_amount"])
        self.stdout.write(self.style.SUCCESS(f"Job {result.job_id} status: WAITING_APPROVAL"))
        self.stdout.write(f"AI recommendation: {result.final_recommendation}")
        approver = User.objects.filter(username="test_adjuster").first()
        if not approver:
            raise CommandError(
                "No user 'test_adjuster' found. Run: python manage.py create_test_claim first, "
                "or create a user with that username manually."
            )
        gate = ApprovalGateUseCase(DjangoApprovalRepository(), FinalizeAdjudicationTool(), audit_logger)
        decision_result = gate.decide(
            claim_id=options["claim_id"], job_id=result.job_id, approver_id=str(approver.id),
            decision=options["decision"],
            outcome=options["outcome"] or ("approved" if options["decision"] != "reject" else "rejected"),
            rationale=options["rationale"] or "Reviewed via run_approval_demo",
            original_recommendation=result.final_recommendation,
        )
        self.stdout.write(self.style.SUCCESS(f"Human decision: {decision_result.status}"))
        self.stdout.write(str(decision_result.finalize_result))
        self.stdout.write("\n--- FULL TRACE ---")
        trace = GetRunTraceUseCase(DjangoTraceRepository()).execute(result.job_id)
        for entry in trace:
            self.stdout.write(f"[{entry.timestamp}] {entry.kind}: {entry.detail}")