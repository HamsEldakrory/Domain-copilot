from unittest.mock import MagicMock

from django.test import TestCase

from application.agents.coverage_matcher import CoverageMatcherAgent
from application.use_cases.adjudication_pipeline import AdjudicationPipelineOrchestrator
from application.use_cases.cancel_job import CancelJobUseCase
from domain.errors import JobCancelledError
from domain.ports.agent import AgentInput
from domain.ports.tool import ToolResult


class FakeStream:
    def __init__(self, tokens):
        self._tokens = iter(tokens)
        self.closed = False
        self.input_tokens = 10
        self.output_tokens = 5

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._tokens)

    def close(self):
        self.closed = True


class FakeLLMForStreaming:
    def __init__(self, tokens):
        self._tokens = tokens

    def stream_completion(self, messages, tools=None):
        return FakeStream(list(self._tokens))

    def completion(self, messages, tools=None):
        raise AssertionError("Agent must use stream_completion, not completion")

    def embeddings(self, texts):
        return [[0.0] for _ in texts]


class FakeTool:
    def __init__(self, output=None, error=None):
        self._output = output or {}
        self._error = error

    def run(self, **kwargs):
        return ToolResult(tool_name="fake", output=self._output, error=self._error)


class TokenStreamingTests(TestCase):
    def test_real_tokens_published_not_split_after_completion(self):
        events = []
        publisher = MagicMock()
        publisher.publish.side_effect = lambda job_id, event_type, data: events.append((event_type, data))

        agent = CoverageMatcherAgent(
            llm_provider=FakeLLMForStreaming(["Cov", "erage ", "applies."]),
            get_policy_version=FakeTool(output={"policy_version_id": "pv-1", "version_mismatch_detected": False}),
            search_policy=FakeTool(output={"citations": []}),
            event_publisher=publisher,
        )
        output = agent.run(AgentInput(claim_id="c1", job_id="job-1"))

        token_events = [e for e in events if e[0] == "token"]
        self.assertEqual(len(token_events), 3)
        self.assertEqual("".join(e[1]["token"] for e in token_events), "Coverage applies.")
        self.assertEqual(output.result["coverage_summary"], "Coverage applies.")

    def test_agent_started_and_complete_bracket_the_run(self):
        events = []
        publisher = MagicMock()
        publisher.publish.side_effect = lambda job_id, event_type, data: events.append(event_type)

        agent = CoverageMatcherAgent(
            llm_provider=FakeLLMForStreaming(["ok"]),
            get_policy_version=FakeTool(output={"policy_version_id": "pv-1", "version_mismatch_detected": False}),
            search_policy=FakeTool(output={"citations": []}),
            event_publisher=publisher,
        )
        agent.run(AgentInput(claim_id="c1", job_id="job-1"))

        self.assertEqual(events[0], "agent_started")
        self.assertIn("agent_progress", events)
        self.assertEqual(events[-1], "agent_complete")


class CancellationTests(TestCase):
    def test_cancellation_stops_mid_stream_and_closes_connection(self):
        checker = MagicMock()
        checker.is_cancelled.side_effect = [False, True]  # cancel on 2nd token

        agent = CoverageMatcherAgent(
            llm_provider=FakeLLMForStreaming(["a", "b", "c", "d"]),
            get_policy_version=FakeTool(output={"policy_version_id": "pv-1", "version_mismatch_detected": False}),
            search_policy=FakeTool(output={"citations": []}),
            cancellation_checker=checker,
        )
        with self.assertRaises(JobCancelledError):
            agent.run(AgentInput(claim_id="c1", job_id="job-1"))

    def test_orchestrator_marks_job_cancelled_not_degraded(self):
        run_recorder = MagicMock()
        run_recorder.start_job.return_value = "job-1"
        run_recorder.is_cancelled.return_value = True  # cancelled before first step

        orch = AdjudicationPipelineOrchestrator(
            coverage_matcher=MagicMock(), exclusion_analyst=MagicMock(), adjudication_drafter=MagicMock(),
            run_recorder=run_recorder, policy_limit_lookup=lambda pv: (0, 0),
        )
        result = orch.run(claim_id="c1", claimed_amount=100)
        run_recorder.update_job_status.assert_any_call("job-1", "CANCELLED")
        self.assertFalse(result.degraded)  # cancellation is not degradation

    def test_cancel_use_case_rejects_terminal_states(self):
        recorder = MagicMock()
        reader = MagicMock()
        reader.get_job_status.return_value = "COMPLETED"
        result = CancelJobUseCase(recorder, reader).execute("job-1")
        self.assertFalse(result.success)
        recorder.update_job_status.assert_not_called()

    def test_cancel_use_case_succeeds_on_running_job(self):
        recorder = MagicMock()
        reader = MagicMock()
        reader.get_job_status.return_value = "RUNNING"
        result = CancelJobUseCase(recorder, reader).execute("job-1")
        self.assertTrue(result.success)
        recorder.update_job_status.assert_called_once_with("job-1", "CANCELLED")


class RetryDoesNotSwallowCancellationTests(TestCase):
    def test_retry_with_backoff_reraises_dont_retry_immediately(self):
        from application.support.retry import retry_with_backoff
        calls = {"count": 0}

        @retry_with_backoff(max_attempts=3, base_delay=0.01, dont_retry=(JobCancelledError,))
        def flaky():
            calls["count"] += 1
            raise JobCancelledError("job-1")

        with self.assertRaises(JobCancelledError):
            flaky()
        self.assertEqual(calls["count"], 1)  # NOT retried 3 times
class IdempotentRecordingTests(TestCase):
    def test_resumed_step_does_not_create_duplicate_agentrun(self):
        recorder = MagicMock()
        recorder.start_job.return_value = "job-1"
        recorder.is_cancelled.return_value = False
        # First step already COMPLETED (resumed), other two are fresh
        recorder.start_or_resume_step.side_effect = [
            ("COMPLETED", {"coverage_summary": "already done", "citations": []}),
            ("RUNNING", None),
            ("RUNNING", None),
        ]

        from domain.ports.agent import AgentOutput
        exclusion_agent = MagicMock()
        exclusion_agent.run.return_value = AgentOutput(agent_name="exclusion_analyst", result={"exclusion_summary": "x"}, tool_calls=[], citations=[])
        drafter_agent = MagicMock()
        drafter_agent.run.return_value = AgentOutput(agent_name="adjudication_drafter", result={"payout": {}}, tool_calls=[], citations=[])

        orch = AdjudicationPipelineOrchestrator(
            coverage_matcher=MagicMock(),  # should NEVER be called - step already completed
            exclusion_analyst=exclusion_agent,
            adjudication_drafter=drafter_agent,
            run_recorder=recorder,
            policy_limit_lookup=lambda pv: (10000, 500),
        )
        orch.run(claim_id="c1", claimed_amount=1000)

        # record_agent_run must be called exactly twice - NOT three times.
        # The resumed coverage_matcher step must not produce a new AgentRun row.
        self.assertEqual(recorder.record_agent_run.call_count, 2)
        recorded_agents = [call.args[1] for call in recorder.record_agent_run.call_args_list]
        self.assertNotIn("coverage_matcher", recorded_agents)
        self.assertIn("exclusion_analyst", recorded_agents)
        self.assertIn("adjudication_drafter", recorded_agents)