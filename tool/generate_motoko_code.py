from typing import Any
import mcp.types as types
from ...rag import inference_base as base
from ...rag import inference_gemini as gemini
from . import tool_factory

class GenerateMotokoCode(tool_factory.ToolFactory):
    def action(self, arguments: dict[str, Any]) -> list[types.ContentBlock]:
        query = arguments.get("query")
        gemini_strategy = gemini.GeminiStrategy()
        context = base.InferenceContext(gemini_strategy)
        retrieved_data = context.generate_response(1,query)
        return [
            types.TextContent(
                type="text",
                text=f"{retrieved_data['response']}",
            )
        ]
