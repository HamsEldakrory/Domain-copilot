from dataclasses import dataclass
from domain.errors.domain_errors import InvalidJobStateTransitionError, MissingEditValuesError
from domain.ports.audit_logger import AuditLogger
from domain.ports.tool import Tool
@dataclass
class ApprovalDecisionResult:
    status: str  # "approved" | "rejected" | "edited_and_approved"
    finalize_result: dict | None = None

class ApprovalGateUseCase:
    def __init__(self, approval_repository, finalize_tool: Tool, audit_logger: AuditLogger):
        self._approval_repo = approval_repository
        self._finalize_tool = finalize_tool
        self._audit_logger = audit_logger
    def decide(
    self, claim_id, job_id, approver_id, decision,
    outcome=None, rationale=None, comment="",
    original_recommendation: dict | None = None,
    ):
        current_status = self._approval_repo.get_job_status(job_id)
        if current_status != "WAITING_APPROVAL":
            raise InvalidJobStateTransitionError(current_status, "approval_decision")
        if decision == "edit" and (not original_recommendation or not outcome or not rationale):
            raise MissingEditValuesError()
        self._approval_repo.record_approval(claim_id, job_id, approver_id, decision, comment)
        self._audit_logger.log(job_id, approver_id, f"approval_decision:{decision}", {"comment": comment})
        if decision == "reject":
            self._approval_repo.update_job_status(job_id, "FAILED")

            return ApprovalDecisionResult(status="rejected")
        if decision == "edit":
            self._audit_logger.log(job_id, approver_id, "recommendation_edited", {
                "original": original_recommendation, "edited_outcome": outcome, "edited_rationale": rationale,
            })
        finalize_result = self._finalize_tool.run(
            claim_id=claim_id, job_id=job_id, approved_by=approver_id,
            outcome=outcome or "approved", rationale=rationale or comment,
            )
        if finalize_result.error:
            self._audit_logger.log(job_id, approver_id, "finalize_failed", {"error": finalize_result.error})
            return ApprovalDecisionResult(status="rejected", finalize_result=finalize_result.output)
        self._approval_repo.update_job_status(job_id, "COMPLETED")
        self._audit_logger.log(job_id, approver_id, "finalized", finalize_result.output)
        return ApprovalDecisionResult(
            status="edited_and_approved" if decision == "edit" else "approved",
            finalize_result=finalize_result.output,
            )