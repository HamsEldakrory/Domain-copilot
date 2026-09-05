from domain.ports.tool import Tool, ToolResult


class CalculatePayoutTool(Tool):
    name = "calculate_payout"
    description = "Calculate payout given claimed amount, policy limit, and deductible."
    def run(self, claimed_amount: float, policy_limit: float, deductible: float) -> ToolResult:
        # Coerce to float: claimed_amount may arrive as decimal.Decimal from
        # Django's DecimalField and Python refuses to mix Decimal with float.
        claimed_amount = float(claimed_amount)
        policy_limit = float(policy_limit)
        deductible = float(deductible)
        if claimed_amount < 0 or policy_limit < 0 or deductible < 0:
            return ToolResult(tool_name=self.name, error="Amounts must be non-negative")

        after_deductible = max(claimed_amount - deductible, 0)
        payout = min(after_deductible, policy_limit)

        return ToolResult(
            tool_name=self.name,
            output={
                "claimed_amount": claimed_amount,
                "deductible_applied": deductible,
                "policy_limit": policy_limit,
                "payout": round(payout, 2),
                "capped_by_limit": after_deductible > policy_limit,
            },
        )