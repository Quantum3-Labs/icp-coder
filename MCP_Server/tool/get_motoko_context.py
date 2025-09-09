from abc import abstractmethod
from typing import Any
import mcp.types as types
import rag.inference_base as base
import rag.inference_gemini as gemini
from . import tool_factory
class GetMotokoContext(tool_factory.ToolFactory):
    def action(self, arguments: dict[str, Any]) -> list[types.ContentBlock]:
        query = arguments.get("query")
        gemini_strategy = gemini.GeminiStrategy()
        context = base.InferenceContext(gemini_strategy)
        retrieved_data = context.retrieve_context(query)

        print("\nRetrieved context:")
        print(f"Documentation chunks: {len(retrieved_data['doc_docs'])}")
        print(f"Code examples: {len(retrieved_data['code_docs'])}")

        # Show documentation context
        if retrieved_data["doc_docs"]:
            print("\n=== DOCUMENTATION RESULTS ===")
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
