from unittest.mock import MagicMock

from django.test import TestCase

from application.use_cases.adjudication_pipeline import AdjudicationPipelineOrchestrator
from domain.ports.agent import AgentOutput


class CorrelationIdPropagationTests(TestCase):
    def test_correlation_id_recorded_on_every_agent_run(self):
        recorder = MagicMock()
        recorder.start_job.return_value = "job-1"
        recorder.is_cancelled.return_value = False
        recorder.start_or_resume_step.return_value = ("CLAIMED", None)

        agent = MagicMock()
        agent.run.return_value = AgentOutput(agent_name="a", result={}, tool_calls=[], citations=[], input_tokens=10, output_tokens=5)

        orch = AdjudicationPipelineOrchestrator(
            coverage_matcher=agent, exclusion_analyst=agent, adjudication_drafter=agent,
            run_recorder=recorder, policy_limit_lookup=lambda pv: (0, 0),
            correlation_id="corr-abc-123",
        )
        orch.run(claim_id="c1", claimed_amount=1000)

        for call in recorder.record_agent_run.call_args_list:
            self.assertEqual(call.kwargs.get("correlation_id"), "corr-abc-123")
            self.assertEqual(call.kwargs.get("input_tokens"), 10)
            self.assertEqual(call.kwargs.get("output_tokens"), 5)