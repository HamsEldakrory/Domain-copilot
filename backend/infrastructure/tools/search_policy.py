from application.use_cases.format_citation import format_citation
from application.use_cases.retrieve_chunks import RetrieveChunksUseCase
from domain.ports.tool import Tool, ToolResult


class SearchPolicyTool(Tool):
    name = "search_policy"
    description = "Search policy documents for text relevant to a query, filtered to a policy version."

    def __init__(self, retrieve_use_case: RetrieveChunksUseCase):
        self._retrieve = retrieve_use_case

    def run(self, query: str, policy_version_id: str | None = None) -> ToolResult:
        result = self._retrieve.execute(query, policy_version_id=policy_version_id, top_k=5)
        if result.refused:
            return ToolResult(tool_name=self.name, output={"refused": True, "reason": result.refusal_reason})
        return ToolResult(
            tool_name=self.name,
            output={"refused": False, "citations": [format_citation(c) for c in result.chunks]},
        )