from typing import Any
import mcp.types as types
from rag import inference_base as base
from rag import inference_gemini as gemini
from tool import tool_factory

class GetMotokoContext(tool_factory.ToolFactory):
    def action(self, arguments: dict[str, Any]) -> list[types.ContentBlock]:
        query = arguments.get("query")
        gemini_strategy = gemini.GeminiStrategy()
        context = base.InferenceContext(gemini_strategy)
        retrieved_data = context.retrieve_context(query)

        if retrieved_data["doc_docs"]:
            doc_results = list(
                zip(
                    retrieved_data["doc_docs"],
                    retrieved_data["doc_metas"],
                    retrieved_data["doc_distances"],
                )
            )
            doc_results.sort(key=lambda x: x[2])  # Sort by distance
            
        return [
            types.TextContent(
                type="text",
                text=(f"{doc_results[:5]}"),
            )
        ]
