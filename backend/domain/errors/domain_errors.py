class DomainError(Exception):
    # Base class for all domain-level errors.
    pass

class NotFoundError(DomainError):
    # Raised when a requested domain entity does not exist.
    pass

class ClaimNotFoundError(NotFoundError):
    def __init__(self, claim_id):
        self.claim_id = claim_id
        super().__init__(f"Claim not found: {claim_id}")

class PolicyVersionNotFoundError(NotFoundError):
    def __init__(self, policy_id, as_of_date):
        self.policy_id = policy_id
        self.as_of_date = as_of_date
        super().__init__(
            f"No policy version found for policy {policy_id} as of {as_of_date}"
        )
class InvalidJobStateTransitionError(DomainError):
    def __init__(self, current_state, attempted_state):
        self.current_state = current_state
        self.attempted_state = attempted_state
        super().__init__(
            f"Cannot transition job from '{current_state}' to '{attempted_state}'"
        )
class UnauthorizedActionError(DomainError):
    def __init__(self, message="You are not authorized to perform this action"):
        super().__init__(message)
class ToolNotAllowedError(DomainError):
    def __init__(self, agent_name, tool_name):
        self.agent_name = agent_name
        self.tool_name = tool_name
        super().__init__(f"Agent '{agent_name}' is not permitted to call tool '{tool_name}'")
class MaxIterationsExceededError(DomainError):
    def __init__(self, max_iterations):
        self.max_iterations = max_iterations
        super().__init__(f"Pipeline exceeded max iterations ({max_iterations})")
class StepTimeoutError(DomainError):
    def __init__(self, step_name, timeout_seconds):
        self.step_name = step_name
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Step '{step_name}' exceeded timeout of {timeout_seconds}s")
class MissingEditValuesError(DomainError):
    def __init__(self):
        super().__init__(
            "decision='edit' requires original_recommendation, outcome, and rationale "
            "to all be provided - otherwise there is nothing to distinguish it from approve"
        )