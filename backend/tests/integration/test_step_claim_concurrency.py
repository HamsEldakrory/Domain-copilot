import threading
import time
from unittest.mock import MagicMock

from django.db import connection
from django.test import TransactionTestCase

from application.use_cases.adjudication_pipeline import AdjudicationPipelineOrchestrator
from domain.ports.agent import AgentOutput
from infrastructure.persistence.django_agent_run_recorder import DjangoAgentRunRecorder
from infrastructure.persistence.models import (
    AgentRun,
    Claim,
    Client,
    Job,
    Policy,
    PolicyVersion,
    User,
)


class ConcurrentStepClaimTests(TransactionTestCase):
    def test_duplicate_task_dispatches_each_agent_executes_exactly_once(self):
        client = Client.objects.create(name="Concurrency Test")
        user = User.objects.create(username="conc_user")
        policy = Policy.objects.create(client=client, policy_number="conc")
        pv = PolicyVersion.objects.create(
            policy=policy, version="v1", effective_from="2024-01-01",
            policy_limit=10000, deductible=500,
        )
        claim = Claim.objects.create(client=client, policy_version=pv, adjuster=user, claim_date="2024-06-01")
        job = Job.objects.create(claim=claim, status="RUNNING")

        call_counts = {"coverage_matcher": 0, "exclusion_analyst": 0, "adjudication_drafter": 0}
        lock = threading.Lock()

        def make_agent(name):
            agent = MagicMock()

            def _run(agent_input):
                with lock:
                    call_counts[name] += 1
                time.sleep(0.3)  # deliberately widen the race window
                return AgentOutput(agent_name=name, result={"ok": True}, tool_calls=[], citations=[])

            agent.run.side_effect = _run
            return agent

        def worker():
            try:
                orch = AdjudicationPipelineOrchestrator(
                    coverage_matcher=make_agent("coverage_matcher"),
                    exclusion_analyst=make_agent("exclusion_analyst"),
                    adjudication_drafter=make_agent("adjudication_drafter"),
                    run_recorder=DjangoAgentRunRecorder(existing_job_id=str(job.id)),
                    policy_limit_lookup=lambda pv_id: (10000, 500),
                )
                orch.run(claim_id=str(claim.id), claimed_amount=1000)
            finally:
                connection.close()  # required: each thread gets its own DB connection

        # Simulate 3 duplicate deliveries of the "same" Celery task
        threads = [threading.Thread(target=worker) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(call_counts["coverage_matcher"], 1)
        self.assertEqual(call_counts["exclusion_analyst"], 1)
        self.assertEqual(call_counts["adjudication_drafter"], 1)

        for name in call_counts:
            self.assertEqual(
                AgentRun.objects.filter(job_id=job.id, agent_name=name).count(), 1,
                f"{name} should have exactly 1 AgentRun row, not duplicated by concurrent claims",
            )