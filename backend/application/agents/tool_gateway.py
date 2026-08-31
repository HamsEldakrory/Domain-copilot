from domain.errors import ToolNotAllowedError
from domain.ports.tool import Tool, ToolResult


class ToolGateway:
    def __init__(self, agent_name: str, allowed_tools: dict[str, Tool]):
        self._agent_name = agent_name
        self._tools = allowed_tools

    def call(self, tool_name: str, **kwargs) -> ToolResult:
        if tool_name not in self._tools:
            raise ToolNotAllowedError(self._agent_name, tool_name)
        return self._tools[tool_name].run(**kwargs)